import calendar
import datetime as dt
import json
import os
import joblib
import numpy as np
import pandas as pd
from typing import List
from .config import FINAL_BUNDLE_FILE, FINAL_METRICS_FILE, MODEL_FILE, LABEL_ENCODER_FILE
from .schemas import CrimePredictionRequest, CrimePredictionResponse, PredictionProbability
from .final_pipeline import RAW_FEATURES, predict_proba_raw, known_locations

DAY_INDEX = {d: i for i, d in enumerate(calendar.day_name)}  # Monday=0 ... Sunday=6

# 77 Chicago Community Areas with coordinate centers
CHICAGO_AREAS_DATA = {
    1: {"name": "Rogers Park", "lat": 42.0098, "lon": -87.6698, "district": 24},
    2: {"name": "West Ridge", "lat": 42.0006, "lon": -87.6925, "district": 24},
    3: {"name": "Uptown", "lat": 41.9658, "lon": -87.6533, "district": 19},
    4: {"name": "Lincoln Square", "lat": 41.9699, "lon": -87.6887, "district": 19},
    5: {"name": "North Center", "lat": 41.9509, "lon": -87.6877, "district": 19},
    6: {"name": "Lake View", "lat": 41.9427, "lon": -87.6534, "district": 19},
    7: {"name": "Lincoln Park", "lat": 41.9214, "lon": -87.6513, "district": 18},
    8: {"name": "Near North Side", "lat": 41.8996, "lon": -87.6333, "district": 18},
    9: {"name": "Edison Park", "lat": 42.0054, "lon": -87.8134, "district": 16},
    10: {"name": "Norwood Park", "lat": 41.9856, "lon": -87.8067, "district": 16},
    11: {"name": "Jefferson Park", "lat": 41.9702, "lon": -87.7633, "district": 16},
    12: {"name": "Forest Glen", "lat": 41.9788, "lon": -87.7554, "district": 16},
    13: {"name": "North Park", "lat": 41.9847, "lon": -87.7189, "district": 17},
    14: {"name": "Albany Park", "lat": 41.9683, "lon": -87.7280, "district": 17},
    15: {"name": "Portage Park", "lat": 41.9537, "lon": -87.7644, "district": 16},
    16: {"name": "Irving Park", "lat": 41.9535, "lon": -87.7189, "district": 17},
    17: {"name": "Dunning", "lat": 41.9472, "lon": -87.8066, "district": 16},
    18: {"name": "Montclare", "lat": 41.9294, "lon": -87.7981, "district": 25},
    19: {"name": "Belmont Cragin", "lat": 41.9264, "lon": -87.7658, "district": 25},
    20: {"name": "Hermosa", "lat": 41.9215, "lon": -87.7344, "district": 25},
    21: {"name": "Avondale", "lat": 41.9387, "lon": -87.7099, "district": 14},
    22: {"name": "Logan Square", "lat": 41.9231, "lon": -87.7093, "district": 14},
    23: {"name": "Humboldt Park", "lat": 41.9022, "lon": -87.7214, "district": 14},
    24: {"name": "West Town", "lat": 41.8979, "lon": -87.6833, "district": 12},
    25: {"name": "Austin", "lat": 41.8924, "lon": -87.7654, "district": 15},
    26: {"name": "West Garfield Park", "lat": 41.8794, "lon": -87.7289, "district": 11},
    27: {"name": "East Garfield Park", "lat": 41.8819, "lon": -87.7022, "district": 11},
    28: {"name": "Near West Side", "lat": 41.8744, "lon": -87.6633, "district": 12},
    29: {"name": "North Lawndale", "lat": 41.8587, "lon": -87.7139, "district": 10},
    30: {"name": "South Lawndale", "lat": 41.8384, "lon": -87.7139, "district": 10},
    31: {"name": "Lower West Side", "lat": 41.8542, "lon": -87.6698, "district": 12},
    32: {"name": "Loop (Downtown)", "lat": 41.8819, "lon": -87.6278, "district": 1},
    33: {"name": "Near South Side", "lat": 41.8566, "lon": -87.6244, "district": 1},
    34: {"name": "Armour Square", "lat": 41.8407, "lon": -87.6339, "district": 9},
    35: {"name": "Douglas", "lat": 41.8344, "lon": -87.6189, "district": 2},
    36: {"name": "Oakland", "lat": 41.8236, "lon": -87.6033, "district": 2},
    37: {"name": "Fuller Park", "lat": 41.8089, "lon": -87.6322, "district": 9},
    38: {"name": "Grand Boulevard", "lat": 41.8128, "lon": -87.6178, "district": 2},
    39: {"name": "Kenwood", "lat": 41.8089, "lon": -87.5933, "district": 2},
    40: {"name": "Washington Park", "lat": 41.7944, "lon": -87.6189, "district": 2},
    41: {"name": "Hyde Park", "lat": 41.7944, "lon": -87.5933, "district": 2},
    42: {"name": "Woodlawn", "lat": 41.7806, "lon": -87.5933, "district": 3},
    43: {"name": "South Shore", "lat": 41.7606, "lon": -87.5756, "district": 3},
    44: {"name": "Chatham", "lat": 41.7439, "lon": -87.6133, "district": 6},
    45: {"name": "Avalon Park", "lat": 41.7439, "lon": -87.5844, "district": 4},
    46: {"name": "South Chicago", "lat": 41.7397, "lon": -87.5533, "district": 4},
    47: {"name": "Burnside", "lat": 41.7289, "lon": -87.5956, "district": 5},
    48: {"name": "Calumet Heights", "lat": 41.7289, "lon": -87.5656, "district": 4},
    49: {"name": "Roseland", "lat": 41.7006, "lon": -87.6256, "district": 5},
    50: {"name": "Pullman", "lat": 41.6961, "lon": -87.6033, "district": 5},
    51: {"name": "South Deering", "lat": 41.6856, "lon": -87.5678, "district": 4},
    52: {"name": "East Side", "lat": 41.7067, "lon": -87.5356, "district": 4},
    53: {"name": "West Pullman", "lat": 41.6744, "lon": -87.6333, "district": 5},
    54: {"name": "Riverdale", "lat": 41.6506, "lon": -87.6033, "district": 5},
    55: {"name": "Hegewisch", "lat": 41.6556, "lon": -87.5456, "district": 4},
    56: {"name": "Garfield Ridge", "lat": 41.7944, "lon": -87.7689, "district": 8},
    57: {"name": "Archer Heights", "lat": 41.8089, "lon": -87.7289, "district": 8},
    58: {"name": "Brighton Park", "lat": 41.8189, "lon": -87.6989, "district": 9},
    59: {"name": "McKinley Park", "lat": 41.8319, "lon": -87.6733, "district": 9},
    60: {"name": "Bridgeport", "lat": 41.8364, "lon": -87.6489, "district": 9},
    61: {"name": "New City (Back of the Yards)", "lat": 41.8067, "lon": -87.6589, "district": 9},
    62: {"name": "West Elsdon", "lat": 41.7933, "lon": -87.7133, "district": 8},
    63: {"name": "Gage Park", "lat": 41.7933, "lon": -87.6989, "district": 8},
    64: {"name": "Clearing", "lat": 41.7789, "lon": -87.7689, "district": 8},
    65: {"name": "West Lawn", "lat": 41.7722, "lon": -87.7289, "district": 8},
    66: {"name": "Chicago Lawn", "lat": 41.7722, "lon": -87.6933, "district": 8},
    67: {"name": "West Englewood", "lat": 41.7753, "lon": -87.6667, "district": 7},
    68: {"name": "Englewood", "lat": 41.7753, "lon": -87.6416, "district": 7},
    69: {"name": "Greater Grand Crossing", "lat": 41.7606, "lon": -87.6189, "district": 3},
    70: {"name": "Ashburn", "lat": 41.7467, "lon": -87.7089, "district": 8},
    71: {"name": "Auburn Gresham", "lat": 41.7439, "lon": -87.6556, "district": 6},
    72: {"name": "Beverly", "lat": 41.7167, "lon": -87.6744, "district": 22},
    73: {"name": "Washington Heights", "lat": 41.7167, "lon": -87.6489, "district": 22},
    74: {"name": "Mount Greenwood", "lat": 41.6933, "lon": -87.7089, "district": 22},
    75: {"name": "Morgan Park", "lat": 41.6889, "lon": -87.6689, "district": 22},
    76: {"name": "O'Hare", "lat": 41.9786, "lon": -87.9047, "district": 16},
    77: {"name": "Edgewater", "lat": 41.9847, "lon": -87.6611, "district": 24}
}


# Rule-based severity groups used only for decision-support text (not predicted by the model)
HIGH_SEVERITY_TYPES = {'HOMICIDE', 'CRIMINAL SEXUAL ASSAULT', 'ROBBERY', 'WEAPONS VIOLATION', 'BATTERY',
                       'ASSAULT', 'KIDNAPPING', 'HUMAN TRAFFICKING', 'ARSON'}
MODERATE_SEVERITY_TYPES = {'BURGLARY', 'MOTOR VEHICLE THEFT', 'NARCOTICS', 'CRIMINAL DAMAGE', 'SEX OFFENSE',
                           'OFFENSE INVOLVING CHILDREN', 'STALKING', 'INTIMIDATION', 'THEFT'}


class InvalidInputError(ValueError):
    """Raised when a request is well-formed but outside what the model was trained on."""


def incident_timestamp(year: int, month: int, day_name: str, hour: int) -> dt.datetime:
    """First date in the given year/month that falls on the requested weekday, at the given hour."""
    first = dt.date(year, month, 1)
    offset = (DAY_INDEX[day_name] - first.weekday()) % 7
    return dt.datetime(year, month, 1 + offset, hour)


def matching_dates(year: int, month: int, day_name: str, hour: int) -> List[dt.datetime]:
    """Every date in the given year/month that falls on the requested weekday, at the given hour."""
    first = incident_timestamp(year, month, day_name, hour)
    days_in_month = calendar.monthrange(year, month)[1]
    return [first + dt.timedelta(days=7 * i) for i in range(5) if first.day + 7 * i <= days_in_month]


# The form gives an hour, not an exact report time. Predictions are averaged over typical minutes:
# minute 0 with its training share (reports are often rounded to the hour), the rest spread evenly.
OTHER_MINUTES = [10, 20, 30, 40, 50]


def severity_for(category: str) -> str:
    if category in HIGH_SEVERITY_TYPES:
        return "High"
    if category in MODERATE_SEVERITY_TYPES:
        return "Moderate"
    return "Low"


class CrimePredictor:
    """Serves the final XGBoost bundle; falls back to the interim model only if it is absent."""

    def __init__(self):
        self.bundle = None
        self.interim_model = None
        self.interim_encoder = None
        self.metrics = {}
        self._load_artifacts()

    def _load_artifacts(self):
        if os.path.exists(FINAL_METRICS_FILE):
            with open(FINAL_METRICS_FILE, encoding="utf-8") as f:
                self.metrics = json.load(f)
        if os.path.exists(FINAL_BUNDLE_FILE):
            self.bundle = joblib.load(FINAL_BUNDLE_FILE)
            print(f"[INFO] Loaded final model bundle: {type(self.bundle['model']).__name__}")
        elif os.path.exists(MODEL_FILE) and os.path.exists(LABEL_ENCODER_FILE):
            self.interim_model = joblib.load(MODEL_FILE)
            self.interim_encoder = joblib.load(LABEL_ENCODER_FILE)
            print("[WARNING] final_model_bundle.joblib not found - serving the INTERIM Random Forest "
                  "from train_model.py. Build it with: python -m backend.train_final_model")
        else:
            print("[ERROR] No model artifacts found in backend/models/.")

    @property
    def is_final(self) -> bool:
        return self.bundle is not None

    @property
    def is_loaded(self) -> bool:
        return self.bundle is not None or self.interim_model is not None

    @property
    def model_name(self) -> str:
        if self.is_final:
            selection = self.metrics.get("selection", {})
            return f"{selection.get('model', 'XGBoost')} - final selected model"
        if self.interim_model is not None:
            return "Random Forest - interim model (final bundle not installed)"
        return "No model loaded"

    def _resolve_inputs(self, req: CrimePredictionRequest) -> dict:
        area = CHICAGO_AREAS_DATA[req.communityArea]
        timestamp = incident_timestamp(req.year, req.month, req.dayOfWeek, req.hourOfDay)
        return {
            "date": timestamp,
            "location_description": req.locationDescription,
            "beat": req.beat,
            "district": req.district if req.district is not None else area["district"],
            "ward": req.ward,
            "community_area": req.communityArea,
            "latitude": req.latitude if req.latitude is not None else area["lat"],
            "longitude": req.longitude if req.longitude is not None else area["lon"],
            "domestic": req.domestic,
        }

    def _final_probabilities(self, raw: dict, req: CrimePredictionRequest):
        if raw["location_description"] not in known_locations(self.bundle):
            raise InvalidInputError(f"Unknown locationDescription '{raw['location_description']}'.")
        on_hour = self.bundle["on_the_hour_share"]
        minute_weights = [(0, on_hour)] + [(m, (1 - on_hour) / len(OTHER_MINUTES)) for m in OTHER_MINUTES]
        dates = matching_dates(req.year, req.month, req.dayOfWeek, req.hourOfDay)
        rows, weights = [], []
        for day in dates:
            for minute, weight in minute_weights:
                rows.append({**raw, "date": day.replace(minute=minute)})
                weights.append(weight / len(dates))
        probabilities = predict_proba_raw(self.bundle, pd.DataFrame(rows)[RAW_FEATURES])
        return np.average(probabilities, axis=0, weights=weights), list(self.bundle["classes"])

    def _interim_probabilities(self, raw: dict):
        encoder = self.interim_model.named_steps["preprocessor"].named_transformers_["cat"]
        if raw["location_description"] not in set(encoder.categories_[0]):
            raise InvalidInputError(f"Unknown locationDescription '{raw['location_description']}'.")
        ts = raw["date"]
        district = raw["district"]
        frame = pd.DataFrame([{
            "hour": ts.hour, "month": ts.month, "day_of_week": ts.weekday(),
            "is_weekend": int(ts.weekday() >= 5), "domestic": int(raw["domestic"]),
            "community_area": raw["community_area"], "district": district,
            "ward": raw["ward"] if raw["ward"] is not None else 0,
            "beat": raw["beat"] if raw["beat"] is not None else district * 100 + 11,
            "latitude": raw["latitude"], "longitude": raw["longitude"],
            "location_description": raw["location_description"],
        }])
        return self.interim_model.predict_proba(frame)[0], list(self.interim_encoder.classes_)

    def predict(self, req: CrimePredictionRequest) -> CrimePredictionResponse:
        if not self.is_loaded:
            raise RuntimeError("No model is loaded on the server.")

        raw = self._resolve_inputs(req)
        if self.is_final:
            probabilities, classes = self._final_probabilities(raw, req)
        else:
            probabilities, classes = self._interim_probabilities(raw)

        top = np.argsort(probabilities)[::-1][:5]
        top_probs: List[PredictionProbability] = [
            PredictionProbability(category=str(classes[i]), probability=round(float(probabilities[i]), 3))
            for i in top
        ]
        predicted = top_probs[0].category
        area_name = CHICAGO_AREAS_DATA[req.communityArea]["name"]
        severity = severity_for(predicted)

        recommendations = [
            f"Most likely incident type in {area_name} for this context: {predicted.title()} "
            f"({top_probs[0].probability:.0%} model probability).",
            f"Brief District {raw['district']} patrols on {predicted.title()} prevention for "
            f"{req.dayOfWeek}s around {req.hourOfDay:02d}:00.",
        ]
        if top_probs[0].probability < 0.4:
            recommendations.append(
                "Low-confidence prediction: also prepare for the next most likely types "
                f"({', '.join(p.category.title() for p in top_probs[1:3])})."
            )
        if severity == "High":
            recommendations.append("Violent-crime category: consider additional visible patrol presence.")

        resolved = {k: (v.isoformat() if isinstance(v, dt.datetime) else v) for k, v in raw.items()}
        if self.is_final:
            resolved["averaged_over"] = (f"every {req.dayOfWeek} in {calendar.month_name[req.month]} {req.year} "
                                         f"at {req.hourOfDay:02d}:00-{req.hourOfDay:02d}:59")
        return CrimePredictionResponse(
            success=True,
            predictedCategory=predicted,
            confidence=round(float(top_probs[0].probability), 3),
            topProbabilities=top_probs,
            modelName=self.model_name,
            isFinalModel=self.is_final,
            severityLevel=severity,
            recommendations=recommendations,
            area=f"{area_name} (Area #{req.communityArea})",
            resolvedInputs=resolved,
        )


predictor = CrimePredictor()
