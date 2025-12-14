import math
import sys
import os
import requests
from PIL import Image
from tqdm import tqdm
from io import BytesIO

# -----------------------------
# Command-line argument
# -----------------------------
if len(sys.argv) != 2:
    print("Usage: python py.py <output_file.jpg>")
    sys.exit(1)

OUTPUT_JPG = sys.argv[1]

# -----------------------------
# Image metadata
# -----------------------------
WIDTH = 56665
HEIGHT = 39292
TILE_SIZE = 512

SCALE = 0.5  # 4× downscaled (½ width × ½ height)

OUT_W = int(WIDTH * SCALE)
OUT_H = int(HEIGHT * SCALE)

BASE_URL = "https://ms01.nasjonalmuseet.no/iip/"
IDENTIFIER = "/tif/NG.M.00258 GP.tif"

tiles_x = math.ceil(WIDTH / TILE_SIZE)
tiles_y = math.ceil(HEIGHT / TILE_SIZE)

session = requests.Session()

# -----------------------------
# Create output image
# -----------------------------
print(f"Creating {OUT_W} × {OUT_H} JPG (4× downscaled)")
img = Image.new("RGB", (OUT_W, OUT_H))

# -----------------------------
# Download, downscale, paste
# -----------------------------
for ty in tqdm(range(tiles_y), desc="Downloading tiles"):
    for tx in range(tiles_x):
        x = tx * TILE_SIZE
        y = ty * TILE_SIZE

        w = min(TILE_SIZE, WIDTH - x)
        h = min(TILE_SIZE, HEIGHT - y)

        tile_url = (
            f"{BASE_URL}?iiif={IDENTIFIER}/"
            f"{x},{y},{w},{h}/512,/0/default.jpg"
        )

        r = session.get(tile_url, timeout=30)
        r.raise_for_status()

        tile = Image.open(BytesIO(r.content)).convert("RGB")

        # Downscale tile
        sw = int(w * SCALE)
        sh = int(h * SCALE)

        if sw == 0 or sh == 0:
            continue

        tile = tile.resize((sw, sh), Image.LANCZOS)

        # Scaled paste position
        px = int(x * SCALE)
        py = int(y * SCALE)

        img.paste(tile, (px, py))

# -----------------------------
# Save JPG (memory-safe)
# -----------------------------
img.save(
    OUTPUT_JPG,
    format="JPEG",
    quality=90,
    subsampling=2,     # 4:2:0
    optimize=False     # CRITICAL
)

print(f"Done. JPG written to {OUTPUT_JPG}")
