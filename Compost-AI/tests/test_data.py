from PIL import Image
import pytest

from compost_ai.data import prepare_manifest


def test_manifest_is_stratified_and_deduplicated(tmp_path):
    source = tmp_path / "images"
    for label, color in (("paper", "white"), ("plastic", "red")):
        folder = source / label
        folder.mkdir(parents=True)
        for index in range(20):
            Image.new("RGB", (16, 16), color=color).save(folder / f"{index}.png")
    # Same bytes in a separate path are treated as a duplicate.
    duplicate = source / "paper" / "copy.png"
    (source / "paper" / "0.png").replace(duplicate)
    (source / "paper" / "0.png").write_bytes(duplicate.read_bytes())
    # Keep examples unique within a class to leave enough rows for stratification.
    for index in range(1, 20):
        Image.new("RGB", (16, 16), color=(index, 0, 0)).save(source / "paper" / f"{index}.png")
    for index in range(20):
        Image.new("RGB", (16, 16), color=(0, index, 0)).save(source / "plastic" / f"{index}.png")
    manifest = prepare_manifest(source, tmp_path / "manifest.csv")
    assert not manifest.sha256.duplicated().any()
    assert set(manifest.split) == {"train", "validation", "test"}


def test_manifest_rejects_empty_source(tmp_path):
    with pytest.raises(ValueError):
        prepare_manifest(tmp_path, tmp_path / "manifest.csv")
