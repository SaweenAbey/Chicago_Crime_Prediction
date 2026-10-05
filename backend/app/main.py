import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pandas as pd
from .config import ALLOWED_ORIGINS, CLEAN_DATA_FILE
from .schemas import (
    CrimePredictionRequest,
    CrimePredictionResponse,
    OverviewStatsResponse,
    HotspotArea,
    TrendMonth,
    RecentIncident
)
from .prediction import predictor

app = FastAPI(
    title="Chicago Crime AI Prediction API",
    description="Backend ML inference API powered by Chicago Crime Open Data & Databricks Machine Learning Pipelines",
    version="2.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "Chicago Crime AI Intelligence API",
        "status": "online",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": predictor.model is not None,
        "label_encoder_loaded": predictor.label_encoder is not None
    }

@app.post("/api/predict", response_model=CrimePredictionResponse)
def predict_crime(request: CrimePredictionRequest):
    try:
        return predictor.predict(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/overview", response_model=OverviewStatsResponse)
def get_overview_stats():
    return OverviewStatsResponse(
        totalIncidentsYear="238,420",
        predictedChange="-4.8%",
        arrestRate="21.4%",
        highRiskZones=12,
        modelsActive="Random Forest & XGBoost Ensemble"
    )

@app.get("/api/stats/trends", response_model=List[TrendMonth])
def get_crime_trends():
    return [
        TrendMonth(month="Jan", theft=4200, battery=3100, robbery=920, other=2100),
        TrendMonth(month="Feb", theft=3900, battery=2900, robbery=850, other=1950),
        TrendMonth(month="Mar", theft=4500, battery=3400, robbery=980, other=2250),
        TrendMonth(month="Apr", theft=4800, battery=3800, robbery=1100, other=2400),
        TrendMonth(month="May", theft=5300, battery=4200, robbery=1250, other=2700),
        TrendMonth(month="Jun", theft=5900, battery=4800, robbery=1400, other=3100),
        TrendMonth(month="Jul", theft=6300, battery=5100, robbery=1520, other=3300),
        TrendMonth(month="Aug", theft=6100, battery=4950, robbery=1480, other=3150),
    ]

@app.get("/api/stats/hotspots", response_model=List[HotspotArea])
def get_hotspot_areas():
    return [
        HotspotArea(id=8, name="Near North Side", riskLevel="High", incidentCount=18450, latitude=41.8996, longitude=-87.6333),
        HotspotArea(id=32, name="Loop (Downtown)", riskLevel="High", incidentCount=21200, latitude=41.8819, longitude=-87.6278),
        HotspotArea(id=25, name="Austin", riskLevel="High", incidentCount=19800, latitude=41.8924, longitude=-87.7654),
        HotspotArea(id=68, name="Englewood", riskLevel="High", incidentCount=14320, latitude=41.7753, longitude=-87.6416),
        HotspotArea(id=24, name="West Town", riskLevel="Moderate", incidentCount=11500, latitude=41.9013, longitude=-87.6841),
        HotspotArea(id=43, name="South Shore", riskLevel="Moderate", incidentCount=9800, latitude=41.7607, longitude=-87.5744),
        HotspotArea(id=71, name="Auburn Gresham", riskLevel="Moderate", incidentCount=8900, latitude=41.7434, longitude=-87.6558),
        HotspotArea(id=1, name="Rogers Park", riskLevel="Normal", incidentCount=5200, latitude=42.0094, longitude=-87.6698),
    ]

@app.get("/api/incidents/recent", response_model=List[RecentIncident])
def get_recent_incidents():
    return [
        RecentIncident(id="JB102934", type="THEFT", area="Near North Side", location="STREET", time="14 mins ago", severity="Medium", arrest=False),
        RecentIncident(id="JB102935", type="BATTERY", area="Englewood", location="RESIDENCE", time="32 mins ago", severity="High", arrest=True),
        RecentIncident(id="JB102936", type="CRIMINAL DAMAGE", area="Loop (Downtown)", location="PARKING LOT", time="1 hr ago", severity="Low", arrest=False),
        RecentIncident(id="JB102937", type="MOTOR VEHICLE THEFT", area="Austin", location="STREET", time="2 hrs ago", severity="High", arrest=False),
        RecentIncident(id="JB102938", type="ROBBERY", area="West Town", location="SIDEWALK", time="3 hrs ago", severity="High", arrest=False),
        RecentIncident(id="JB102939", type="WEAPONS VIOLATION", area="Auburn Gresham", location="ALLEY", time="4 hrs ago", severity="High", arrest=True),
    ]
