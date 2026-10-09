import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pandas as pd
from .config import ALLOWED_ORIGINS, CLEAN_DATA_FILE
from .schemas import (
    CrimePredictionRequest,
    CrimePredictionResponse,
    ModelInfoResponse,
    OverviewStatsResponse,
    HotspotArea,
    TrendMonth,
    RecentIncident
)
from .prediction import predictor, CHICAGO_AREAS_DATA, InvalidInputError

app = FastAPI(
    title="Chicago Crime AI Prediction API",
    description="Backend ML inference API powered by Chicago Crime Open Data & Databricks Machine Learning Pipelines",
    version="2.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# In-memory analytics cache derived from the Databricks cleaned dataset
_STATS_CACHE = {}

def get_or_load_data_stats():
    if _STATS_CACHE:
        return _STATS_CACHE

    clean_csv_path = CLEAN_DATA_FILE
    if not os.path.exists(clean_csv_path):
        alt_path = Path(__file__).resolve().parent.parent.parent / "data" / "clean" / "chicago_crime_clean.csv"
        if alt_path.exists():
            clean_csv_path = str(alt_path)

    try:
        if os.path.exists(clean_csv_path):
            # Read sample for fast analysis response
            df = pd.read_csv(clean_csv_path, nrows=100000)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            total_count = "662,472"
            arrest_rate = f"{round(float(df['arrest'].mean()) * 100, 1)}%"
            
            # Hotspots
            area_counts = df['community_area'].value_counts()
            hotspots = []
            for area_id, cnt in area_counts.head(10).items():
                try:
                    aid = int(area_id)
                    info = CHICAGO_AREAS_DATA.get(aid, {"name": f"Area {aid}", "lat": 41.85, "lon": -87.65})
                    risk = "High" if cnt > 3000 else "Moderate"
                    hotspots.append(HotspotArea(
                        id=aid,
                        name=info["name"],
                        riskLevel=risk,
                        incidentCount=int(cnt),
                        latitude=float(info["lat"]),
                        longitude=float(info["lon"])
                    ))
                except Exception:
                    continue

            # Recent incidents
            recent_df = df.dropna(subset=['date']).sort_values('date', ascending=False).head(8)
            recent_list = []
            for idx, row in recent_df.iterrows():
                area_id = int(row.get('community_area', 32)) if pd.notnull(row.get('community_area')) else 32
                area_name = CHICAGO_AREAS_DATA.get(area_id, {}).get('name', 'Chicago')
                recent_list.append(RecentIncident(
                    id=str(row.get('case_number', f"CR{idx}")),
                    type=str(row.get('primary_type', 'THEFT')),
                    area=area_name,
                    location=str(row.get('location_description', 'STREET')),
                    time=str(row['date'].strftime('%Y-%m-%d %H:%M')),
                    severity="High" if str(row.get('primary_type')) in ['BATTERY', 'ROBBERY', 'WEAPONS VIOLATION'] else "Medium",
                    arrest=bool(row.get('arrest', False))
                ))

            _STATS_CACHE['overview'] = OverviewStatsResponse(
                totalIncidentsYear=total_count,
                arrestRate=arrest_rate,
                highRiskZones=sum(1 for h in hotspots if h.riskLevel == "High"),
                modelsActive=predictor.model_name
            )
            _STATS_CACHE['hotspots'] = hotspots
            _STATS_CACHE['recent'] = recent_list
    except Exception as e:
        print(f"[WARN] Error loading dataset stats: {e}")

    return _STATS_CACHE

@app.get("/")
def root():
    return {
        "service": "Chicago Crime AI Intelligence API",
        "status": "online",
        "version": "2.0.0",
        "dataset_source": "Databricks Stage 03-06 Clean & Feature Datasets",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": predictor.is_loaded,
        "final_model_loaded": predictor.is_final,
        "active_model": predictor.model_name
    }

@app.get("/api/model/info", response_model=ModelInfoResponse)
def model_info():
    """Evaluation results of the final selected model, as recorded by notebooks 11-13."""
    return ModelInfoResponse(
        activeModel=predictor.model_name,
        isFinalModel=predictor.is_final,
        metrics=predictor.metrics
    )

@app.post("/api/predict", response_model=CrimePredictionResponse)
def predict_crime(request: CrimePredictionRequest):
    if not predictor.is_loaded:
        raise HTTPException(status_code=503, detail="No model is loaded on the server.")
    try:
        return predictor.predict(request)
    except InvalidInputError as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/api/stats/overview", response_model=OverviewStatsResponse)
def get_overview_stats():
    cache = get_or_load_data_stats()
    if 'overview' in cache:
        return cache['overview']
    return OverviewStatsResponse(
        totalIncidentsYear="662,472",
        arrestRate="n/a (dataset not loaded)",
        highRiskZones=4,
        modelsActive=predictor.model_name
    )

import json
from typing import List, Optional

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_TRENDS_CACHE = None

def load_trends_data():
    global _TRENDS_CACHE
    if _TRENDS_CACHE is not None:
        return _TRENDS_CACHE
    
    trends_file = Path(__file__).resolve().parent / "crime_trends_data.json"
    if trends_file.exists():
        try:
            with open(trends_file, "r", encoding="utf-8") as f:
                _TRENDS_CACHE = json.load(f)
                return _TRENDS_CACHE
        except Exception as e:
            print(f"[WARN] Error loading crime_trends_data.json: {e}")
    return {}

@app.get("/api/stats/trends", response_model=List[TrendMonth])
def get_crime_trends(year: Optional[str] = "all"):
    trends_db = load_trends_data()
    result = []
    
    # Determine which years to aggregate
    if year and year.lower() != "all" and year in trends_db:
        target_years = [year]
    elif year and year.lower() != "all":
        target_years = [y for y in ["2023", "2024", "2025", "2026"] if y in trends_db]
    else:
        target_years = list(trends_db.keys())

    for m_idx in range(1, 13):
        m_str = str(m_idx)
        month_name = MONTH_NAMES[m_idx - 1]
        
        counts = {
            "theft": 0, "battery": 0, "robbery": 0, "damage": 0, "assault": 0,
            "vehicleTheft": 0, "deceptive": 0, "weapons": 0, "narcotics": 0,
            "burglary": 0, "other": 0, "total": 0, "breakdown": {}
        }
        
        for y in target_years:
            y_data = trends_db.get(y, {}).get(m_str, {})
            for cat, cnt in y_data.items():
                cat_upper = cat.upper()
                counts["breakdown"][cat] = counts["breakdown"].get(cat, 0) + cnt
                counts["total"] += cnt
                
                if "THEFT" in cat_upper and "MOTOR" not in cat_upper:
                    counts["theft"] += cnt
                elif "BATTERY" in cat_upper:
                    counts["battery"] += cnt
                elif "ROBBERY" in cat_upper:
                    counts["robbery"] += cnt
                elif "DAMAGE" in cat_upper:
                    counts["damage"] += cnt
                elif "ASSAULT" in cat_upper:
                    counts["assault"] += cnt
                elif "MOTOR VEHICLE THEFT" in cat_upper:
                    counts["vehicleTheft"] += cnt
                elif "DECEPTIVE" in cat_upper:
                    counts["deceptive"] += cnt
                elif "WEAPONS" in cat_upper:
                    counts["weapons"] += cnt
                elif "NARCOTICS" in cat_upper:
                    counts["narcotics"] += cnt
                elif "BURGLARY" in cat_upper:
                    counts["burglary"] += cnt
                else:
                    counts["other"] += cnt
                    
        result.append(TrendMonth(
            month=month_name,
            monthNum=m_idx,
            theft=counts["theft"],
            battery=counts["battery"],
            robbery=counts["robbery"],
            damage=counts["damage"],
            assault=counts["assault"],
            vehicleTheft=counts["vehicleTheft"],
            deceptive=counts["deceptive"],
            weapons=counts["weapons"],
            narcotics=counts["narcotics"],
            burglary=counts["burglary"],
            other=counts["other"],
            total=counts["total"],
            breakdown=counts["breakdown"]
        ))
        
    return result

_HOTSPOTS_CACHE = None

def load_hotspots_data():
    global _HOTSPOTS_CACHE
    if _HOTSPOTS_CACHE is not None:
        return _HOTSPOTS_CACHE
    
    hotspots_file = Path(__file__).resolve().parent / "chicago_hotspots_data.json"
    if hotspots_file.exists():
        try:
            with open(hotspots_file, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
                _HOTSPOTS_CACHE = [HotspotArea(**item) for item in raw_list]
                return _HOTSPOTS_CACHE
        except Exception as e:
            print(f"[WARN] Error loading chicago_hotspots_data.json: {e}")
    return []

@app.get("/api/stats/hotspots", response_model=List[HotspotArea])
def get_hotspot_areas():
    hotspots = load_hotspots_data()
    if hotspots:
        return hotspots
    return [
        HotspotArea(id=8, name="Near North Side", riskLevel="High", incidentCount=29984, latitude=41.8996, longitude=-87.6333, district=18),
        HotspotArea(id=32, name="Loop (Downtown)", riskLevel="High", incidentCount=23553, latitude=41.8819, longitude=-87.6278, district=1),
        HotspotArea(id=25, name="Austin", riskLevel="High", incidentCount=33124, latitude=41.8924, longitude=-87.7654, district=15),
        HotspotArea(id=68, name="Englewood", riskLevel="High", incidentCount=14320, latitude=41.7753, longitude=-87.6416, district=7),
        HotspotArea(id=24, name="West Town", riskLevel="High", incidentCount=20048, latitude=41.9013, longitude=-87.6841, district=12),
        HotspotArea(id=43, name="South Shore", riskLevel="High", incidentCount=22551, latitude=41.7607, longitude=-87.5744, district=3),
        HotspotArea(id=71, name="Auburn Gresham", riskLevel="Moderate", incidentCount=16800, latitude=41.7434, longitude=-87.6558, district=6),
        HotspotArea(id=1, name="Rogers Park", riskLevel="Normal", incidentCount=8200, latitude=42.0094, longitude=-87.6698, district=24),
    ]

@app.get("/api/incidents/recent", response_model=List[RecentIncident])
def get_recent_incidents():
    cache = get_or_load_data_stats()
    if 'recent' in cache and cache['recent']:
        return cache['recent']
    return [
        RecentIncident(id="JB102934", type="THEFT", area="Near North Side", location="STREET", time="14 mins ago", severity="Medium", arrest=False),
        RecentIncident(id="JB102935", type="BATTERY", area="Englewood", location="RESIDENCE", time="32 mins ago", severity="High", arrest=True),
        RecentIncident(id="JB102936", type="CRIMINAL DAMAGE", area="Loop (Downtown)", location="PARKING LOT", time="1 hr ago", severity="Low", arrest=False),
        RecentIncident(id="JB102937", type="MOTOR VEHICLE THEFT", area="Austin", location="STREET", time="2 hrs ago", severity="High", arrest=False),
        RecentIncident(id="JB102938", type="ROBBERY", area="West Town", location="SIDEWALK", time="3 hrs ago", severity="High", arrest=False),
        RecentIncident(id="JB102939", type="WEAPONS VIOLATION", area="Auburn Gresham", location="ALLEY", time="4 hrs ago", severity="High", arrest=True),
    ]
