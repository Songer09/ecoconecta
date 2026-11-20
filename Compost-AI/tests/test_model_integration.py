from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from compost_ai.api import app


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "artifacts/model_bdwaste_individual"
MANIFEST = PROJECT_ROOT / "data/processed/bdwaste-individual-train-manifest.csv"
MODEL_READY = (MODEL_DIR / "metadata.json").is_file() and (MODEL_DIR / "classifier.joblib").is_file()


@pytest.mark.skipif(not MODEL_READY or not MANIFEST.is_file(), reason="Run the authorized training pipeline first.")
def test_api_runs_individual_material_model_on_grouped_holdout_photographs():
    manifest = pd.read_csv(MANIFEST)
    test_rows = manifest[manifest.split == "test"].sort_values("label").drop_duplicates("label")
    assert len(test_rows) >= 2
    with TestClient(app) as client:
        for row in test_rows.itertuples():
            path = Path(row.path)
            with path.open("rb") as photo:
                response = client.post(
                    "/api/v1/recognize",
                    data={"compost_profile": "household"},
                    files={"image": (path.name, photo, "image/jpeg")},
                )
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload["status"] in {"recognized", "review_required", "unknown"}
            assert payload["metadata"]["candidate_class"] == row.label
            expected_decision = "COMPOSTABLE" if row.label in {"banana_peel", "potato_peel", "mango_peel", "sugarcane_husk"} else "NO_COMPOSTABLE"
            if payload["status"] == "recognized":
                assert payload["environmental"]["decision"] == expected_decision
            else:
                assert payload["environmental"]["decision"] == "REQUIRES_REVIEW"
            assert isinstance(payload["confidence"], float)
            assert payload["out_of_distribution"] in {True, False}
            assert payload["request_id"]
            assert payload["confidence_calibrated"] is False
            assert payload["manual_review_required"] == (payload["status"] != "recognized")
            assert payload["justification"] == payload["environmental"]["reason"]
            assert payload["waste_category"] in {None, "organic", "inorganic"}
            assert payload["model_version"] == "0.3.0-bdwaste-individual-experimental"
            assert payload["handling_recommendation"]
