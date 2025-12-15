import math
import sys
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
# Image metadata (source)
# -----------------------------
WIDTH = 56665
HEIGHT = 39292
TILE_SIZE = 512

# -----------------------------
# Scale factor
# -----------------------------
SCALE = 0.2   # 1/8 linear scale

# -----------------------------
# IIIF source
# -----------------------------
BASE_URL = "https://ms01.nasjonalmuseet.no/iip/"
IDENTIFIER = "/tif/NG.M.00258 GP.tif"

# -----------------------------
# Tile grid (source space)
# -----------------------------
tiles_x = math.ceil(WIDTH / TILE_SIZE)
tiles_y = math.ceil(HEIGHT / TILE_SIZE)

# -----------------------------
# Scaled tile size (integer grid)
# -----------------------------
SCALED_TILE = round(TILE_SIZE * SCALE)

# -----------------------------
# Output dimensions (grid-aligned)
# -----------------------------
OUT_W = SCALED_TILE * tiles_x
OUT_H = SCALED_TILE * tiles_y

print(f"Creating {OUT_W} × {OUT_H} JPG (gap-free)")

# -----------------------------
# Create output image
# -----------------------------
img = Image.new("RGB", (OUT_W, OUT_H))

session = requests.Session()

# -----------------------------
# Download → scale → paste
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

        # -----------------------------
        # Scaled tile size (edge-safe)
        # -----------------------------
        if w == TILE_SIZE:
            sw = SCALED_TILE
        else:
            sw = OUT_W - tx * SCALED_TILE

        if h == TILE_SIZE:
            sh = SCALED_TILE
        else:
            sh = OUT_H - ty * SCALED_TILE

        tile = tile.resize((sw, sh), Image.LANCZOS)

        # -----------------------------
        # Perfect grid-aligned paste
        # -----------------------------
        px = tx * SCALED_TILE
        py = ty * SCALED_TILE

        img.paste(tile, (px, py))

# -----------------------------
# Save JPG (robust settings)
# -----------------------------
img.save(
    OUTPUT_JPG,
    format="JPEG",
    quality=90,
    subsampling=2,   # 4:2:0
    optimize=False  # REQUIRED for huge images
)

print(f"Done. JPG written to {OUTPUT_JPG}")
