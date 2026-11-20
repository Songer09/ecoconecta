from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, Dinov2Model


class WasteRecognizer:
    """Loads DINOv2 and the trained sklearn head once, then serves predictions."""

    def __init__(self, artifact_dir: str | Path):
        root = Path(artifact_dir)
        required = [root / "classifier.joblib", root / "metadata.json"]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError("Trained model artifacts missing: " + ", ".join(missing))
        self.metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
        self.classifier = joblib.load(root / "classifier.joblib")
        backbone_path = root / self.metadata.get("backbone_path", "backbone")
        self.processor = AutoImageProcessor.from_pretrained(backbone_path, use_fast=False)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.backbone = Dinov2Model.from_pretrained(backbone_path).to(self.device).eval()
        self.labels = self.metadata["labels"]

    @torch.inference_mode()
    def embed(self, image: Image.Image) -> np.ndarray:
        inputs = self.processor(images=image.convert("RGB"), return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        return self.backbone(**inputs).last_hidden_state[:, 0, :].cpu().numpy()

    def predict(self, image: Image.Image) -> dict:
        vector = self.embed(image)
        probabilities = self.classifier.predict_proba(vector)[0]
        order = np.argsort(probabilities)[::-1]
        index = int(order[0])
        confidence = float(probabilities[index])
        margin = confidence - float(probabilities[order[1]]) if len(order) > 1 else confidence
        centroid = np.asarray(self.metadata["class_centroids"][self.labels[index]], dtype=np.float32)
        distance = float(np.linalg.norm(vector[0] - centroid))
        thresholds = self.metadata["thresholds"]
        ood = distance > float(thresholds["ood_distance"])
        accepted = confidence >= thresholds["minimum_confidence"] and margin >= thresholds["minimum_margin"] and not ood
        return {
            "material": self.metadata["materials"].get(self.labels[index]),
            "predicted_class": self.labels[index] if accepted else None,
            "candidate_class": self.labels[index],
            "confidence": confidence,
            "confidence_margin": margin,
            "out_of_distribution": ood,
            "accepted": accepted,
            "ood_distance": distance,
        }
