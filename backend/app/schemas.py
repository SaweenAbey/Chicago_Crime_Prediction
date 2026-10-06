from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Literal, Optional

DayOfWeek = Literal['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


class CrimePredictionRequest(BaseModel):
    """Incident context supplied by the user. Unknown fields are rejected."""
    model_config = ConfigDict(extra="forbid")

    # Required inputs
    communityArea: int = Field(..., ge=1, le=77, description="Chicago community area number (1-77)")
    locationDescription: str = Field(..., min_length=1, max_length=80)
    dayOfWeek: DayOfWeek
    hourOfDay: int = Field(..., ge=0, le=23)
    month: int = Field(..., ge=1, le=12)

    # Optional inputs; missing values are derived from the community area or left as "Unknown"
    year: int = Field(default=2026, ge=2001, le=2030)
    domestic: bool = False
    district: Optional[int] = Field(default=None, ge=1, le=31)
    ward: Optional[int] = Field(default=None, ge=1, le=50)
    beat: Optional[int] = Field(default=None, ge=111, le=2535)
    latitude: Optional[float] = Field(default=None, ge=41.6, le=42.1, description="Must lie within Chicago")
    longitude: Optional[float] = Field(default=None, ge=-87.95, le=-87.5, description="Must lie within Chicago")

    @field_validator("locationDescription")
    @classmethod
    def normalise_location(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("locationDescription must not be blank")
        return value


class PredictionProbability(BaseModel):
    category: str
    probability: float


class CrimePredictionResponse(BaseModel):
    success: bool
    predictedCategory: str
    confidence: float
    topProbabilities: List[PredictionProbability]
    modelName: str
    isFinalModel: bool
    # Rule-based decision support derived from the predicted category (not model outputs)
    severityLevel: str
    recommendations: List[str]
    area: str
    resolvedInputs: dict


class ModelInfoResponse(BaseModel):
    activeModel: str
    isFinalModel: bool
    metrics: dict


class OverviewStatsResponse(BaseModel):
    totalIncidentsYear: str
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
