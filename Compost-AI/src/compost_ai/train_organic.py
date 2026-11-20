from __future__ import annotations

import argparse
import hashlib
import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import torch
import transformers
from PIL import Image
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, LinearSVC
from transformers import AutoImageProcessor, Dinov2Model

from compost_ai.train import extract


def run(manifest_path: Path, out: Path, backbone_cache: Path, seed: int = 42) -> dict:
    frame = pd.read_csv(manifest_path)
    required = {"path", "label", "source_dataset", "source_group", "split", "sha256"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Manifest lacks fields: {sorted(required - set(frame.columns))}")
    if frame.sha256.duplicated().any():
        raise ValueError("Manifest contains duplicate image hashes.")
    for label, subset in frame.groupby("label"):
        if set(subset.loc[subset.split == "train", "source_group"]) & set(subset.loc[subset.split == "test", "source_group"]):
            raise ValueError(f"Training/test context leakage for {label}.")
    train_mask = frame.split.eq("train").to_numpy()
    val_mask = frame.split.eq("validation").to_numpy()
    test_mask = frame.split.eq("test").to_numpy()
    if min(train_mask.sum(), val_mask.sum(), test_mask.sum()) == 0:
        raise ValueError("Train, validation, and test partitions must all be non-empty.")

    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    processor = AutoImageProcessor.from_pretrained(backbone_cache, use_fast=False, local_files_only=True)
    backbone = Dinov2Model.from_pretrained(backbone_cache, local_files_only=True).to(device).eval()
    features = []
    started = time.perf_counter()
    batch_size = 8
    for start_idx in range(0, len(frame), batch_size):
        paths = frame.path.iloc[start_idx:start_idx + batch_size].tolist()
        images = []
        for path in paths:
            with Image.open(path) as image:
                images.append(image.convert("RGB"))
        batch = processor(images=images, return_tensors="pt")
        batch = {key: value.to(device) for key, value in batch.items()}
        with torch.inference_mode():
            vectors = backbone(**batch).last_hidden_state[:, 0, :].cpu().numpy()
        features.extend(vectors)
        if (start_idx // batch_size) % 20 == 0:
            print(f"DINOv2 embeddings: {min(start_idx + len(paths), len(frame))}/{len(frame)}", flush=True)
    features = np.asarray(features, dtype=np.float32)
    extraction_seconds = time.perf_counter() - started

    labels = sorted(frame.loc[train_mask, "label"].unique().tolist())
    if set(labels) != set(frame.label.unique()):
        raise ValueError("Every class must be present in training.")
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    y = frame.label.map(label_to_idx).to_numpy()
    candidates = {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(
            max_iter=3000, class_weight="balanced", random_state=seed)),
        "linear_svc_calibrated": make_pipeline(StandardScaler(), CalibratedClassifierCV(
            estimator=LinearSVC(class_weight="balanced", random_state=seed), cv=3)),
        "rbf_svc": make_pipeline(StandardScaler(), SVC(C=1.0, kernel="rbf", class_weight="balanced",
                                                       probability=True, random_state=seed)),
    }
    comparison = {}
    fitted = {}
    for name, model in candidates.items():
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model.fit(features[train_mask], y[train_mask])
        pred = model.predict(features[val_mask])
        p, r, f, _ = precision_recall_fscore_support(y[val_mask], pred, average="macro", zero_division=0)
        comparison[name] = {"validation_accuracy": float(accuracy_score(y[val_mask], pred)),
                            "validation_macro_precision": float(p), "validation_macro_recall": float(r),
                            "validation_macro_f1": float(f), "fit_warnings": [str(w.message) for w in caught]}
        fitted[name] = model
    selected_name = sorted(comparison, key=lambda name: (-comparison[name]["validation_macro_f1"],
                                                          -comparison[name]["validation_macro_recall"], name))[0]
    model = fitted[selected_name]

    val_probs = model.predict_proba(features[val_mask])
    val_order = np.sort(val_probs, axis=1)
    val_conf = val_order[:, -1]
    val_margin = val_order[:, -1] - val_order[:, -2]
    train_centroids = {label: features[train_mask & (frame.label.to_numpy() == label)].mean(axis=0) for label in labels}
    val_pred = model.predict(features[val_mask])
    val_dist = np.asarray([np.linalg.norm(vector - train_centroids[labels[pred]])
                           for vector, pred in zip(features[val_mask], val_pred)])
    thresholds = {
        "minimum_confidence": float(np.quantile(val_conf, 0.10)),
        "minimum_margin": float(np.quantile(val_margin, 0.10)),
        "ood_distance": float(np.quantile(val_dist, 0.99)),
    }

    pred = model.predict(features[test_mask])
    y_test = y[test_mask]
    report = classification_report(y_test, pred, labels=np.arange(len(labels)), target_names=labels,
                                   output_dict=True, zero_division=0)
    macro_p, macro_r, macro_f, _ = precision_recall_fscore_support(y_test, pred, average="macro", zero_division=0)
    test_positions = np.flatnonzero(test_mask)
    accepted = []
    latencies = []
    # Measure live image-to-prediction latency independently on the held-out test images.
    for idx in test_positions:
        with Image.open(frame.iloc[idx].path) as image:
            start = time.perf_counter()
            vector = extract(frame.iloc[idx].path, processor, backbone, device).reshape(1, -1)
            probabilities = model.predict_proba(vector)[0]
            top = np.argsort(probabilities)[::-1]
            candidate = int(top[0])
            confidence = float(probabilities[candidate])
            margin = confidence - float(probabilities[top[1]])
            distance = float(np.linalg.norm(vector[0] - train_centroids[labels[candidate]]))
            accepted.append(confidence >= thresholds["minimum_confidence"] and
                            margin >= thresholds["minimum_margin"] and
                            distance <= thresholds["ood_distance"])
            latencies.append((time.perf_counter() - start) * 1000)
    accepted = np.asarray(accepted, dtype=bool)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out / "classifier.joblib")
    backbone.save_pretrained(out / "backbone", safe_serialization=True)
    processor.save_pretrained(out / "backbone")
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    metadata = {
        "model_version": "0.2.0-organic-scene",
        "task_scope": "scene-level organic food-waste scenes versus known recyclable-material scenes",
        "unknown_policy": "reject to review using confidence, margin, and embedding distance; unknown has no supervised label",
        "backbone": "facebook/dinov2-base (DINOv2 ViT-B/14)", "backbone_path": "backbone",
        "backbone_license": "Apache-2.0", "backbone_revision": getattr(backbone.config, "_commit_hash", None),
        "labels": labels,
        "materials": {"organic_food_waste_scene": "organic_food_waste_scene",
                      "recyclable_material_scene": "recyclable_material_scene"},
        "confidence_calibrated": False,
        "thresholds": thresholds,
        "class_centroids": {label: train_centroids[label].tolist() for label in labels},
        "preprocessing": "RGB then AutoImageProcessor from bundled DINOv2 checkpoint; CLS token; same training/inference path",
        "manifest_sha256": manifest_sha,
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__, "scikit_learn": sklearn.__version__},
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (out / "labels.json").write_text(json.dumps({"labels": labels, "scope": metadata["task_scope"]}, indent=2), encoding="utf-8")
    (out / "training_config.json").write_text(json.dumps({
        "seed": seed, "selected_classifier": selected_name, "validation_model_comparison": comparison,
        "candidate_selection_metric": "validation macro F1; tie-break validation macro recall",
        "threshold_calibration_split": "validation only", "manifest_sha256": manifest_sha,
        "feature_extraction_device": str(device), "feature_batch_size": batch_size,
        "feature_extraction_seconds": extraction_seconds,
    }, indent=2), encoding="utf-8")
    (out / "THIRD_PARTY.md").write_text(
        "DINOv2 ViT-B/14: facebook/dinov2-base, Apache-2.0; https://github.com/facebookresearch/dinov2\n\n"
        "Positive training scenes: An image dataset for food waste in Bangladesh v1, CC BY 4.0; "
        "https://doi.org/10.17632/y3vy6hmthy.1\n\n"
        "Negative subset: Recyclable Waste Image Dataset v1, CC BY 4.0; "
        "https://doi.org/10.17632/h5pxbsdz4m.1\n\n"
        "Labels are dataset-level scene/context labels and are not item-level compostability labels. "
        "See reports/organic-model-audit-2026-11.md for source limitations and attribution.\n",
        encoding="utf-8")
    metrics = {
        "test_accuracy": float(accuracy_score(y_test, pred)), "macro_precision": float(macro_p),
        "macro_recall": float(macro_r), "macro_f1": float(macro_f),
        "confusion_matrix": confusion_matrix(y_test, pred, labels=np.arange(len(labels))).tolist(),
        "labels": labels, "per_class": report, "test_images": int(test_mask.sum()),
        "test_groups": {label: sorted(set(frame.loc[test_mask & (frame.label == label), "source_group"])) for label in labels},
        "mean_inference_latency_ms_including_dinov2_and_classifier": float(np.mean(latencies)),
        "p50_inference_latency_ms_including_dinov2_and_classifier": float(np.median(latencies)),
        "selective_coverage": float(accepted.mean()),
        "selective_accuracy": float(accuracy_score(y_test[accepted], pred[accepted])) if accepted.any() else None,
        "rejected_test_samples": int((~accepted).sum()),
        "thresholds_from_validation_only": thresholds,
        "candidate_model_comparison_validation_only": comparison,
        "false_compost_approvals": 0,
        "environmental_policy": "all current class mappings require review; zero automatic compost approvals is policy behavior, not empirical compostability validation",
        "out_of_distribution_limit": "OOD thresholds use only in-distribution validation embeddings; external unknown behavior is reported separately and was not used to tune thresholds.",
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data/processed/organic-binary-manifest.csv"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/model_organic_binary"))
    parser.add_argument("--backbone-cache", type=Path, default=Path("artifacts/model/backbone"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = run(args.manifest, args.out, args.backbone_cache, args.seed)
    print(json.dumps(result, indent=2))
