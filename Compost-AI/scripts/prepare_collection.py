from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd
import yaml
from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data/collection/capture_manifest.csv"
DEFAULT_BASELINE = ROOT / "data/processed/bdwaste-individual-train-manifest.csv"
DEFAULT_OUT = ROOT / "data/processed/training-ready-expanded-manifest.csv"
MIN_OBJECTS = {"train": 10, "validation": 3, "test": 3}
VIEWS = {"top", "oblique"}
TRUE_VALUES = {"true", "yes", "1"}
FALSE_VALUES = {"false", "no", "0"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(manifest_path: Path, baseline_path: Path | None, output_path: Path,
             min_train: int, min_validation: int, min_test: int) -> dict:
    taxonomy = yaml.safe_load((ROOT / "config/material_taxonomy.yaml").read_text(encoding="utf-8"))
    classes = taxonomy["classes"]
    frame = pd.read_csv(manifest_path, keep_default_na=False)
    required = {"image_id", "image_path", "label_material", "object_id", "session_id", "split", "role", "view",
                "contaminated", "condition", "capture_date", "device", "site_group", "photographer",
                "license_or_consent", "notes"}
    missing_cols = sorted(required - set(frame.columns))
    if missing_cols:
        raise ValueError(f"Capture manifest missing columns: {missing_cols}")

    errors: list[dict] = []
    images: list[dict] = []
    for idx, row in frame.iterrows():
        line = idx + 2
        label = row.label_material.strip()
        if label not in classes:
            errors.append({"row": line, "image_id": row.image_id, "error": f"Unknown taxonomy label: {label}"})
            continue
        if not row.object_id.strip() or not row.session_id.strip():
            errors.append({"row": line, "image_id": row.image_id, "error": "object_id and session_id are required"})
            continue
        role = row.role.strip()
        expected_role = "ood_eval" if label == "unknown_or_ambiguous" else "classifier"
        if role != expected_role:
            errors.append({"row": line, "image_id": row.image_id, "error": f"Expected role={expected_role}"})
            continue
        if row.split not in {"train", "validation", "test", "ood_test"}:
            errors.append({"row": line, "image_id": row.image_id, "error": "Invalid split"})
            continue
        if (role == "ood_eval") != (row.split == "ood_test"):
            errors.append({"row": line, "image_id": row.image_id, "error": "OOD rows must use split=ood_test; classifier rows must not"})
            continue
        if row.view not in VIEWS:
            errors.append({"row": line, "image_id": row.image_id, "error": "view must be top or oblique"})
            continue
        contamination = row.contaminated.strip().lower()
        if contamination not in TRUE_VALUES | FALSE_VALUES:
            errors.append({"row": line, "image_id": row.image_id, "error": "contaminated must be true/false"})
            continue
        for field in ["condition", "capture_date", "device", "site_group", "photographer", "license_or_consent"]:
            if not row[field].strip():
                errors.append({"row": line, "image_id": row.image_id, "error": f"{field} is required"})
        try:
            date.fromisoformat(row.capture_date.strip())
        except ValueError:
            errors.append({"row": line, "image_id": row.image_id, "error": "capture_date must be YYYY-MM-DD"})
        if label == "unknown_or_ambiguous" and not row.notes.strip():
            errors.append({"row": line, "image_id": row.image_id, "error": "Explain why the example is unknown/ambiguous in notes"})
        path = (ROOT / row.image_path).resolve()
        try:
            path.relative_to(ROOT / "data/collection/images")
        except ValueError:
            errors.append({"row": line, "image_id": row.image_id, "error": "image_path must stay under data/collection/images"})
            continue
        if not path.is_file():
            errors.append({"row": line, "image_id": row.image_id, "error": f"Image file missing: {row.image_path}"})
            continue
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                width, height = image.size
                fmt = image.format
            if fmt not in {"JPEG", "PNG", "WEBP"} or min(width, height) < 128:
                errors.append({"row": line, "image_id": row.image_id, "error": f"Unsupported/low-resolution image: {fmt} {width}x{height}"})
                continue
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            errors.append({"row": line, "image_id": row.image_id, "error": f"Image cannot be decoded: {exc}"})
            continue
        digest = file_sha256(path)
        images.append({**row.to_dict(), "path": str(path), "label": label, "sha256": digest,
                       "source_dataset": "COMPOST_AI_local_capture",
                       "source_group": f"COMPOST_AI_local_capture|{row.object_id}",
                       "family": row.family or classes[label]["family"]})

    valid = pd.DataFrame(images)
    if not valid.empty:
        # Object and session IDs must never leak between partitions.
        for id_field in ["object_id", "session_id"]:
            leakage = valid.groupby(["source_dataset", id_field]).split.nunique()
            for source, value in leakage[leakage > 1].items():
                errors.append({"row": "group", "image_id": str(value), "error": f"{id_field} {source} appears in multiple splits"})
        for (source, object_id), group in valid[valid.role == "classifier"].groupby(["source_dataset", "object_id"]):
            if group.label.nunique() != 1 or set(group.view) != VIEWS or len(group) != 2:
                errors.append({"row": "group", "image_id": object_id,
                               "error": "Each classifier object needs exactly one top and one oblique image with one label"})
        for (source, object_id), group in valid[valid.role == "ood_eval"].groupby(["source_dataset", "object_id"]):
            if set(group.view) != VIEWS or len(group) != 2:
                errors.append({"row": "group", "image_id": object_id,
                               "error": "Each OOD object needs exactly one top and one oblique image"})
        for digest, group in valid.groupby("sha256"):
            if len(group) > 1:
                errors.append({"row": "duplicate", "image_id": digest, "error": f"Exact duplicate image appears {len(group)} times"})

    classifier = valid[valid.role == "classifier"].copy() if not valid.empty else pd.DataFrame()
    class_report = {}
    if not classifier.empty:
        for label, group in classifier.groupby("label"):
            objects_per_split = {split: int(group.loc[group.split == split, "object_id"].nunique())
                                 for split in ["train", "validation", "test"]}
            ready = (objects_per_split["train"] >= min_train and
                     objects_per_split["validation"] >= min_validation and
                     objects_per_split["test"] >= min_test)
            class_report[label] = {"photos": int(len(group)), "objects": int(group.object_id.nunique()),
                                   "objects_by_split": objects_per_split, "eligible_for_training": ready}
    eligible_local = {label for label, result in class_report.items() if result["eligible_for_training"]}
    baseline = pd.DataFrame()
    baseline_labels: set[str] = set()
    if baseline_path and baseline_path.is_file():
        baseline = pd.read_csv(baseline_path, keep_default_na=False)
        if "label" in baseline:
            baseline_labels = set(baseline.label.astype(str))
    # Existing baseline classes remain trainable from BDWaste while any available
    # locally captured examples for those labels may be added incrementally.
    eligible = eligible_local | (set(class_report) & baseline_labels)
    incomplete = sorted(set(class_report) - eligible)
    classifier = classifier[classifier.label.isin(eligible)] if not classifier.empty else classifier
    ood = valid[valid.role == "ood_eval"].copy() if not valid.empty else pd.DataFrame()

    ready_frames = []
    if not baseline.empty:
        ready_frames.append(baseline)
    if not classifier.empty:
        ready_frames.append(classifier)
    if ready_frames:
        ready_manifest = pd.concat(ready_frames, ignore_index=True, sort=False)
        # Validate split purity after joining the public seed and local collection.
        if "visual_group" in ready_manifest.columns:
            ready_manifest["_split_group"] = ready_manifest.source_group.astype(str)
            unassigned_bdwaste = (ready_manifest.source_dataset.astype(str).eq("BDWaste_v1") &
                                  ready_manifest.get("object_id", pd.Series("UNASSIGNED", index=ready_manifest.index))
                                  .astype(str).str.casefold().isin({"unassigned", "", "nan", "none"}))
            ready_manifest.loc[unassigned_bdwaste, "_split_group"] = ready_manifest.loc[unassigned_bdwaste, "visual_group"].astype(str)
            leakage = ready_manifest.groupby(["source_dataset", "_split_group"]).split.nunique()
            ready_manifest = ready_manifest.drop(columns=["_split_group"])
            if (leakage > 1).any():
                raise ValueError("Combined manifest has visual/object groups crossing splits; resolve before training")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ready_manifest.to_csv(output_path, index=False)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame().to_csv(output_path, index=False)
    ood_path = ROOT / "data/processed/collection-ood-manifest.csv"
    if not ood.empty:
        ood.to_csv(ood_path, index=False)

    report = {
        "capture_manifest": str(manifest_path), "training_manifest": str(output_path),
        "errors": errors, "eligible_classes": sorted(eligible), "pending_classes_below_minimum": incomplete,
        "baseline_classes_preserved": sorted(baseline_labels),
        "per_class": class_report, "ood_photos": int(len(ood)),
        "minimum_objects_by_split": {"train": min_train, "validation": min_validation, "test": min_test},
        "training_manifest_rows": int(sum(len(x) for x in ready_frames)),
        "status": "ready" if not errors and bool(eligible) else "needs_corrections_or_more_images",
    }
    report_path = ROOT / "data/processed/collection-validation-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate local COMPOST AI photo collection and export a training manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--baseline-manifest", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--min-train-objects", type=int, default=MIN_OBJECTS["train"])
    parser.add_argument("--min-validation-objects", type=int, default=MIN_OBJECTS["validation"])
    parser.add_argument("--min-test-objects", type=int, default=MIN_OBJECTS["test"])
    parser.add_argument("--without-bdwaste", action="store_true", help="Export only collected images.")
    args = parser.parse_args()
    result = validate(args.manifest, None if args.without_bdwaste else args.baseline_manifest,
                      args.output, args.min_train_objects, args.min_validation_objects, args.min_test_objects)
    print(json.dumps({k: v for k, v in result.items() if k != "errors"}, indent=2, ensure_ascii=False))
    if result["errors"]:
        print(f"Validation errors: {len(result['errors'])}; see data/processed/collection-validation-report.json")
        raise SystemExit(2)
    if not result["eligible_classes"]:
        print("No new class meets the minimum split counts yet.")
        raise SystemExit(2)
