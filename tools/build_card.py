"""Render the neofetch-style profile card (dark_mode.svg, light_mode.svg).

Inputs: assets/ascii-art.txt (dark card), assets/ascii-art-light.txt (light
card) and cache/stats.json from fetch_stats.py. Edit PROFILE below to change
what the card says. Every info line is padded to WIDTH characters with dot
leaders, so the right column stays aligned in any monospace font.
"""

import calendar
import datetime as dt
import json
import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIDTH = 58

TITLE = "shawn@nichols"
PROFILE = [
    ("OS", "Arch Linux (Omarchy)"),
    ("Uptime", "{uptime}"),
    ("Host", "nicholsai.com"),
    ("Kernel", "Independent Research Engineer"),
    ("IDE", "Claude Code, Codex, alts"),
    None,
    ("Languages.Code", "Go, Rust, Python, C++, TypeScript"),
    ("Languages.Computer", "Bash, SQL, YAML, HTML"),
    ("Languages.Real", "English"),
    None,
    ("Focus.Agents", "Harnesses, Verification, MCP"),
    ("Focus.Evals", "Benchmarks, Trajectories, Replay"),
    ("Focus.Inference", "Local open-weight models, NIM"),
    ("Background", "Walmart cold chain, Mercedes JIT"),
]
CONTACT = [
    ("Email", "shawn5cents@gmail.com"),
    ("LinkedIn", "shawn5cents"),
    ("Web", "nicholsai.com"),
]

# Shared with build_links.py so the buttons match the card.
THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "key": "#e3b341",
             "value": "#79c0ff", "dots": "#484f58", "add": "#3fb950", "del": "#f85149"},
    "light": {"bg": "#f6f8fa", "border": "#d0d7de", "text": "#24292f", "key": "#9a6700",
              "value": "#0550ae", "dots": "#8c959f", "add": "#1a7f37", "del": "#cf222e"},
}
FONT = "Consolas,'DejaVu Sans Mono',Menlo,'Liberation Mono',monospace"


def uptime(created_at):
    start = dt.date.fromisoformat(created_at[:10])
    today = dt.date.today()
    months = (today.year - start.year) * 12 + today.month - start.month
    if today.day < start.day:
        months -= 1
    ay, am = start.year + (start.month - 1 + months) // 12, (start.month - 1 + months) % 12 + 1
    days = (today - dt.date(ay, am, min(start.day, calendar.monthrange(ay, am)[1]))).days
    y, m = divmod(months, 12)
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural(days, 'day')}"


def field(key, value, width=WIDTH):
    """Return [(class, text), ...] for '. key: ..... value' padded to width."""
    head = f". {key}:"
    gap = width - len(head) - len(value) - 2
    if gap < 1:
        raise ValueError(f"line too long for card: {key}: {value}")
    return [("cc", ". "), ("key", f"{key}:"), ("cc", " " + "." * gap + " "), ("value", value)]


def header(label, width=WIDTH):
    text = f"- {label} -"
    return [("key", text), ("cc", "—" * (width - len(text) - 1) + "-")]


def stat_pair(k1, v1, k2, v2, right_width=20):
    left = field(k1, v1, WIDTH - right_width - 3)
    right = field(k2, v2, right_width + 2)[1:]  # drop the leading '. '
    return left + [("cc", " | ")] + right


def lines(stats):
    out = [[("title", TITLE), ("cc", " -" + "—" * (WIDTH - len(TITLE) - 3) + "-")]]
    for item in PROFILE:
        if item is None:
            out.append([("cc", ".")])
        else:
            out.append(field(item[0], item[1].format(uptime=uptime(stats["created_at"]))))
    out.append([("cc", ".")])
    out.append(header("Contact"))
    out += [field(k, v) for k, v in CONTACT]
    out.append([("cc", ".")])
    out.append(header("GitHub Stats"))
    n = lambda x: f"{x:,}"
    out.append(stat_pair("Repos", f"{n(stats['repos'])} {{Contributed: {n(stats['contributed'])}}}",
                         "Stars", n(stats["stars"])))
    out.append(stat_pair("Commits", n(stats["commits"]), "Followers", n(stats["followers"])))
    loc = stats["loc_add"] - stats["loc_del"]
    head = ". Lines of Code:"
    tail = [("value", n(loc)), ("cc", " ( "), ("add", f"{n(stats['loc_add'])}++"), ("cc", ", "),
            ("del", f"{n(stats['loc_del'])}--"), ("cc", " )")]
    tail_len = sum(len(t) for _, t in tail)
    out.append([("cc", ". "), ("key", "Lines of Code:"),
                ("cc", " " + "." * max(1, WIDTH - len(head) - tail_len - 2) + " ")] + tail)
    return out


def render(theme, art_path, stats):
    c = THEMES[theme]
    art = art_path.read_text().rstrip("\n").split("\n")
    info = lines(stats)
    lh, top = 20, 34
    height = max(top + lh * (len(info) + 1), 30 + 12.8 * len(art)) + 20
    art_top = (height - 12.8 * len(art)) / 2 + 9
    w = 1018
    svg = [f"<?xml version='1.0' encoding='UTF-8'?>",
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}px" height="{height:.0f}px" '
           f'viewBox="0 0 {w} {height:.0f}" font-family="{FONT}">',
           "<style>",
           f".key{{fill:{c['key']}}} .value{{fill:{c['value']}}} .cc{{fill:{c['dots']}}}",
           f".title{{fill:{c['key']};font-weight:bold}} .add{{fill:{c['add']}}} .del{{fill:{c['del']}}}",
           "text,tspan{white-space:pre}",
           "</style>",
           f'<rect x="0.5" y="0.5" width="{w - 1}" height="{height - 1:.0f}" rx="12" '
           f'fill="{c["bg"]}" stroke="{c["border"]}"/>',
           f'<text fill="{c["text"]}" font-size="11.5px" xml:space="preserve">']
    for i, row in enumerate(art):
        svg.append(f'<tspan x="18" y="{art_top + i * 12.8:.2f}">{escape(row)}</tspan>')
    svg.append("</text>")
    svg.append(f'<text fill="{c["text"]}" font-size="16px" xml:space="preserve">')
    for i, row in enumerate(info):
        parts = "".join(f'<tspan class="{cls}">{escape(t)}</tspan>' for cls, t in row)
        svg.append(f'<tspan x="440" y="{top + i * lh}">{parts}</tspan>')
    y = top + len(info) * lh
    svg.append(f'<tspan x="440" y="{y}" class="key">&gt; </tspan>'
               f'<tspan fill="{c["text"]}">█<animate attributeName="opacity" values="1;1;0;0" '
               f'keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></tspan>')
    svg.append("</text></svg>")
    return "\n".join(svg) + "\n"


def main():
    stats = json.loads((ROOT / "cache" / "stats.json").read_text())
    (ROOT / "dark_mode.svg").write_text(render("dark", ROOT / "assets" / "ascii-art.txt", stats))
    (ROOT / "light_mode.svg").write_text(render("light", ROOT / "assets" / "ascii-art-light.txt", stats))


if __name__ == "__main__":
    main()
