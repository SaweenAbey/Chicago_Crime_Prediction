"""API tests for the prediction service. Run from backend/: python -m pytest -v"""
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.prediction import incident_timestamp, predictor

client = TestClient(app)

VALID = {
    "communityArea": 68,
    "locationDescription": "STREET",
    "dayOfWeek": "Saturday",
    "hourOfDay": 23,
    "month": 7,
}


def test_health_reports_model_status():
    body = client.get("/health").json()
    assert body["model_loaded"] is True
    assert "active_model" in body


def test_model_info_returns_recorded_test_metrics():
    body = client.get("/api/model/info").json()
    assert body["metrics"]["selection"]["model"] == "XGBoost"
    assert 0 < body["metrics"]["test"]["accuracy"] < 1


def test_valid_prediction_returns_probabilities():
    response = client.post("/api/predict", json=VALID)
    assert response.status_code == 200
    body = response.json()
    probs = [p["probability"] for p in body["topProbabilities"]]
    assert body["predictedCategory"] == body["topProbabilities"][0]["category"]
    assert probs == sorted(probs, reverse=True)
    assert all(0 <= p <= 1 for p in probs)
    assert body["resolvedInputs"]["district"] == 7  # derived from Englewood


def test_prediction_is_deterministic():
    first = client.post("/api/predict", json=VALID).json()
    second = client.post("/api/predict", json=VALID).json()
    assert first == second


def test_location_is_normalised():
    response = client.post("/api/predict", json={**VALID, "locationDescription": "  street "})
    assert response.status_code == 200
    assert response.json()["resolvedInputs"]["location_description"] == "STREET"


@pytest.mark.parametrize("override, field", [
    ({"communityArea": 0}, "communityArea"),
    ({"communityArea": 78}, "communityArea"),
    ({"dayOfWeek": "Funday"}, "dayOfWeek"),
    ({"hourOfDay": 24}, "hourOfDay"),
    ({"month": 13}, "month"),
    ({"latitude": 0.0}, "latitude"),
    ({"longitude": 0.0}, "longitude"),
    ({"ward": 99}, "ward"),
    ({"locationDescription": "   "}, "locationDescription"),
    ({"crimeType": "THEFT"}, "crimeType"),  # target variable must not be accepted as input
])
def test_invalid_inputs_are_rejected(override, field):
    response = client.post("/api/predict", json={**VALID, **override})
    assert response.status_code == 422
    assert field in str(response.json()["detail"])


@pytest.mark.parametrize("missing", ["communityArea", "locationDescription", "dayOfWeek", "hourOfDay", "month"])
def test_missing_required_inputs_are_rejected(missing):
    payload = {k: v for k, v in VALID.items() if k != missing}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422
    assert missing in str(response.json()["detail"])


def test_unknown_location_is_rejected():
    response = client.post("/api/predict", json={**VALID, "locationDescription": "MOON BASE"})
    assert response.status_code == 422
    assert "MOON BASE" in response.json()["detail"]


def test_incident_timestamp_matches_requested_weekday():
    ts = incident_timestamp(2026, 7, "Saturday", 23)
    assert ts.strftime("%A") == "Saturday" and ts.month == 7 and ts.hour == 23
    assert ts == dt.datetime(2026, 7, 4, 23)


def test_pipeline_endpoint_removed():
    assert client.post("/api/pipeline/run").status_code in (404, 405)


@pytest.mark.skipif(not predictor.is_final, reason="final_model_bundle.joblib not installed")
def test_final_bundle_is_served():
    body = client.post("/api/predict", json=VALID).json()
    assert body["isFinalModel"] is True
    assert "XGBoost" in body["modelName"]
