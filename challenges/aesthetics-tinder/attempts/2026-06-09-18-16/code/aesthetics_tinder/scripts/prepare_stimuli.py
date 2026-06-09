"""Download demo web images and standardize them to 500 x 500 px."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

import requests
from PIL import Image, ImageOps

LOREM_FLICKR_JSON = "https://loremflickr.com/json/700/700/{tags}/all?lock={lock}"
IMAGE_SIZE = (500, 500)
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"
MANIFEST_PATH = DATA_DIR / "stimuli_manifest.json"

IMAGE_QUERIES = {
    "clothes": {"tags": "clothes", "locks": [101, 102, 103, 104, 105]},
    "house_interiors": {"tags": "house,interior", "locks": [201, 202, 203, 204, 205]},
    "paintings": {"tags": "painting", "locks": [301, 302, 303, 304, 305]},
}


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def fetch_metadata(tags: str, lock: int) -> dict:
    source_request_url = LOREM_FLICKR_JSON.format(tags=tags, lock=lock)
    response = requests.get(
        source_request_url,
        headers={"User-Agent": "PsyNetSkills demo stimulus preparation"},
        timeout=30,
    )
    response.raise_for_status()
    metadata = response.json()
    metadata["source_request_url"] = source_request_url
    return metadata


def download_image(url: str) -> Image.Image:
    response = requests.get(
        url,
        headers={"User-Agent": "PsyNetSkills demo stimulus preparation"},
        timeout=30,
    )
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


def prepare_stimuli() -> list[dict]:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []

    for category, query in IMAGE_QUERIES.items():
        for index, lock in enumerate(query["locks"], start=1):
            stimulus_id = f"{category}_{index:02d}"
            source = fetch_metadata(query["tags"], lock)
            image = download_image(source["file"])
            standardized = ImageOps.fit(
                image,
                IMAGE_SIZE,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            image_path = IMAGE_DIR / f"{stimulus_id}.jpg"
            standardized.save(image_path, "JPEG", quality=90, optimize=True)

            manifest.append(
                {
                    "stimulus_id": stimulus_id,
                    "category": category,
                    "search_term": query["tags"],
                    "lock": lock,
                    "path": str(image_path.relative_to(ROOT)),
                    "width_px": IMAGE_SIZE[0],
                    "height_px": IMAGE_SIZE[1],
                    "source_title": f"LoremFlickr image for {query['tags']} lock {lock}",
                    "source_page": source.get("rawFileUrl") or source["file"],
                    "source_request_url": source["source_request_url"],
                    "image_url": source["file"],
                    "author": source.get("owner"),
                    "license": source.get("license"),
                    "license_url": None,
                    "original_width_px": source.get("width"),
                    "original_height_px": source.get("height"),
                }
            )

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    stimuli = prepare_stimuli()
    print(f"Wrote {len(stimuli)} stimuli to {MANIFEST_PATH}")
