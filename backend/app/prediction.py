import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .config import MODEL_FILE, LABEL_ENCODER_FILE
from .schemas import CrimePredictionRequest, CrimePredictionResponse, PredictionProbability

DAY_MAP = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4,
    'Saturday': 5,
    'Sunday': 6
}

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

COMMUNITY_NAME_TO_ID = {v["name"].lower(): k for k, v in CHICAGO_AREAS_DATA.items()}

HIGH_SEVERITY_TYPES = {'HOMICIDE', 'CRIMINAL SEXUAL ASSAULT', 'ROBBERY', 'WEAPONS VIOLATION', 'BATTERY', 'ASSAULT', 'BURGLARY', 'MOTOR VEHICLE THEFT'}

class CrimePredictor:
    def __init__(self):
        self.model = None
        self.label_encoder = None
        self._load_artifacts()

    def _load_artifacts(self):
        try:
            if os.path.exists(MODEL_FILE) and os.path.exists(LABEL_ENCODER_FILE):
                self.model = joblib.load(MODEL_FILE)
                self.label_encoder = joblib.load(LABEL_ENCODER_FILE)
                print("[INFO] Successfully loaded Chicago Crime ML Model & Label Encoder.")
            else:
                print("[WARNING] Model artifacts not found. Predictions will run in simulation mode.")
        except Exception as e:
            print(f"[ERROR] Error loading model: {e}")

    def predict(self, req: CrimePredictionRequest) -> CrimePredictionResponse:
        day_idx = DAY_MAP.get(req.dayOfWeek, 4)
        is_weekend = 1 if day_idx in [5, 6] else 0
        
        # Resolve community area id and location
        if isinstance(req.communityArea, int):
            comm_id = req.communityArea
        elif str(req.communityArea).isdigit():
            comm_id = int(req.communityArea)
        else:
            comm_id = COMMUNITY_NAME_TO_ID.get(str(req.communityArea).strip().lower(), 32)

        area_info = CHICAGO_AREAS_DATA.get(comm_id, CHICAGO_AREAS_DATA[32])
        area_name = area_info["name"]

        # Fill default lat/lon if not provided
        lat = req.latitude if req.latitude is not None else area_info["lat"]
        lon = req.longitude if req.longitude is not None else area_info["lon"]
        district = req.district if req.district is not None else area_info["district"]
        ward = req.ward if req.ward is not None else 42
        beat = req.beat if req.beat is not None else (district * 100 + 11)

        # Standardize location description
        loc_desc = req.locationDescription.strip().upper() if req.locationDescription else "STREET"

        input_df = pd.DataFrame([{
            'hour': req.hourOfDay,
            'month': req.month or 6,
            'day_of_week': day_idx,
            'is_weekend': is_weekend,
            'domestic': 1 if req.domestic else 0,
            'community_area': comm_id,
            'district': district,
            'ward': ward,
            'beat': beat,
            'latitude': lat,
            'longitude': lon,
            'location_description': loc_desc
        }])

        top_probs: List[PredictionProbability] = []
        predicted_cat = 'THEFT'
        confidence = 0.65

        if self.model is not None and self.label_encoder is not None:
            try:
                probabilities = self.model.predict_proba(input_df)[0]
                classes = self.label_encoder.classes_
                top_indices = np.argsort(probabilities)[::-1][:5]

                top_probs = [
                    PredictionProbability(
                        category=str(classes[idx]),
                        probability=round(float(probabilities[idx]), 3)
                    )
                    for idx in top_indices
                ]

                predicted_cat = top_probs[0].category
                confidence = top_probs[0].probability
            except Exception as e:
                print(f"[WARN] Inference fallback: {e}")

        if not top_probs:
            # Heuristic simulation if model unavailable
            if req.domestic:
                top_probs = [
                    PredictionProbability(category='BATTERY', probability=0.48),
                    PredictionProbability(category='ASSAULT', probability=0.26),
                    PredictionProbability(category='CRIMINAL DAMAGE', probability=0.14),
                    PredictionProbability(category='OTHER OFFENSE', probability=0.12)
                ]
            elif loc_desc in ['DEPARTMENT STORE', 'GROCERY FOOD STORE', 'SMALL RETAIL STORE', 'RESTAURANT']:
                top_probs = [
                    PredictionProbability(category='THEFT', probability=0.55),
                    PredictionProbability(category='DECEPTIVE PRACTICE', probability=0.22),
                    PredictionProbability(category='CRIMINAL TRESPASS', probability=0.13),
                    PredictionProbability(category='BURGLARY', probability=0.10)
                ]
            elif loc_desc in ['STREET', 'PARKING LOT', 'ALLEY', 'SIDEWALK']:
                top_probs = [
                    PredictionProbability(category='MOTOR VEHICLE THEFT', probability=0.36),
                    PredictionProbability(category='THEFT', probability=0.32),
                    PredictionProbability(category='ROBBERY', probability=0.18),
                    PredictionProbability(category='WEAPONS VIOLATION', probability=0.14)
                ]
            else:
                top_probs = [
                    PredictionProbability(category='THEFT', probability=0.42),
                    PredictionProbability(category='BATTERY', probability=0.28),
                    PredictionProbability(category='CRIMINAL DAMAGE', probability=0.18),
                    PredictionProbability(category='ASSAULT', probability=0.12)
                ]
            predicted_cat = top_probs[0].category
            confidence = top_probs[0].probability

        # Calculate dynamic risk score & arrest likelihood based on features
        is_night = 1 if (req.hourOfDay >= 22 or req.hourOfDay <= 5) else 0
        is_high_sev = 1 if predicted_cat in HIGH_SEVERITY_TYPES else 0
        
        base_risk = 45 + (is_night * 20) + (is_high_sev * 25) + (15 if req.domestic else 0)
        risk_score = min(98, max(25, int(base_risk + (confidence * 15))))

        risk_level = "High" if risk_score >= 70 else "Moderate" if risk_score >= 45 else "Low"

        # Arrest probability calculation
        if predicted_cat in ['WEAPONS VIOLATION', 'NARCOTICS', 'CRIMINAL TRESPASS']:
            arrest_prob = round(0.72 + (0.15 * np.random.rand()), 2)
        elif req.domestic or predicted_cat in ['BATTERY', 'ASSAULT']:
            arrest_prob = round(0.48 + (0.12 * np.random.rand()), 2)
        elif predicted_cat in ['MOTOR VEHICLE THEFT', 'BURGLARY']:
            arrest_prob = round(0.12 + (0.08 * np.random.rand()), 2)
        else:
            arrest_prob = round(0.20 + (0.10 * np.random.rand()), 2)

        # Estimated emergency response time (minutes)
        if risk_level == "High":
            est_time = "3.8 mins"
        elif risk_level == "Moderate":
            est_time = "5.2 mins"
        else:
            est_time = "7.4 mins"

        recommendations = [
            f"Prioritize patrol units in {area_name} (District {district}, Beat {beat}).",
            f"Deploy sector surveillance for potential {predicted_cat} patterns.",
            "Alert district dispatch of elevated probability during current time window.",
            "Coordinate field verification with beat patrol officers."
        ]

        return CrimePredictionResponse(
            success=True,
            predictedCategory=predicted_cat,
            riskScore=risk_score,
            riskLevel=risk_level,
            arrestProbability=arrest_prob,
            confidence=round(float(confidence), 2),
            primaryHotspot=f"{area_name} (Area #{comm_id})",
            estimatedResponseTime=est_time,
            topProbabilities=top_probs,
            recommendations=recommendations
        )

predictor = CrimePredictor()
