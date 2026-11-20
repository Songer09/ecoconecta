import io
from types import SimpleNamespace

from fastapi.testclient import TestClient
from PIL import Image

from compost_ai.api import app
from compost_ai.contracts import EnvironmentalDecision, EnvironmentalResult


def client():
    def decide(profile, cls, accepted):
        if profile not in {"household", "community", "industrial"}:
            raise ValueError(f"Unknown compost profile: {profile}")
        return EnvironmentalResult(
            decision=EnvironmentalDecision.REQUIRES_REVIEW, profile=profile, reason="review"
        )
    app.state.rules = SimpleNamespace(decide=decide)
    app.state.rules.category_for = lambda material: "inorganic" if material == "plastic" else None
    app.state.recognizer = SimpleNamespace(
        metadata={"model_version": "test", "confidence_calibrated": False},
        predict=lambda image: {
            "accepted": True, "out_of_distribution": False, "predicted_class": "plastic",
            "material": "plastic", "confidence": 0.99, "confidence_margin": 0.9,
            "candidate_class": "plastic", "ood_distance": 10.0,
        },
    )
    return TestClient(app)


def test_invalid_image_is_rejected():
    response = client().post("/api/v1/recognize", files={"image": ("x.txt", b"not an image", "text/plain")})
    assert response.status_code == 415


def test_unknown_profile_is_rejected_before_inference():
    response = client().post("/api/v1/recognize", data={"compost_profile": "mars"}, files={"image": ("x.png", b"x", "image/png")})
    assert response.status_code == 422


def test_response_exposes_category_calibration_and_review_state():
    image = Image.new("RGB", (8, 8), "white")
    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    response = client().post("/api/v1/recognize", files={"image": ("x.jpg", stream.getvalue(), "image/jpeg")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["waste_category"] == "inorganic"
    assert payload["confidence_calibrated"] is False
    assert payload["manual_review_required"] is True
    assert payload["justification"] == payload["environmental"]["reason"]
    assert payload["handling_recommendation"]
