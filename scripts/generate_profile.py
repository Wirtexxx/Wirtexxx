#!/usr/bin/env python3
"""Generate the profile README and its SVG widgets.

GitHub strips CSS from READMEs, so every block is an SVG image. Text is converted
to outlines, because an SVG loaded through <img> cannot use web fonts.

Needs GH_TOKEN. A token of the account owner also counts private contributions.
"""
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

LOGIN = "Wirtexxx"
CONTACT_URL = "https://www.linkedin.com/in/vlad-haidaichuk/"

QUESTS = [
    ("plugin-sorter", "Swift",
     "macOS plugin manager for music producers: sorts VST3 and VST, tests VST3, VST, AU and CLAP, removes duplicates."),
    ("auction-simulator", "TypeScript",
     "Multi-round auction backend: bids, frozen balances, winner settlement, recovery after restart."),
    ("openstorm", "Python",
     "One CLI to run MongoDB, PostgreSQL and ClickHouse through Docker, in dev and production."),
]
INVENTORY = [
    ("#a3485e", ["TypeScript", "Python", "Swift"]),
    ("#4f8f8b", ["FastAPI", "Express", "GraphQL"]),
    ("#4a3a55", ["MongoDB", "PostgreSQL", "Redis", "Docker"]),
]
# Colors belong to the language, not its rank. Anything else folds into Other.
LANGUAGES = {"TypeScript": "#d0607f", "Swift": "#4a94e0", "Shell": "#b08a20"}
OTHER_COLOR = "#a56be0"
HEAT_RAMP = ["#241c2c", "#4a2f4f", "#7a3f6a", "#b4557f", "#e58aa6"]

PAGE = "#0d1117"  # GitHub dark background: panels vanish there, and stay dark in light mode
INK, INK2, INK3 = "#efe8f2", "#d9cfe0", "#9b8fa4"
LINE = "#6d5879"
THEMES = {
    "dark": {"ink": "#e5e0e8", "label": "#d9cfe0", "rule": "#6d5879", "a": "#d0708a", "b": "#b45fb4"},
    "light": {"ink": "#2a2030", "label": "#3a2e44", "rule": "#8d7a99", "a": "#b0405f", "b": "#8a3f9a"},
}

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


class Face:
    def __init__(self, filename):
        self.font = TTFont(ASSETS / "fonts" / filename)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upem = self.font["head"].unitsPerEm
        self.hmtx = self.font["hmtx"]

    def advance(self, ch):
        return self.hmtx[self.cmap[ord(ch)]][0]

    def width(self, s, size, spacing=0.0):
        return sum(self.advance(c) for c in s) * size / self.upem + spacing * (len(s) - 1)


CINZEL = Face("Cinzel-Bold.ttf")
PIXEL = Face("PixelifySans-Regular.ttf")
PLEX = Face("IBMPlexSans-Regular.ttf")


def num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def text(s, face, size, x, y, fill, anchor="start", spacing=0.0):
    if anchor == "middle":
        x -= face.width(s, size, spacing) / 2
    elif anchor == "end":
        x -= face.width(s, size, spacing)
    scale = size / face.upem
    pen = SVGPathPen(face.glyphs, ntos=num)
    for ch in s:
        face.glyphs[face.cmap[ord(ch)]].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += face.advance(ch) * scale + spacing
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>'


def wrap(s, face, size, limit):
    lines, line = [], ""
    for word in s.split():
        trial = f"{line} {word}".strip()
        if face.width(trial, size) > limit and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def svg(name, w, h, label, body, defs=""):
    (ASSETS / name).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{label}"><title>{label}</title><defs>{defs}</defs>{body}</svg>\n',
        encoding="utf-8",
    )


def panel(w, h):
    return f'<rect width="{w}" height="{h}" rx="6" fill="{PAGE}"/>'


CARD_FILL = ('<linearGradient id="card" x1="0" y1="0" x2="1" y2="1">'
             '<stop offset="0" stop-color="#241c2c"/><stop offset="1" stop-color="#17131d"/></linearGradient>')


def diamond(cx, cy, r, fill):
    return f'<path fill="{fill}" d="M{cx} {cy - r}L{cx + r} {cy}L{cx} {cy + r}L{cx - r} {cy}Z"/>'


def title_svg(theme):
    t = THEMES[theme]
    size, spacing = 27, 0.8
    parts = [("BACKEND SENTINEL ", t["ink"]), ("· ", t["rule"]), ("ARCHITECT", "url(#arch)"), (" OF THE VOID", t["ink"])]
    x = (840 - CINZEL.width("".join(p for p, _ in parts), size, spacing)) / 2
    body = ""
    for s, fill in parts:
        body += text(s, CINZEL, size, x, 38, fill, spacing=spacing)
        x += CINZEL.width(s, size, spacing) + spacing
    defs = (f'<linearGradient id="arch" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["a"]}"/>'
            f'<stop offset="1" stop-color="{t["b"]}"/></linearGradient>')
    svg(f"title-{theme}.svg", 840, 56, "Backend Sentinel, Architect of the Void", body, defs)


def divider_svg(slug, label, theme):
    t = THEMES[theme]
    size, spacing = 16, 2.4
    half = CINZEL.width(label, size, spacing) / 2
    left, right = 420 - half - 30, 420 + half + 30
    defs = (f'<linearGradient id="l"><stop offset="0" stop-color="{t["rule"]}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{t["rule"]}"/></linearGradient>'
            f'<linearGradient id="r"><stop offset="0" stop-color="{t["rule"]}"/>'
            f'<stop offset="1" stop-color="{t["rule"]}" stop-opacity="0"/></linearGradient>')
    body = (f'<rect y="19" width="{num(left - 10)}" height="1" fill="url(#l)"/>'
            f'<rect x="{num(right + 10)}" y="19" width="{num(830 - right)}" height="1" fill="url(#r)"/>'
            + diamond(left + 2, 19.5, 5.5, "#c0607f") + diamond(right - 2, 19.5, 5.5, "#c0607f")
            + text(label, CINZEL, size, 420, 25, t["label"], "middle", spacing))
    svg(f"divider-{slug}-{theme}.svg", 840, 40, label.title(), body, defs)


def stats_svg(stats):
    tiles = [
        (str(stats["contributions"]), "contributions", "past 12 months"),
        (str(stats["active_days"]), "active days", "past 12 months"),
        (str(stats["repos"]), "public repos", f"since {stats['since']}"),
        (stats["forging"], "now forging", f"last push {stats['forging_date']}"),
    ]
    w, h, gap = 201, 104, 12
    body = panel(840, h)
    for i, (value, label, note) in enumerate(tiles):
        x = i * (w + gap)
        cx = x + w / 2
        size = 34
        while CINZEL.width(value, size) > w - 24:
            size -= 1
        body += f'<rect x="{x + 0.5}" y="0.5" width="{w - 1}" height="{h - 1}" fill="url(#card)" stroke="{LINE}"/>'
        body += text(value, CINZEL, size, cx, 44, INK, "middle")
        body += text(label, PIXEL, 16, cx, 70, INK2, "middle")
        body += text(note, PLEX, 12, cx, 90, INK3, "middle")
    svg("stats.svg", 840, h, f"{stats['contributions']} contributions and {stats['active_days']} active days in the past 12 months, "
        f"{stats['repos']} public repos, now forging {stats['forging']}", body, CARD_FILL)


def languages_svg(langs):
    total = sum(langs.values())
    rows = [(n, langs.get(n, 0), c) for n, c in LANGUAGES.items()]
    rows.append(("Other", total - sum(r[1] for r in rows), OTHER_COLOR))
    rows = [r for r in rows if r[1] > 0]
    body = panel(840, 76) + text("Languages by code size", PIXEL, 14, 10, 16, "#b5a9bd")
    x = 10.0
    for _, size, color in rows:
        width = 820 * size / total
        body += f'<rect x="{num(x)}" y="25" width="{num(max(width - 2, 3))}" height="12" rx="2" fill="{color}"/>'
        x += width
    x = 10.0
    for name, size, color in rows:
        pct = f"{size * 100 / total:.1f}%"
        body += f'<rect x="{num(x)}" y="52" width="10" height="10" rx="2" fill="{color}"/>'
        body += text(name, PLEX, 13, x + 16, 62, INK2)
        x += 16 + PLEX.width(name, 13) + 6
        body += text(pct, PLEX, 13, x, 62, INK3)
        x += PLEX.width(pct, 13) + 22
    label = ", ".join(f"{n} {s * 100 / total:.1f}%" for n, s, _ in rows)
    svg("languages.svg", 840, 76, f"Languages by code size: {label}", body)


def heat_level(n):
    return 0 if n == 0 else 1 if n <= 2 else 2 if n <= 6 else 3 if n <= 15 else 4


def chronicle_svg(weeks):
    x0, y0, step, cell = 22, 20, 15, 12
    body, last_month = panel(840, 150), None
    for wi, week in enumerate(weeks):
        x = x0 + wi * step
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month and wi < len(weeks) - 2:
            body += text(first.strftime("%b"), PIXEL, 12, x, 12, "#b5a9bd")
            last_month = first.month
        for day in week["contributionDays"]:
            color = HEAT_RAMP[heat_level(day["contributionCount"])]
            y = y0 + day["weekday"] * step
            body += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color}"/>'
    x = 817 - PIXEL.width("More", 12) - len(HEAT_RAMP) * 15 - 8
    body += text("Less", PIXEL, 12, x - 6, 144, INK3, "end")
    for i, color in enumerate(HEAT_RAMP):
        body += f'<rect x="{x + i * 15}" y="134" width="11" height="11" rx="2" fill="{color}"/>'
    body += text("More", PIXEL, 12, 817, 144, INK3, "end")
    svg("chronicle.svg", 840, 150, "Contribution calendar for the past year", body)


def quest_svg(name, language, description):
    w, h = 272, 176
    body = (panel(w, h)
            + f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" fill="none" stroke="#2c2433"/>'
            + f'<rect x="5.5" y="5.5" width="{w - 11}" height="{h - 11}" fill="url(#card)" stroke="{LINE}"/>')
    for cx in (6, w - 6):
        body += diamond(cx, 6, 4.5, "#c9b6d3")
    body += text(name, CINZEL, 17, 20, 36, INK)
    for i, line in enumerate(wrap(description, PLEX, 13.5, w - 40)):
        body += text(line, PLEX, 13.5, 20, 60 + i * 20, "#b5a9bd")
    body += text(language, PIXEL, 15, 20, h - 22, "#8fd0c8")
    svg(f"quest-{name}.svg", w, h, f"{name}, {language}: {description}", body, CARD_FILL)


def inventory_svg():
    size, pad, gap, row_h, limit = 15, 15, 10, 44, 820
    items = [(n, c) for c, names in INVENTORY for n in names]
    rows, row, used = [], [], 0.0
    for name, color in items:
        w = PIXEL.width(name, size) + pad * 2
        if used + w > limit and row:
            rows.append((row, used - gap))
            row, used = [], 0.0
        row.append((name, color, w))
        used += w + gap
    rows.append((row, used - gap))
    h = len(rows) * row_h
    body = panel(840, h)
    for ri, (row, width) in enumerate(rows):
        x = (840 - width) / 2
        y = ri * row_h + 2
        for name, color, w in row:
            body += f'<rect x="{num(x)}" y="{y}" width="{num(w)}" height="35" fill="#1c1623" stroke="{color}" stroke-width="2"/>'
            body += text(name, PIXEL, size, x + w / 2, y + 23, "#e6dfe8", "middle")
            x += w + gap
    svg("inventory.svg", 840, h, "Stack: " + ", ".join(n for n, _ in items), body)


def button_svg():
    w, h = 280, 62
    label = "Get in touch"
    tw = PLEX.width(label, 17)
    x = (w - tw - 20) / 2
    ax = x + tw + 9
    body = (panel(w, h)
            + f'<rect x="4.5" y="4.5" width="{w - 9}" height="{h - 9}" fill="none" stroke="#4a3a55"/>'
            + f'<rect x="8.5" y="8.5" width="{w - 17}" height="{h - 17}" fill="#2c2233" stroke="#b9a6c9"/>')
    for cx, cy in ((5, 5), (w - 5, 5), (5, h - 5), (w - 5, h - 5)):
        body += diamond(cx, cy, 4, "#c9b6d3")
    body += text(label, PLEX, 17, x, 37, INK)
    body += (f'<path fill="none" stroke="{INK}" stroke-width="1.6" '
             f'd="M{num(ax)} 37L{num(ax + 10)} 27M{num(ax + 2)} 27H{num(ax + 10)}V35"/>')
    svg("button.svg", w, h, "Get in touch", body)


def fetch():
    query = """query($login:String!){user(login:$login){createdAt
      contributionsCollection{contributionCalendar{weeks{contributionDays{date weekday contributionCount}}}}
      repositories(first:100,ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC){totalCount nodes{name pushedAt
        languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "User-Agent": "profile-widgets"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if "errors" in payload:
        raise SystemExit(f"GitHub API error: {payload['errors']}")
    return payload["data"]["user"]


def summarize(user):
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    cutoff = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    days = [d for w in weeks for d in w["contributionDays"] if d["date"] > cutoff]
    repos = user["repositories"]["nodes"]
    # This repo is skipped: the daily widget commit would always make it the latest.
    latest = max((r for r in repos if r["name"] != LOGIN), key=lambda r: r["pushedAt"])
    pushed = dt.date.fromisoformat(latest["pushedAt"][:10])
    langs = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            langs[edge["node"]["name"]] = langs.get(edge["node"]["name"], 0) + edge["size"]
    stats = {
        "contributions": sum(d["contributionCount"] for d in days),
        "active_days": sum(1 for d in days if d["contributionCount"]),
        "repos": user["repositories"]["totalCount"],
        "since": user["createdAt"][:4],
        "forging": latest["name"],
        "forging_date": f"{pushed.strftime('%b')} {pushed.day}, {pushed.year}",
    }
    return stats, langs, weeks


def picture(stem, alt):
    return (f'<picture><source media="(prefers-color-scheme: light)" srcset="assets/{stem}-light.svg">'
            f'<img src="assets/{stem}-dark.svg" alt="{alt}" width="100%"></picture>')


def readme(stats):
    quests = "\n".join(
        f'  <a href="https://github.com/{LOGIN}/{n}"><img src="assets/quest-{n}.svg" alt="{n}: {d}" width="32%"></a>'
        for n, _, d in QUESTS
    )
    button = f'<a href="{CONTACT_URL}"><img src="assets/button.svg" alt="Get in touch" width="280"></a>'
    stack = ", ".join(n for _, names in INVENTORY for n in names)
    (ROOT / "README.md").write_text(f"""<div align="center">

{picture("title", "Backend Sentinel, Architect of the Void")}

{picture("divider-sheet", "Character Sheet")}

<img src="assets/stats.svg" alt="{stats['contributions']} contributions and {stats['active_days']} active days in the past 12 months, {stats['repos']} public repos" width="100%">

<img src="assets/languages.svg" alt="Languages by code size" width="100%">

{picture("divider-chronicle", "Chronicle")}

<img src="assets/chronicle.svg" alt="Contribution calendar for the past year" width="100%">

{picture("divider-quests", "Quest Log")}

<p>
{quests}
</p>

{picture("divider-inventory", "Inventory")}

<img src="assets/inventory.svg" alt="Stack: {stack}" width="100%">

<br><br>

{button}

</div>
""", encoding="utf-8")


def main():
    stats, langs, weeks = summarize(fetch())
    for theme in THEMES:
        title_svg(theme)
        for slug, label in (("sheet", "CHARACTER SHEET"), ("chronicle", "CHRONICLE"),
                            ("quests", "QUEST LOG"), ("inventory", "INVENTORY")):
            divider_svg(slug, label, theme)
    stats_svg(stats)
    languages_svg(langs)
    chronicle_svg(weeks)
    for quest in QUESTS:
        quest_svg(*quest)
    inventory_svg()
    button_svg()
    readme(stats)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
