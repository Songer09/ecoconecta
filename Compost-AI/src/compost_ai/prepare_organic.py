from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from PIL import Image, UnidentifiedImageError


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
FOOD_ROOT = Path("data/raw/extracted/food-waste-bangladesh-v1/unpacked/Root")
RECYCLABLE_ROOT = Path("data/processed/curated")
NEAR_DUPLICATE_EXCLUSIONS = {"IMG_4806.JPG"}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def prepare(manifest: Path, audit_path: Path, seed: int = 42) -> pd.DataFrame:
    rows: list[dict] = []
    damaged: list[dict] = []
    seen_hashes: dict[str, Path] = {}

    food_splits = {
        "Buffet Food waste": "train",
        "Food waste (General)": "train",
        "Restaurant  food  waste": "validation",
        "Vegetables  waste": "validation",
        "Wedding  Food waste": "test",
    }
    for folder in sorted(FOOD_ROOT.iterdir()):
        split = food_splits.get(folder.name)
        if split is None:
            continue
        for path in sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES):
            if path.name in NEAR_DUPLICATE_EXCLUSIONS:
                continue
            try:
                with Image.open(path) as im:
                    im.verify()
                sha = digest(path)
            except (UnidentifiedImageError, OSError, ValueError) as exc:
                damaged.append({"path": str(path), "reason": str(exc)})
                continue
            if sha in seen_hashes:
                damaged.append({"path": str(path), "reason": f"exact_duplicate_of:{seen_hashes[sha]}"})
                continue
            seen_hashes[sha] = path
            rows.append({"path": str(path.resolve()), "label": "organic_food_waste_scene",
                         "source_dataset": "food_waste_bangladesh_v1", "source_group": folder.name,
                         "original_label": folder.name, "split": split, "sha256": sha,
                         "label_scope": "scene-level food waste; not item-level compostability"})

    urban: list[dict] = []
    calheta: list[dict] = []
    for class_dir in sorted(p for p in RECYCLABLE_ROOT.iterdir() if p.is_dir()):
        for path in sorted(p for p in class_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES):
            group = path.parent.name
            if group not in {"Urban and Household Waste", "Calheta Waste Management Facility"}:
                continue
            try:
                with Image.open(path) as im:
                    im.verify()
                sha = digest(path)
            except (UnidentifiedImageError, OSError, ValueError) as exc:
                damaged.append({"path": str(path), "reason": str(exc)})
                continue
            if sha in seen_hashes:
                damaged.append({"path": str(path), "reason": f"exact_duplicate_of:{seen_hashes[sha]}"})
                continue
            seen_hashes[sha] = path
            entry = {"path": str(path.resolve()), "label": "recyclable_material_scene",
                     "source_dataset": "recyclable_waste_image_dataset_v1", "source_group": group,
                     "original_label": class_dir.name, "split": "", "sha256": sha,
                     "label_scope": "known recyclable material subset; not all non-organic waste"}
            (calheta if group == "Calheta Waste Management Facility" else urban).append(entry)

    # Keep the complete Calheta collection out of model fitting and threshold selection.
    for row in calheta:
        row["split"] = "test"
    # Validation is sampled within Urban, stratified by material. It is not a context-held-out set.
    frame = pd.DataFrame(urban)
    if frame.empty or frame.original_label.nunique() < 2:
        raise ValueError("Expected several recyclable material classes in Urban group.")
    for label, group in frame.groupby("original_label", sort=True):
        shuffled = group.sample(frac=1, random_state=seed)
        n_val = max(1, round(len(shuffled) * 0.2)) if len(shuffled) > 3 else 1
        for idx, row in enumerate(shuffled.to_dict("records")):
            row["split"] = "validation" if idx < n_val else "train"
            rows.append(row)

    rows.extend(calheta)
    prepared = pd.DataFrame(rows).sort_values(["split", "label", "path"]).reset_index(drop=True)
    if prepared.sha256.duplicated().any():
        raise ValueError("Duplicate image hashes remain in the prepared manifest.")
    # Tests must be separated by capture-context group from training for each target class.
    for label, subset in prepared.groupby("label"):
        test_groups = set(subset.loc[subset.split == "test", "source_group"])
        train_groups = set(subset.loc[subset.split == "train", "source_group"])
        if test_groups & train_groups:
            raise ValueError(f"Capture-context leakage for {label}: {test_groups & train_groups}")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(manifest, index=False)
    counts = {f"{split}/{label}": int(n) for (split, label), n in prepared.groupby(["split", "label"]).size().items()}
    audit = {
        "task": "organic food-waste scenes versus known recyclable-material scenes",
        "unknown_policy": "confidence/margin/OOD rejection; no supervised unknown class",
        "random_seed": seed,
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "unique_images": len(prepared),
        "class_split_counts": counts,
        "group_split_counts": {f"{label}/{split}": dict(Counter(groups)) for (label, split), groups in
                                prepared.groupby(["label", "split"]).source_group.apply(list).items()},
        "near_duplicate_excluded_without_deletion": sorted(NEAR_DUPLICATE_EXCLUSIONS),
        "damaged_or_duplicate_exclusions": damaged,
        "test_groups_are_disjoint_from_train_within_each_target_class": True,
        "limitations": [
            "The labels describe dataset folders/scenes, not every object in an image.",
            "Food-waste images include surrounding dishes/utensils and may not depict organic matter as the sole object.",
            "The negative class is only the known recyclable subset and is not all non-organic waste.",
            "Both classes have one dataset lineage; held-out locations/events test context transfer, not dataset-source transfer.",
            "The recyclable validation images share the Urban capture context with training; only the final test is context-held-out.",
        ],
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return prepared


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data/processed/organic-binary-manifest.csv"))
    parser.add_argument("--audit", type=Path, default=Path("data/processed/organic-binary-manifest.audit.json"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = prepare(args.manifest, args.audit, args.seed)
    print(result.groupby(["split", "label"]).size().to_string())
