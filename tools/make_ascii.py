import sys
# usage: python tools/make_ascii.py AVATAR COLS ROWS light-ink|dark-ink [--mask]
# light-ink feeds assets/ascii-art.txt (dark card), dark-ink feeds ascii-art-light.txt.
# The crop box below is tuned for the current GitHub avatar.
from PIL import Image, ImageOps, ImageFilter
src, cols, rows, mode = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rgb = Image.open(src).convert("RGB").crop((110, 25, 410, 345))
g = rgb.convert("L")
S = rgb.convert("HSV").getchannel("S")
# subject mask: saturated (skin, shirt) or dark (hair, beard); wall is pale gray
mask = Image.eval(Image.merge("RGB", (g, S, g)).convert("L"), lambda v: 0)
px = mask.load(); gp = g.load(); sp = S.load()
for y in range(g.height):
    for x in range(g.width):
        px[x, y] = 255 if (sp[x, y] > 55 or gp[x, y] < 95) else 0
mask = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
if "--mask" in sys.argv:
    m = mask.resize((cols, rows))
    for y in range(rows): print("".join("#" if m.getpixel((x, y)) > 127 else "." for x in range(cols)))
    sys.exit()
eq = ImageOps.autocontrast(g, cutoff=1).filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=2))
d = eq.resize((cols, rows), Image.LANCZOS); m = mask.resize((cols, rows), Image.LANCZOS)
ramp = " .:-=+*#%@"
for y in range(rows):
    s = ""
    for x in range(cols):
        if m.getpixel((x, y)) < 128: s += " "; continue
        v = d.getpixel((x, y)) / 255
        dens = v if mode == "light-ink" else 1 - v
        s += ramp[max(1, min(9, int(dens * 10)))]
    print(s.rstrip())
