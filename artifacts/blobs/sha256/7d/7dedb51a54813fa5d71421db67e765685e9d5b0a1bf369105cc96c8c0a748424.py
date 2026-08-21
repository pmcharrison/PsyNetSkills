"""Download Wikimedia Commons demo stimuli and standardize them to 500x500 px."""

from __future__ import annotations

import json
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static" / "stimuli"
MANIFEST_PATH = ROOT / "stimuli" / "manifest.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "PsyNetSkills-aesthetics-tinder-demo/1.0"


QUERIES = {
    "clothes": [
        "red dress clothing",
        "denim jacket clothing",
        "white sneakers footwear",
        "wool sweater clothing",
        "fedora hat clothing",
    ],
    "house_interiors": [
        "living room interior",
        "kitchen interior",
        "bedroom interior",
        "dining room interior",
        "office interior",
    ],
    "paintings": [
        "Vincent van Gogh painting",
        "Claude Monet painting",
        "Pierre-Auguste Renoir painting",
        "Wassily Kandinsky painting",
        "Rembrandt painting",
    ],
}


def fetch_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urlopen(req, timeout=60) as response:
                return response.read()
        except (HTTPError, URLError):
            if attempt == 4:
                raise
            time.sleep(2**attempt)
    raise RuntimeError(f"Failed to fetch {url}")


def metadata_value(extmetadata: dict, key: str) -> str | None:
    value = extmetadata.get(key, {})
    return value.get("value") if isinstance(value, dict) else None


def commons_file_url(title: str) -> str:
    file_name = title.removeprefix("File:").replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/File:{quote(file_name)}"


def search_commons(query: str) -> dict:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": 6,
        "gsrlimit": 12,
        "gsrsearch": query,
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": 1000,
    }
    data = fetch_json(f"{COMMONS_API}?{urlencode(params)}")
    pages = data.get("query", {}).get("pages", {})
    for page in sorted(pages.values(), key=lambda item: item.get("index", 9999)):
        info = page.get("imageinfo", [{}])[0]
        mime = info.get("mime", "")
        if not mime.startswith("image/") or mime in {"image/svg+xml", "image/gif"}:
            continue
        return {"title": page["title"], "imageinfo": info}
    raise RuntimeError(f"No suitable Commons image found for query: {query}")


def square_resize(image_bytes: bytes, output_path: Path) -> None:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((500, 500), Image.Resampling.LANCZOS)
    image.save(output_path, format="JPEG", quality=88, optimize=True)


def main() -> None:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = []

    for category, queries in QUERIES.items():
        for index, query in enumerate(queries, start=1):
            image_id = f"{category}_{index:02d}"
            filename = f"{image_id}.jpg"
            output_path = STATIC_DIR / filename
            result = search_commons(query)
            info = result["imageinfo"]
            source_image_url = info.get("thumburl") or info["url"]
            if not output_path.exists():
                square_resize(fetch_bytes(source_image_url), output_path)
            extmetadata = info.get("extmetadata", {})
            manifest.append(
                {
                    "image_id": image_id,
                    "category": category,
                    "filename": filename,
                    "source_query": query,
                    "source_title": result["title"],
                    "source_page": commons_file_url(result["title"]),
                    "source_image_url": info["url"],
                    "license": metadata_value(extmetadata, "LicenseShortName"),
                    "artist": metadata_value(extmetadata, "Artist"),
                    "credit": metadata_value(extmetadata, "Credit"),
                    "standardized_size_px": [500, 500],
                }
            )
            time.sleep(0.2)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(manifest)} stimuli to {STATIC_DIR}")
    print(f"Wrote manifest to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
