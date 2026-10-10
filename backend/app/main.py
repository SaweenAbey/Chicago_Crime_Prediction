import calendar
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
from .prediction import predictor, CHICAGO_AREAS_DATA, InvalidInputError, severity_for

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
    """Descriptive statistics computed once from the full cleaned dataset (data/clean)."""
    if _STATS_CACHE:
        return _STATS_CACHE
    if not os.path.exists(CLEAN_DATA_FILE):
        print(f"[WARN] {CLEAN_DATA_FILE} not found - dashboard statistics unavailable.")
        return _STATS_CACHE
    try:
        df = pd.read_csv(CLEAN_DATA_FILE, usecols=['case_number', 'date', 'primary_type', 'location_description',
                                                   'arrest', 'community_area'])
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df['arrest'] = df['arrest'].astype(str).str.lower().eq('true')

        # Hotspots: the 10 community areas with the most incidents. "High" = at least three times the
        # median community area's count; descriptive only, not a model prediction.
        area_counts = df['community_area'].dropna().astype(int).value_counts()
        high_threshold = 3 * area_counts.median()
        hotspots = []
        for area_id, cnt in area_counts.head(10).items():
            info = CHICAGO_AREAS_DATA.get(int(area_id), {"name": f"Area {area_id}", "lat": 41.85, "lon": -87.65})
            hotspots.append(HotspotArea(
                id=int(area_id), name=info["name"], riskLevel="High" if cnt >= high_threshold else "Moderate",
                incidentCount=int(cnt), latitude=float(info["lat"]), longitude=float(info["lon"])))

        # Monthly counts for the last complete calendar year in the data
        full_year = int(df['date'].dt.year.max()) - 1
        year_df = df[df['date'].dt.year == full_year]
        trends = []
        for month in range(1, 13):
            m = year_df[year_df['date'].dt.month == month]['primary_type']
            theft, battery, robbery = (int((m == t).sum()) for t in ('THEFT', 'BATTERY', 'ROBBERY'))
            trends.append(TrendMonth(month=f"{calendar.month_abbr[month]} {full_year}", theft=theft,
                                     battery=battery, robbery=robbery, other=int(len(m)) - theft - battery - robbery))

        recent_list = []
        for _, row in df.sort_values('date', ascending=False).head(8).iterrows():
            area_id = int(row['community_area']) if pd.notnull(row['community_area']) else None
            recent_list.append(RecentIncident(
                id=str(row['case_number']), type=str(row['primary_type']),
                area=CHICAGO_AREAS_DATA.get(area_id, {}).get('name', 'Unknown area'),
                location=str(row['location_description']), time=row['date'].strftime('%Y-%m-%d %H:%M'),
                severity=severity_for(str(row['primary_type'])), arrest=bool(row['arrest'])))

        _STATS_CACHE['overview'] = OverviewStatsResponse(
            totalIncidentsYear=f"{len(df):,}",
            arrestRate=f"{df['arrest'].mean() * 100:.1f}%",
            highRiskZones=sum(1 for h in hotspots if h.riskLevel == "High"),
            modelsActive=predictor.model_name
        )
        _STATS_CACHE['hotspots'] = hotspots
        _STATS_CACHE['trends'] = trends
        _STATS_CACHE['recent'] = recent_list
    except Exception as e:
        print(f"[WARN] Error loading dataset stats: {e}")

    return _STATS_CACHE


def cached_or_unavailable(key):
    cache = get_or_load_data_stats()
    if not cache.get(key):
        raise HTTPException(status_code=503, detail="Dataset not loaded: add data/clean/chicago_crime_clean.csv.")
    return cache[key]

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
        totalIncidentsYear="n/a (dataset not loaded)",
        arrestRate="n/a (dataset not loaded)",
        highRiskZones=0,
        modelsActive=predictor.model_name
    )

@app.get("/api/stats/trends", response_model=List[TrendMonth])
def get_crime_trends():
    return cached_or_unavailable('trends')

@app.get("/api/stats/hotspots", response_model=List[HotspotArea])
def get_hotspot_areas():
    return cached_or_unavailable('hotspots')

@app.get("/api/incidents/recent", response_model=List[RecentIncident])
def get_recent_incidents():
    return cached_or_unavailable('recent')
