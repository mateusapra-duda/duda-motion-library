"""Compare a Rive capture with the Figma 3x export: side-by-side, 50% onion skin and a diff heatmap.

usage: python overlay.py <rive.png> <figma_export@3x.png> <out.jpg>
"""
import sys

import numpy as np
from PIL import Image, ImageChops

a = Image.open(sys.argv[1]).convert("RGB")
b = Image.open(sys.argv[2]).convert("RGB").resize(a.size, Image.LANCZOS)
onion = Image.blend(a, b, 0.5)
diff = ImageChops.difference(a, b).convert("L").point(lambda v: min(255, v * 3))
heat = Image.merge("RGB", (diff, Image.new("L", a.size, 0), Image.new("L", a.size, 0)))
w, h = a.size
sheet = Image.new("RGB", (w * 2, h * 2), "white")
sheet.paste(a, (0, 0)); sheet.paste(b, (w, 0)); sheet.paste(onion, (0, h)); sheet.paste(heat, (w, h))
sheet.resize((w, h)).save(sys.argv[3], quality=88)
d = np.asarray(ImageChops.difference(a, b).convert("L"), dtype=float)
print(f"mean abs diff {d.mean():.2f} / 255, pixels >40: {(d > 40).mean() * 100:.1f}%")
