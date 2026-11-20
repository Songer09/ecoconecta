from __future__ import annotations

import hashlib
import json
import random
from io import BytesIO
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError


ROOT = Path("data/raw/downloads/bdwaste-v1")
EXTRACTED = Path("data/raw/extracted/bdwaste-v1")
MANIFEST = Path("data/processed/bdwaste-individual-manifest.csv")
AUDIT = Path("data/processed/bdwaste-individual-audit.json")
CONTACT = Path("data/processed/bdwaste-individual-sample.jpg")
CLASS_MAP = {
    "Banana peel.zip": "banana_peel",
    "Potato Peel.zip": "potato_peel",
    "Lemon Peel.zip": "lemon_peel_candidate",
    "Shell of Malta.zip": "malta_peel_candidate",
    "Mango Peel.zip": "mango_peel",
    " Egg shell.zip": "eggshell",
    " Sugarcane  husk.zip": "sugarcane_husk",
    "Pastic.zip": "plastic",
    "Glass.zip": "glass",
    "Cane.zip": "can_candidate",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def dhash(image: Image.Image) -> int:
    pixels = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    values = list(pixels.getdata())
    result = 0
    for y in range(8):
        for x in range(8):
            result = (result << 1) | int(values[y * 9 + x] > values[y * 9 + x + 1])
    return result


def extract_and_audit() -> tuple[pd.DataFrame, dict]:
    rows: list[dict] = []
    corrupt: list[dict] = []
    for zip_name, label in CLASS_MAP.items():
        archive_path = ROOT / zip_name
        if not archive_path.is_file():
            raise FileNotFoundError(f"Missing verified source ZIP: {archive_path}")
        with ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if member.is_dir() or Path(member.filename).suffix.lower() not in IMAGE_SUFFIXES:
                    continue
                rel = PurePosixPath(member.filename)
                if rel.is_absolute() or ".." in rel.parts:
                    raise ValueError(f"Unsafe archive path rejected: {member.filename}")
                target = EXTRACTED / label / Path(*rel.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                data = archive.read(member)
                try:
                    with Image.open(BytesIO(data)) as image:
                        image.verify()
                    with Image.open(BytesIO(data)) as image:
                        width, height = image.size
                        exif = image.getexif()
                        exif_names = {str(k): str(v) for k, v in exif.items()}
                        image_hash = hashlib.sha256(data).hexdigest()
                        perceptual_hash = dhash(image)
                        target.write_bytes(data)
                except (UnidentifiedImageError, OSError, ValueError) as exc:
                    corrupt.append({"file": member.filename, "label": label, "reason": str(exc)})
                    continue
                rows.append({
                    "path": str(target.resolve()), "label": label, "source_dataset": "BDWaste_v1",
                    "source_class_zip": zip_name, "source_group": "BDWaste_v1_no_per_image_group_ids",
                    "original_member": member.filename, "object_id": "UNASSIGNED",
                    "session_id": "UNASSIGNED", "sha256": image_hash,
                    "dhash_hex": f"{perceptual_hash:016x}", "width": width, "height": height,
                    "exif_entry_count": len(exif_names),
                    "exif_datetime_original": exif_names.get("36867", ""),
                    "exif_device_model": exif_names.get("272", ""),
                    "split": "unassigned",
                    "label_scope": "dataset folder class; image content pending human sample audit",
                })
    frame = pd.DataFrame(rows)
    exact_duplicates = frame[frame.duplicated("sha256", keep=False)].sort_values("sha256")
    near_pairs: list[dict] = []
    for label, subset in frame.groupby("label"):
        records = list(subset[["path", "dhash_hex"]].itertuples(index=False, name=None))
        vals = [(path, int(code, 16)) for path, code in records]
        for i, (path_a, hash_a) in enumerate(vals):
            for path_b, hash_b in vals[i + 1:]:
                distance = (hash_a ^ hash_b).bit_count()
                if distance <= 2:
                    near_pairs.append({"label": label, "path_a": path_a, "path_b": path_b,
                                       "dhash_distance": distance})
    frame.to_csv(MANIFEST, index=False)
    counts = frame.groupby("label").size().to_dict()
    audit = {
        "dataset": "BDWaste v1", "doi": "10.17632/96g5pgfnfw.1", "license": "CC BY 4.0",
        "classes_audited": list(CLASS_MAP.values()), "valid_images_by_class": counts,
        "valid_images_total": len(frame), "corrupt_images": corrupt,
        "exact_duplicate_paths": exact_duplicates.path.tolist(),
        "near_duplicate_pairs_dhash_le_2": near_pairs,
        "per_image_capture_ids": False,
        "per_image_exif": {"images_with_exif": int((frame.exif_entry_count > 0).sum()),
                            "images_with_datetime": int(frame.exif_datetime_original.ne("").sum()),
                            "images_with_device_model": int(frame.exif_device_model.ne("").sum()),
                            "device_model_counts": frame.loc[frame.exif_device_model.ne(""), "exif_device_model"].value_counts().to_dict()},
        "split": "none; images remain unassigned until object/session grouping is audited",
        "license_and_provenance": "Mendeley Data record CC BY 4.0; source article says photos primarily captured by researchers in Dhaka and consent obtained for waste images.",
        "label_caveat": "Folder labels indicate waste type but visually audit sample/full distribution before training. Dataset publication reports differing totals (2,497 article raw vs 2,624/2,625 repository metadata).",
    }
    AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    create_contact_sheet(frame)
    return frame, audit


def create_contact_sheet(frame: pd.DataFrame, seed: int = 42) -> None:
    labels = list(CLASS_MAP.values())
    cell_w, cell_h, caption_h = 220, 190, 32
    sheet = Image.new("RGB", (cell_w * 6, (cell_h + caption_h) * len(labels)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    rng = random.Random(seed)
    for row_idx, label in enumerate(labels):
        subset = frame[frame.label == label]
        chosen = rng.sample(list(subset.path), min(6, len(subset)))
        y0 = row_idx * (cell_h + caption_h)
        draw.text((2, y0 + 2), label, fill="black", font=font)
        for col_idx, path in enumerate(chosen):
            with Image.open(path) as source:
                thumb = source.convert("RGB")
                thumb.thumbnail((cell_w - 8, cell_h - 14))
                x = col_idx * cell_w + (cell_w - thumb.width) // 2
                y = y0 + caption_h + (cell_h - thumb.height) // 2
                sheet.paste(thumb, (x, y))
            draw.text((col_idx * cell_w + 4, y0 + caption_h + cell_h - 14),
                      Path(path).name, fill="black", font=font)
    CONTACT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT, quality=90)


if __name__ == "__main__":
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    frame, audit = extract_and_audit()
    print(frame.groupby("label").size().to_string())
    print(json.dumps(audit["per_image_exif"], indent=2))
    print("corrupt", len(audit["corrupt_images"]), "exact duplicate paths", len(audit["exact_duplicate_paths"]),
          "near pairs <=2", len(audit["near_duplicate_pairs_dhash_le_2"]))
