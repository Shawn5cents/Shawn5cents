"""Render the link buttons (link_<name>_<theme>.svg) in the card's palette.

Each button is a terminal-style tab: a pixel-art icon, a command-ish label and
an accent underline. Icons are drawn from the small bitmaps below (one char per
pixel, '#' = filled), scaled by PX.
"""

import pathlib

from build_card import FONT, THEMES

ROOT = pathlib.Path(__file__).resolve().parent.parent
PX = 3
W, H = 340, 60

ICONS = {
    "email": [
        "#############",
        "##.........##",
        "#.#.......#.#",
        "#..#.....#..#",
        "#...#...#...#",
        "#....###....#",
        "#...........#",
        "#...........#",
        "#############",
    ],
    "linkedin": [
        "#############",
        "#.###########",
        "#############",
        "#.###.#..####",
        "#.###..##.###",
        "#.###.###.###",
        "#.###.###.###",
        "#.###.###.###",
        "#############",
    ],
    "web": [
        "##...........",
        ".##..........",
        "..##.........",
        "...##........",
        "..##.........",
        ".##..........",
        "##...#######.",
        ".............",
        ".............",
    ],
}
LABELS = {"email": "~/email", "linkedin": "~/linkedin", "web": "~/nicholsai"}


def icon_path(bitmap, ox, oy):
    d = []
    for y, row in enumerate(bitmap):
        for x, ch in enumerate(row):
            if ch == "#":
                d.append(f"M{ox + x * PX} {oy + y * PX}h{PX}v{PX}h-{PX}z")
    return "".join(d)


def render(name, theme):
    c = THEMES[theme]
    label = LABELS[name]
    bitmap = ICONS[name]
    text_w = len(label) * 10.8  # ~0.6em at 18px
    total = len(bitmap[0]) * PX + 12 + text_w
    ox = round((W - total) / 2)
    oy = round((H - len(bitmap) * PX) / 2) - 1
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}px" height="{H}px" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="8" fill="{c['bg']}" stroke="{c['border']}" stroke-width="2"/>
<rect x="12" y="{H - 6}" width="{W - 24}" height="3" fill="{c['key']}"/>
<path shape-rendering="crispEdges" fill="{c['key']}" d="{icon_path(bitmap, ox, oy)}"/>
<text x="{ox + len(bitmap[0]) * PX + 12}" y="{H / 2 + 5:.0f}" font-size="18px" fill="{c['text']}" xml:space="preserve"><tspan fill="{c['value']}">{label}</tspan></text>
</svg>
"""


def main():
    for name in ICONS:
        for theme in THEMES:
            (ROOT / f"link_{name}_{theme}.svg").write_text(render(name, theme))


if __name__ == "__main__":
    main()
