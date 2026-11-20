from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import sklearn
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import make_pipeline
import transformers
from transformers import AutoImageProcessor, Dinov2Model

from compost_ai.data import prepare_manifest


def extract(path: str, processor, backbone, device) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    batch = processor(images=image, return_tensors="pt")
    batch = {key: value.to(device) for key, value in batch.items()}
    with torch.inference_mode():
        return backbone(**batch).last_hidden_state[:, 0, :].cpu().numpy()[0]


def run(data_root: Path, manifest_path: Path, out: Path, backbone_name: str, seed: int,
        backbone_cache: Path | None = None, backbone_revision: str | None = None):
    frame = prepare_manifest(data_root, manifest_path, seed=seed)
    model_source = str(backbone_cache) if backbone_cache else backbone_name
    processor = AutoImageProcessor.from_pretrained(model_source, use_fast=False, local_files_only=bool(backbone_cache))
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    backbone = Dinov2Model.from_pretrained(model_source, local_files_only=bool(backbone_cache)).to(device).eval()
    features = np.stack([extract(row.path, processor, backbone, device) for row in frame.itertuples()])
    frame = frame.reset_index(drop=True)
    train_mask = frame.split == "train"
    val_mask = frame.split == "validation"
    test_mask = frame.split == "test"
    encoder = LabelEncoder().fit(frame.loc[train_mask, "label"])
    y_train = encoder.transform(frame.loc[train_mask, "label"])
    y_val = encoder.transform(frame.loc[val_mask, "label"])
    y_test = encoder.transform(frame.loc[test_mask, "label"])
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed))
    model.fit(features[train_mask], y_train)
    classifier = model[-1]
    # Calibrate confidence and OOD distance using validation only; test remains held out.
    val_prob = model.predict_proba(features[val_mask])
    sorted_prob = np.sort(val_prob, axis=1)
    margins = sorted_prob[:, -1] - sorted_prob[:, -2]
    val_conf = sorted_prob[:, -1]
    val_pred = model.predict(features[val_mask])
    val_centroids = {label: features[train_mask & (frame.label.to_numpy() == label)].mean(axis=0) for label in encoder.classes_}
    val_dist = np.array([np.linalg.norm(row - val_centroids[encoder.classes_[pred]]) for row, pred in zip(features[val_mask], val_pred)])
    thresholds = {
        "minimum_confidence": float(np.quantile(val_conf, 0.10)),
        "minimum_margin": float(np.quantile(margins, 0.10)),
        "ood_distance": float(np.quantile(val_dist, 0.99)),
    }
    pred = model.predict(features[test_mask])
    y_true = y_test
    report = classification_report(y_true, pred, labels=np.arange(len(encoder.classes_)), target_names=encoder.classes_, output_dict=True, zero_division=0)
    macro = precision_recall_fscore_support(y_true, pred, average="macro", zero_division=0)
    # Measure the online path on the held-out test images, including embedding and head.
    import time
    per_image_ms = []
    accepted_test = []
    for idx in np.flatnonzero(test_mask):
        start = time.perf_counter()
        vector = extract(frame.iloc[idx].path, processor, backbone, device).reshape(1, -1)
        probabilities = model.predict_proba(vector)[0]
        order = np.argsort(probabilities)[::-1]
        candidate = int(order[0])
        confidence = float(probabilities[candidate])
        margin = confidence - float(probabilities[order[1]]) if len(order) > 1 else confidence
        distance = float(np.linalg.norm(vector[0] - val_centroids[encoder.classes_[candidate]]))
        accepted_test.append(confidence >= thresholds["minimum_confidence"] and margin >= thresholds["minimum_margin"] and distance <= thresholds["ood_distance"])
        per_image_ms.append((time.perf_counter() - start) * 1000)
    latency_ms = float(np.mean(per_image_ms))
    accepted_test = np.asarray(accepted_test, dtype=bool)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out / "classifier.joblib")
    backbone_dir = out / "backbone"
    backbone.save_pretrained(backbone_dir, safe_serialization=True)
    processor.save_pretrained(backbone_dir)
    materials = {label: label.split("__", 1)[0] for label in encoder.classes_}
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    metadata = {
        "model_version": "0.1.0",
        "backbone": backbone_name,
        "backbone_path": "backbone",
        "backbone_license": "Apache-2.0",
        "labels": encoder.classes_.tolist(),
        "materials": materials,
        "thresholds": thresholds,
        "class_centroids": {label: val_centroids[label].tolist() for label in encoder.classes_},
        "preprocessing": "AutoImageProcessor.from_pretrained(backbone); RGB; CLS token; identical training/inference processor",
        "manifest_sha256": manifest_sha256,
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__, "scikit_learn": sklearn.__version__},
        "backbone_revision": backbone_revision or getattr(backbone.config, "_commit_hash", None),
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (out / "labels.json").write_text(json.dumps({"labels": metadata["labels"], "materials": materials}, indent=2), encoding="utf-8")
    (out / "training_config.json").write_text(json.dumps({
        "backbone": backbone_name,
        "seed": seed,
        "test_fraction": 0.15,
        "validation_fraction": 0.15,
        "classifier": "StandardScaler + LogisticRegression(class_weight=balanced, max_iter=2000)",
        "confidence_and_ood_calibration_split": "validation",
        "manifest_sha256": manifest_sha256,
    }, indent=2), encoding="utf-8")
    (out / "THIRD_PARTY.md").write_text(
        "DINOv2 ViT-B/14 checkpoint: `facebook/dinov2-base`, Apache-2.0.\n"
        "Source and license: https://github.com/facebookresearch/dinov2\n\n"
        "Training images: Recyclable Waste Image Dataset, João Alves (2026), CC BY 4.0.\n"
        "Dataset DOI: https://doi.org/10.17632/h5pxbsdz4m.1\n",
        encoding="utf-8",
    )
    metrics = {
        "accuracy": accuracy_score(y_true, pred),
        "macro_precision": float(macro[0]), "macro_recall": float(macro[1]), "macro_f1": float(macro[2]),
        "confusion_matrix": confusion_matrix(y_true, pred, labels=np.arange(len(encoder.classes_))).tolist(),
        "labels": encoder.classes_.tolist(), "per_class": report,
        "mean_inference_latency_ms_including_feature_extraction_and_classifier": latency_ms,
        "selective_coverage": float(accepted_test.mean()),
        "selective_accuracy": float(accuracy_score(y_true[accepted_test], pred[accepted_test])) if accepted_test.any() else None,
        "rejected_test_samples": int((~accepted_test).sum()),
        "test_samples": int(test_mask.sum()), "threshold_calibration_split": "validation",
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True, help="Class folders: data/<class-name>/*")
    parser.add_argument("--manifest", type=Path, default=Path("data/processed/manifest.csv"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/model"))
    parser.add_argument("--backbone", default="facebook/dinov2-base")
    parser.add_argument("--backbone-cache", type=Path, help="Local checkpoint directory; skips online download.")
    parser.add_argument("--backbone-revision", help="Exact upstream commit hash for provenance.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.data, args.manifest, args.out, args.backbone, args.seed, args.backbone_cache, args.backbone_revision)
