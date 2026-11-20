from __future__ import annotations

import hashlib
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DATASET_ID = "96g5pgfnfw"
VERSION = "1"
BASE = f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}"
OUT = Path("data/raw/downloads/bdwaste-v1")
CLASSES = {
    "Banana peel.zip": "8880fac7-1667-4455-afec-1c1aadb64ae1",
    "Potato Peel.zip": "13182676-b518-4c62-92f2-9af5d4a7e410",
    "Lemon Peel.zip": "9c5ae005-2b01-4d34-879d-203d130f83ac",
    "Shell of Malta.zip": "bd51ce74-8546-4f13-bf7b-e2ad0d65d832",
    "Pastic.zip": "c0775dc6-c719-4208-90b3-9ab858112267",
    "Glass.zip": "ce2b6566-d62d-4065-9ea9-413642db7c5d",
    "Cane.zip": "7ec7a4be-f899-4dc6-925a-a954d20f96da",
    "Mango Peel.zip": "76681980-e1f2-4286-be54-9bdb3b04b056",
    " Egg shell.zip": "76357ab0-e172-4844-b686-9e4419b5c0bb",
    " Sugarcane  husk.zip": "65b77a23-6840-4d82-9c59-8347bdddd1f3",
}
LOCK = threading.Lock()


def get_json(url: str) -> dict:
    req = Request(url, headers={"Accept": "application/vnd.mendeley-public-dataset.1+json",
                                "User-Agent": "COMPOST-AI-dataset-audit/1.0"})
    with urlopen(req, timeout=60) as response:
        return json.load(response)


def download(filename: str, file_id: str) -> dict:
    item = get_json(f"{BASE}/files/{file_id}")
    detail = item["content_details"]
    target = OUT / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    offset = target.stat().st_size if target.exists() else 0
    if offset > detail["size"]:
        raise ValueError(f"Unexpected oversized partial file: {target}")
    headers = {"User-Agent": "COMPOST-AI-dataset-audit/1.0"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    req = Request(detail["download_url"], headers=headers)
    try:
        response = urlopen(req, timeout=120)
    except HTTPError as exc:
        if exc.code == 416 and offset == detail["size"]:
            response = None
        else:
            raise
    if response is not None:
        mode = "ab" if offset and response.status == 206 else "wb"
        if offset and response.status != 206:
            offset = 0
        received = offset
        with response, target.open(mode) as out:
            while block := response.read(1024 * 1024):
                out.write(block)
                received += len(block)
                if received % (32 * 1024 * 1024) < len(block):
                    with LOCK:
                        print(f"{filename}: {received}/{detail['size']} bytes", flush=True)
    hasher = hashlib.sha256()
    with target.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            hasher.update(block)
    actual_hash = hasher.hexdigest()
    if target.stat().st_size != detail["size"]:
        raise ValueError(f"Size mismatch for {filename}: {target.stat().st_size} != {detail['size']}")
    if actual_hash != detail["sha256_hash"]:
        raise ValueError(f"SHA-256 mismatch for {filename}: {actual_hash} != {detail['sha256_hash']}")
    return {"filename": filename, "file_id": file_id, "bytes": detail["size"],
            "sha256": actual_hash, "license": "CC BY 4.0", "source": item}


def main() -> None:
    records = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(download, name, fid): name for name, fid in CLASSES.items()}
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            print(f"Verified {record['filename']}: {record['bytes']} bytes SHA256={record['sha256']}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "download-audit.json").write_text(json.dumps({
        "dataset": "BDWaste v1", "doi": "10.17632/96g5pgfnfw.1", "license": "CC BY 4.0",
        "downloaded_classes": sorted(records, key=lambda x: x["filename"]),
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
