from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/collection/capture_manifest.csv"
BASELINE = ["banana_peel", "potato_peel", "mango_peel", "sugarcane_husk", "plastic", "glass"]
PRIORITY = ["coffee_grounds", "leaves_dry", "leaves_green", "vegetable_scraps", "eggshell", "metal"]
VIEWS = ["top", "oblique"]
FIELDS = [
    "image_id", "image_path", "label_material", "family", "subtype", "object_id", "session_id",
    "split", "role", "view", "contaminated", "condition", "capture_date", "device", "site_group",
    "photographer", "license_or_consent", "sha256", "notes",
]


def generate(output: Path = OUT) -> int:
    plan = output.with_name("capture_plan_priority.csv")
    if output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing collection manifest: {output}. "
            "Choose a new --output path to make a fresh blank plan."
        )
    if plan.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing collection quota plan: {plan}. "
            "Choose an output path in a new directory."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    class_rows = []
    for label in BASELINE + PRIORITY:
        family = "baseline_material" if label in BASELINE else "priority_new_material"
        counts = {"train": 15, "validation": 5, "test": 5}
        for split, object_count in counts.items():
            split_tag = {"train": "tr", "validation": "va", "test": "te"}[split]
            session_id = f"capture_{split}_01"
            for n in range(1, object_count + 1):
                object_id = f"{label}_{split_tag}_{n:03d}"
                for view in VIEWS:
                    image_id = f"{object_id}__{view}"
                    rows.append({
                        "image_id": image_id,
                        "image_path": f"data/collection/images/{label}/{image_id}.jpg",
                        "label_material": label,
                        "family": family,
                        "subtype": "",
                        "object_id": object_id,
                        "session_id": session_id,
                        "split": split,
                        "role": "classifier",
                        "view": view,
                        "contaminated": "",
                        "condition": "",
                        "capture_date": "",
                        "device": "",
                        "site_group": "",
                        "photographer": "",
                        "license_or_consent": "",
                        "sha256": "",
                        "notes": "",
                    })
        class_rows.append({"label_material": label, "physical_objects": 25, "train_objects": 15,
                           "validation_objects": 5, "locked_test_objects": 5, "photos_per_object": 2,
                           "photos_total": 50, "photo_views": "top;oblique"})

    for n in range(1, 21):
        object_id = f"unknown_ood_{n:03d}"
        session_id = "capture_ood_test_01"
        for view in VIEWS:
            image_id = f"{object_id}__{view}"
            rows.append({
                "image_id": image_id,
                "image_path": f"data/collection/images/unknown_or_ambiguous/{image_id}.jpg",
                "label_material": "unknown_or_ambiguous",
                "family": "rejection",
                "subtype": "",
                "object_id": object_id,
                "session_id": session_id,
                "split": "ood_test",
                "role": "ood_eval",
                "view": view,
                "contaminated": "",
                "condition": "",
                "capture_date": "",
                "device": "",
                "site_group": "",
                "photographer": "",
                "license_or_consent": "",
                "sha256": "",
                "notes": "Describe why this object is unknown, ambiguous, or out of scope.",
            })
    with output.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with plan.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(class_rows[0]))
        writer.writeheader()
        writer.writerows(class_rows)
    print(f"Created {len(rows)} photo slots: {output}")
    print(f"Created class quota plan: {plan}")
    print("Pilot target: 600 classifier photos + 40 unknown/OOD photos.")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate pre-labeled COMPOST AI photo capture slots.")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    generate(args.output)
