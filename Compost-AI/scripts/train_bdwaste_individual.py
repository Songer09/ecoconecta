from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import torch
import transformers
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from transformers import AutoImageProcessor, Dinov2Model


CLASSES = ["banana_peel", "potato_peel", "mango_peel", "sugarcane_husk", "plastic", "glass"]
EXCLUDE_SOURCE_FILES = {
    # Full contact-sheet review: intact potato tubers are not potato peel waste.
    "potato_peel": {"117.jpg", "118.jpg", "89.jpg", "86.jpg", "90.jpg", "87.jpg", "85.jpg", "88.jpg"},
    # Folder includes an intact banana bunch rather than discarded peel.
    "banana_peel": {"116.jpg"},
    # These mango-folder photos contain an intact green mango beside peel; exclude the mixed/ambiguous frame.
    "mango_peel": {"7.jpg", *{f"{number}.jpg" for number in range(61, 90)}},
}
EXCLUSION_REASONS = {
    "banana_peel": "Image shows an intact banana bunch, not discarded peel.",
    "potato_peel": "Image shows one or more whole potato tubers, not peel waste.",
    "mango_peel": "Image includes an intact green mango with peel pieces; ambiguous mixed frame.",
}


def load_encoder(backbone_dir: Path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processor = AutoImageProcessor.from_pretrained(backbone_dir, use_fast=False, local_files_only=True)
    backbone = Dinov2Model.from_pretrained(backbone_dir, local_files_only=True).to(device).eval()
    return processor, backbone, device


@torch.inference_mode()
def embed_paths(paths: list[str], processor, backbone, device, batch_size: int = 8) -> np.ndarray:
    features: list[np.ndarray] = []
    for start in range(0, len(paths), batch_size):
        batch_paths = paths[start:start + batch_size]
        images = []
        for path in batch_paths:
            with Image.open(path) as image:
                images.append(image.convert("RGB"))
        inputs = processor(images=images, return_tensors="pt")
        inputs = {key: value.to(device) for key, value in inputs.items()}
        features.extend(backbone(**inputs).last_hidden_state[:, 0, :].cpu().numpy())
        done = min(start + len(batch_paths), len(paths))
        if done == len(paths) or done % 64 == 0:
            print(f"DINOv2 ViT-B/14 features: {done}/{len(paths)}", flush=True)
    return np.asarray(features, dtype=np.float32)


def build_group_ids(frame: pd.DataFrame, features: np.ndarray, cosine_threshold: float) -> tuple[np.ndarray, list[dict]]:
    # Conservative connected components over very high-cosine DINO neighbours.
    # This approximates shared capture/object groups; it cannot recover missing source IDs.
    normalized = features / np.maximum(np.linalg.norm(features, axis=1, keepdims=True), 1e-12)
    parent = list(range(len(frame)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    pair_records: list[dict] = []
    labels = frame.label.to_numpy()
    for label in sorted(set(labels)):
        indices = np.flatnonzero(labels == label)
        sim = normalized[indices] @ normalized[indices].T
        for local_i in range(len(indices)):
            for local_j in range(local_i + 1, len(indices)):
                score = float(sim[local_i, local_j])
                if score >= cosine_threshold:
                    i, j = int(indices[local_i]), int(indices[local_j])
                    union(i, j)
                    pair_records.append({"label": label, "path_a": frame.iloc[i].path,
                                         "path_b": frame.iloc[j].path, "cosine_similarity": score})
        # Preserve explicit physical-object grouping supplied by the local collection.
        if "object_id" in frame.columns and "source_dataset" in frame.columns:
            explicit: dict[tuple[str, str], int] = {}
            for idx in indices:
                source = str(frame.iloc[idx].get("source_dataset", ""))
                object_id = str(frame.iloc[idx].get("object_id", ""))
                if not object_id.strip() or object_id.casefold() in {"unassigned", "nan", "none"}:
                    continue
                key = (source, object_id)
                if key in explicit:
                    union(idx, explicit[key])
                else:
                    explicit[key] = int(idx)
    roots: dict[int, str] = {}
    group_ids = []
    for idx in range(len(frame)):
        root = find(idx)
        roots.setdefault(root, f"{frame.iloc[idx].label}__group_{len(roots):04d}")
        group_ids.append(roots[root])
    return np.asarray(group_ids), pair_records


def split_by_group(frame: pd.DataFrame, seed: int, class_labels: list[str]) -> pd.Series:
    split = pd.Series(index=frame.index, dtype="object")
    for label in class_labels:
        indices = np.flatnonzero(frame.label.to_numpy() == label)
        groups = frame.iloc[indices].visual_group.to_numpy()
        unique_groups = np.unique(groups)
        if len(unique_groups) < 3:
            raise ValueError(f"{label} has only {len(unique_groups)} visual groups; cannot create train/val/test.")
        # Hold out about 20% of groups for test, then about 20% of the remainder for validation.
        outer = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
        trainval_local, test_local = next(outer.split(indices, groups=groups))
        trainval_idx = indices[trainval_local]
        test_idx = indices[test_local]
        inner = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed + 1)
        train_local, val_local = next(inner.split(trainval_idx, groups=frame.loc[trainval_idx, "visual_group"].to_numpy()))
        split.loc[frame.index[trainval_idx[train_local]]] = "train"
        split.loc[frame.index[trainval_idx[val_local]]] = "validation"
        split.loc[frame.index[test_idx]] = "test"
    return split


def run(manifest_path: Path, out: Path, backbone_dir: Path, seed: int, cosine_threshold: float,
        allow_new_classes: bool = False) -> dict:
    output_stem = "bdwaste-individual" if out.name == "model_bdwaste_individual" else out.name.replace("_", "-")
    split_manifest = Path("data/processed") / f"{output_stem}-training-manifest.csv"
    pair_path = Path("data/processed") / f"{output_stem}-visual-similar-pairs.csv"
    feature_path = Path("data/processed") / f"{output_stem}-dinov2-features.npz"
    curation_path = Path("data/processed") / f"{output_stem}-curation-exclusions.csv"
    frame = pd.read_csv(manifest_path, keep_default_na=False)
    if "label" not in frame or "path" not in frame:
        raise ValueError("Training manifest must include path and label columns.")
    if not allow_new_classes:
        frame = frame[frame.label.isin(CLASSES)].copy()
    elif "role" in frame:
        frame = frame[frame.role.astype(str).ne("ood_eval")].copy()
    frame = frame.reset_index(drop=True)
    class_labels = sorted(frame.label.astype(str).unique().tolist())
    if len(class_labels) < 2:
        raise ValueError("At least two labeled material classes are required.")
    frame["source_filename"] = (frame.original_member.map(lambda x: Path(x).name)
                                 if "original_member" in frame else "")
    if "source_dataset" not in frame:
        frame["source_dataset"] = "BDWaste_v1"
    manual_excluded = frame.apply(
        lambda row: row.source_dataset == "BDWaste_v1" and
        row.source_filename in EXCLUDE_SOURCE_FILES.get(row.label, set()), axis=1)
    exclusions = frame.loc[manual_excluded, ["path", "label", "source_filename", "sha256"]].copy()
    exclusions["reason"] = exclusions.label.map(EXCLUSION_REASONS)
    frame = frame.loc[~manual_excluded].copy().reset_index(drop=True)

    # Deduplicate exactly across all selected classes. Conflicting-label hashes are excluded.
    conflict_hashes = frame.groupby("sha256").label.nunique()
    conflicting = set(conflict_hashes[conflict_hashes > 1].index)
    if conflicting:
        cross_label = frame[frame.sha256.isin(conflicting)][["path", "label", "source_filename", "sha256"]].copy()
        cross_label["reason"] = "Exact SHA-256 duplicate has conflicting folder labels; excluded from every class."
        exclusions = pd.concat([exclusions, cross_label], ignore_index=True)
    frame = frame[~frame.sha256.isin(conflicting)].copy()
    duplicate_mask = frame.duplicated("sha256", keep="first")
    exact_duplicates = frame.loc[duplicate_mask, ["path", "label", "source_filename", "sha256"]].copy()
    exact_duplicates["reason"] = "Exact SHA-256 duplicate; keep first occurrence only."
    exclusions = pd.concat([exclusions, exact_duplicates], ignore_index=True)
    frame = frame.loc[~duplicate_mask].reset_index(drop=True)
    curation_path.parent.mkdir(parents=True, exist_ok=True)
    exclusions.to_csv(curation_path, index=False)
    processor, backbone, device = load_encoder(backbone_dir)
    extraction_start = time.perf_counter()
    if feature_path.is_file():
        cached = np.load(feature_path, allow_pickle=True)
        cache_index = {(str(path), str(label)): i for i, (path, label) in enumerate(zip(cached["paths"], cached["labels"]))}
        keys = list(zip(frame.path.astype(str), frame.label.astype(str)))
        if all(key in cache_index for key in keys):
            features = np.stack([cached["features"][cache_index[key]] for key in keys])
        else:
            features = embed_paths(frame.path.tolist(), processor, backbone, device)
    else:
        features = embed_paths(frame.path.tolist(), processor, backbone, device)
    extraction_seconds = time.perf_counter() - extraction_start
    group_ids, pairs = build_group_ids(frame, features, cosine_threshold)
    frame["visual_group"] = group_ids
    assigned_splits = set(frame.get("split", pd.Series(dtype=str)).astype(str))
    if {"train", "validation", "test"}.issubset(assigned_splits):
        frame["split"] = frame.split.astype(str)
        leaking_groups = frame.groupby("visual_group").split.nunique()
        if (leaking_groups > 1).any():
            raise ValueError("A visual/object group crosses preassigned train/validation/test splits.")
    else:
        frame["split"] = split_by_group(frame, seed, class_labels)
    frame["deduplication"] = "sha256 exact duplicates removed; high DINO cosine connected components grouped"
    if "COMPOST_AI_local_capture" in set(frame.source_dataset.astype(str)):
        frame["label_review"] = "BDWaste exclusions manually reviewed; local labels supplied by collector, not independently adjudicated"
    else:
        frame["label_review"] = "full contact sheets reviewed; exclusions recorded in training script"
    split_manifest.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(split_manifest, index=False)
    pd.DataFrame(pairs).to_csv(pair_path, index=False)
    np.savez_compressed(feature_path, features=features, paths=np.asarray(frame.path), labels=np.asarray(frame.label), groups=group_ids)

    labels = class_labels
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    y = frame.label.map(label_to_idx).to_numpy()
    train_mask = frame.split.eq("train").to_numpy()
    val_mask = frame.split.eq("validation").to_numpy()
    test_mask = frame.split.eq("test").to_numpy()
    for split_name, mask in [("train", train_mask), ("validation", val_mask), ("test", test_mask)]:
        missing_labels = sorted(set(labels) - set(frame.loc[mask, "label"].astype(str)))
        if missing_labels:
            raise ValueError(f"Split {split_name} is missing classes: {missing_labels}")
    classifier = make_pipeline(StandardScaler(), LogisticRegression(
        max_iter=3000, class_weight="balanced", random_state=seed))
    classifier.fit(features[train_mask], y[train_mask])
    val_prob = classifier.predict_proba(features[val_mask])
    val_pred = classifier.predict(features[val_mask])
    val_report = classification_report(y[val_mask], val_pred, labels=np.arange(len(labels)),
                                       target_names=labels, output_dict=True, zero_division=0)
    pred = classifier.predict(features[test_mask])
    true = y[test_mask]
    test_report = classification_report(true, pred, labels=np.arange(len(labels)), target_names=labels,
                                        output_dict=True, zero_division=0)
    macro_p, macro_r, macro_f, _ = precision_recall_fscore_support(true, pred, average="macro", zero_division=0)
    centroids = {label: features[train_mask & (frame.label.to_numpy() == label)].mean(axis=0) for label in labels}
    val_conf = np.max(val_prob, axis=1)
    val_sorted = np.sort(val_prob, axis=1)
    val_margin = val_sorted[:, -1] - val_sorted[:, -2]
    val_distances = [np.linalg.norm(vector - centroids[labels[int(predicted)]])
                     for vector, predicted in zip(features[val_mask], val_pred)]
    thresholds = {"minimum_confidence": float(np.quantile(val_conf, .10)),
                  "minimum_margin": float(np.quantile(val_margin, .10)),
                  "ood_distance": float(np.quantile(val_distances, .99))}

    # End-to-end image latency on grouped holdout samples (DINO + classifier).
    latency_ms = []
    latency_positions = []
    for label in labels:
        candidates = np.flatnonzero(test_mask & (frame.label.to_numpy() == label))
        latency_positions.extend(candidates[:5].tolist())
    for idx in latency_positions:
        start = time.perf_counter()
        one_feature = embed_paths([frame.iloc[idx].path], processor, backbone, device, batch_size=1)
        classifier.predict_proba(one_feature)
        latency_ms.append((time.perf_counter() - start) * 1000)

    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(classifier, out / "classifier.joblib")
    backbone.save_pretrained(out / "backbone", safe_serialization=True)
    processor.save_pretrained(out / "backbone")
    manifest_sha = hashlib.sha256(split_manifest.read_bytes()).hexdigest()
    group_counts = frame.groupby("label").visual_group.nunique().to_dict()
    split_strategy = ("preassigned splits, validated by object and visual groups"
                      if {"train", "validation", "test"}.issubset(assigned_splits)
                      else "GroupShuffleSplit 64/16/20 by approximate visual group per class")
    data_sources = sorted(frame.source_dataset.astype(str).unique().tolist())
    test_sources = sorted(frame.loc[test_mask, "source_dataset"].astype(str).unique().tolist())
    split_counts = frame.groupby(["label", "split"]).size().unstack(fill_value=0).to_dict(orient="index")
    group_split_counts = frame.groupby(["label", "split"]).visual_group.nunique().unstack(fill_value=0).to_dict(orient="index")
    meta = {
        "model_version": ("0.3.0-bdwaste-individual-experimental" if set(labels) == set(CLASSES)
                          else "0.4.0-material-expansion-experimental"),
        "task_scope": f"{len(labels)}-class individual waste material recognition; experimental; sources={data_sources}",
        "backbone": "facebook/dinov2-base (DINOv2 ViT-B/14)", "backbone_path": "backbone",
        "backbone_license": "Apache-2.0", "backbone_revision": getattr(backbone.config, "_commit_hash", None),
        "labels": labels, "materials": {label: label for label in labels},
        "confidence_calibrated": False, "thresholds": thresholds,
        "class_centroids": {label: centroids[label].tolist() for label in labels},
        "preprocessing": "RGB + bundled AutoImageProcessor + DINOv2 CLS token; shared train/inference path",
        "grouping": {"method": "within-class connected components using DINOv2 cosine similarity",
                     "cosine_similarity_threshold": cosine_threshold,
                     "explicit_object_ids": "used when provided; BDWaste images without IDs grouped by DINO similarity",
                     "limitation": "DINO similarity groups approximate capture/session identity"},
        "manifest_sha256": manifest_sha,
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__, "scikit_learn": sklearn.__version__},
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (out / "labels.json").write_text(json.dumps({"labels": labels, "materials": meta["materials"]}, indent=2), encoding="utf-8")
    (out / "training_config.json").write_text(json.dumps({
        "seed": seed, "classifier": "StandardScaler + balanced LogisticRegression(max_iter=3000)",
        "selection": f"{len(labels)} labeled classes from validated manifest; DINOv2 feature extractor frozen",
        "deduplication": "exact SHA-256 duplicates removed; cross-label exact-hash conflicts excluded",
        "visual_grouping": meta["grouping"], "split_strategy": split_strategy,
        "groups_per_class": group_counts, "groups_per_class_split": group_split_counts,
        "sample_counts_per_class_split": split_counts,
        "manually_excluded": {k: sorted(v) for k, v in EXCLUDE_SOURCE_FILES.items()},
        "test_sources": test_sources, "feature_extraction_seconds": extraction_seconds,
        "end_to_end_test_latency_ms_mean": float(np.mean(latency_ms)), "latency_measurement_images": len(latency_ms),
    }, indent=2), encoding="utf-8")
    third_party = (
        "DINOv2 ViT-B/14 (`facebook/dinov2-base`), Apache-2.0: https://github.com/facebookresearch/dinov2\n\n"
        "BDWaste v1, CC BY 4.0, DOI 10.17632/96g5pgfnfw.1: https://data.mendeley.com/datasets/96g5pgfnfw/1\n"
        "Attribute Rahman et al., Akter et al., Sultana et al., Farjana et al. (2024), Data in Brief 53, 110153.\n"
    )
    if "COMPOST_AI_local_capture" in data_sources:
        third_party += "Local photographs: collected and labeled for COMPOST AI; usage permissions recorded in the collection manifest.\n"
    (out / "THIRD_PARTY.md").write_text(third_party, encoding="utf-8")
    metrics = {
        "evaluation_type": ("approximate grouped holdout within BDWaste v1; not external validation"
                             if data_sources == ["BDWaste_v1"] else
                             f"preassigned object/session grouped holdout across sources: {data_sources}"),
        "test_accuracy": float(accuracy_score(true, pred)), "macro_precision": float(macro_p),
        "macro_recall": float(macro_r), "macro_f1": float(macro_f),
        "confusion_matrix": confusion_matrix(true, pred, labels=np.arange(len(labels))).tolist(),
        "labels": labels, "per_class": test_report, "validation_per_class": val_report,
        "test_samples": int(test_mask.sum()), "validation_samples": int(val_mask.sum()),
        "train_samples": int(train_mask.sum()), "visual_groups_by_class": group_counts,
        "visual_groups_by_class_and_split": group_split_counts, "sample_counts_by_class_and_split": split_counts,
        "mean_inference_latency_ms_including_dinov2_and_classifier": float(np.mean(latency_ms)),
        "p50_inference_latency_ms_including_dinov2_and_classifier": float(np.median(latency_ms)),
        "latency_measurement_images": len(latency_ms),
        "external_labeled_test": ("none available; no external accuracy reported" if data_sources == ["BDWaste_v1"] else test_sources),
        "unknown_rejection_test": "not independently measured; thresholds estimated from validation only",
        "error_analysis": {"test_rows": frame.loc[test_mask, ["path", "label", "visual_group"]].assign(
            true=true, predicted=pred, correct=(true == pred)).to_dict(orient="records")},
        "limitations": ["visual grouping approximates object/session identity",
                        f"dataset sources: {', '.join(data_sources)}",
                        "some images have multiple pieces/material context", "confidence scores are not calibrated",
                        "class labels identify visual material only; compostability comes from independent rules"],
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data/processed/bdwaste-individual-manifest.csv"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/model_bdwaste_individual"))
    parser.add_argument("--backbone-dir", type=Path, default=Path("artifacts/model/backbone"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cosine-threshold", type=float, default=.995)
    parser.add_argument("--allow-new-classes", action="store_true",
                        help="Train every label in a validated combined manifest instead of the six BDWaste baseline labels.")
    args = parser.parse_args()
    result = run(args.manifest, args.out, args.backbone_dir, args.seed, args.cosine_threshold,
                 allow_new_classes=args.allow_new_classes)
    print(json.dumps({k: v for k, v in result.items() if k != "error_analysis"}, indent=2))
