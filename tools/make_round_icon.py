"""
Simple helper to create a circular PNG favicon from a source image.
Usage:
  1) Install Pillow if needed:
     python -m pip install pillow
  2) Run from project root:
     python tools/make_round_icon.py ifood_logo.jpg
  3) The script will create `ifoo_logo_round.png` in the project root which Streamlit
     will use as `page_icon` (if present).

If no argument is provided the script will try `ifood_logo.jpg` by default.
"""
from PIL import Image, ImageDraw
import sys
import os

DEFAULT_IN = "ifood_icon.jpg"
OUT = "ifood_icon_round.png"

src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IN
if not os.path.exists(src):
    print(f"Source image not found: {src}")
    sys.exit(1)

img = Image.open(src).convert("RGBA")
# Crop to square (center) then resize to 256x256 for favicon-quality
w, h = img.size
side = min(w, h)
left = (w - side) // 2
top = (h - side) // 2
img = img.crop((left, top, left + side, top + side)).resize((256, 256), Image.LANCZOS)

# Create circular mask
mask = Image.new("L", (256, 256), 0)
draw = ImageDraw.Draw(mask)
draw.ellipse((0, 0, 256, 256), fill=255)

# Apply mask and save as PNG with transparency
img.putalpha(mask)
img.save(OUT, format="PNG")
print(f"Saved rounded icon: {OUT}")
