from pydantic import BaseModel, Field
from typing import List, Optional, Union

class CrimePredictionRequest(BaseModel):
    locationDescription: str = "STREET"
    communityArea: Union[str, int] = "Loop (Downtown)"
    district: Optional[int] = 1
    ward: Optional[int] = 42
    beat: Optional[int] = 111
    hourOfDay: int = Field(default=18, ge=0, le=23)
    dayOfWeek: str = "Friday"
    month: Optional[int] = Field(default=6, ge=1, le=12)
    domestic: bool = False
    latitude: Optional[float] = 41.8819
    longitude: Optional[float] = -87.6278

class PredictionProbability(BaseModel):
    category: str
    probability: float

class CrimePredictionResponse(BaseModel):
    success: bool
    predictedCategory: str
    riskScore: int
    riskLevel: str
    arrestProbability: float
    confidence: float
    primaryHotspot: str
    estimatedResponseTime: str
    topProbabilities: List[PredictionProbability]
    recommendations: List[str]

class OverviewStatsResponse(BaseModel):
    totalIncidentsYear: str
    predictedChange: str
    arrestRate: str
    highRiskZones: int
    modelsActive: str

class HotspotArea(BaseModel):
    id: int
    name: str
    riskLevel: str
    incidentCount: int
    latitude: float
    longitude: float

class TrendMonth(BaseModel):
    month: str
    theft: int
    battery: int
    robbery: int
    other: int

class RecentIncident(BaseModel):
    id: str
    type: str
    area: str
    location: str
    time: str
    severity: str
    arrest: bool
