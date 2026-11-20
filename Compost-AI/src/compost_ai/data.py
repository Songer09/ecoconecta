from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
from PIL import Image, UnidentifiedImageError
from sklearn.model_selection import train_test_split


def prepare_manifest(source: str | Path, destination: str | Path, seed: int = 42,
                     validation_fraction: float = 0.15, test_fraction: float = 0.15) -> pd.DataFrame:
    """Index class-folder images and create reproducible, stratified data splits."""
    root = Path(source)
    rows = []
    damaged = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}):
        relative = path.relative_to(root)
        label = relative.parts[0] if len(relative.parts) > 1 else path.parent.name
        source_dataset = relative.parts[1] if len(relative.parts) > 3 else "unspecified"
        source_group = relative.parts[2] if len(relative.parts) > 3 else source_dataset
        try:
            with Image.open(path) as image:
                image.verify()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            damaged.append({"path": str(path.resolve()), "reason": str(exc)})
            continue
        rows.append({"path": str(path.resolve()), "label": label, "sha256": digest,
                     "source_dataset": source_dataset, "source_group": source_group})
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError(f"No supported images found under {root}")
    if frame.groupby("label").size().min() < 3:
        raise ValueError("At least three valid images per class are needed for train/validation/test splits.")
    duplicates = frame[frame.duplicated("sha256", keep=False)]
    duplicate_labels = duplicates.groupby("sha256")["label"].nunique()
    conflicting_hashes = set(duplicate_labels[duplicate_labels > 1].index)
    conflicts = frame[frame.sha256.isin(conflicting_hashes)]
    if not conflicts.empty:
        frame = frame[~frame.sha256.isin(conflicting_hashes)]
    if not duplicates.empty:
        frame = frame.drop_duplicates("sha256", keep="first").reset_index(drop=True)
    if frame.empty or frame.groupby("label").size().min() < 3:
        raise ValueError("Cleaning left fewer than three images for at least one class; inspect the audit and labels.")
    test_fraction = max(test_fraction, 1e-6)
    remaining, test = train_test_split(frame, test_size=test_fraction, random_state=seed, stratify=frame["label"])
    val_relative = validation_fraction / (1.0 - test_fraction)
    train, validation = train_test_split(remaining, test_size=val_relative, random_state=seed, stratify=remaining["label"])
    frame = pd.concat([train.assign(split="train"), validation.assign(split="validation"), test.assign(split="test")])
    out = Path(destination)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.sort_values(["split", "label", "path"]).to_csv(out, index=False)
    class_counts = {f"{split}/{label}": int(count) for (split, label), count in frame.groupby(["split", "label"]).size().items()}
    audit = {
        "unique_images": len(frame),
        "exact_duplicate_images_removed": int(len(duplicates)),
        "cross_label_duplicate_images_excluded": int(len(conflicts)),
        "damaged_images_excluded": len(damaged),
        "damaged_files": damaged,
        "class_counts": class_counts,
        "source_counts_by_split": {
            str(split): {str(source): int(count) for source, count in subset.groupby("source_dataset").size().items()}
            for split, subset in frame.groupby("split")
        },
    }
    out.with_suffix(".audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return frame
