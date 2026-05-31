#!/usr/bin/env python3
"""
Commit Odyssey — GitHub Contribution Graph Generator
Fetches real contribution data and renders a pixel-art space-themed SVG.
"""

import json
import os
import sys
import math
import random
import datetime
import urllib.request
import urllib.error

USERNAME = os.environ.get("GH_USERNAME", "VThuongg")
TOKEN = os.environ.get("GH_TOKEN", "")
OUTPUT = os.environ.get("OUTPUT_PATH", "assets/contribution-odyssey.svg")

COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BORDERS = ["#30363d", "#0e4429", "#006d32", "#26a641", "#39d353"]

CELL = 11
GAP = 3
STEP = CELL + GAP
DAY_LABEL_W = 30
MARGIN_TOP = 32
MARGIN_LEFT = 10
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 40

SPRITES = [
    {"level_min": 4, "icon": "🚀", "label": "Launch!"},
    {"level_min": 4, "icon": "⭐", "label": "Star burst"},
    {"level_min": 3, "icon": "🛸", "label": "Big PR"},
    {"level_min": 4, "icon": "☄️", "label": "Hotfix!"},
    {"level_min": 3, "icon": "🪐", "label": "Feature orbit"},
    {"level_min": 4, "icon": "🌙", "label": "Midnight push"},
    {"level_min": 3, "icon": "🧬", "label": "Bio-ML"},
]

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""

LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_contributions():
    now = datetime.datetime.utcnow()
    to_dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    from_dt = (now - datetime.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = json.dumps({
        "query": QUERY,
        "variables": {"login": USERNAME, "from": from_dt, "to": to_dt}
    }).encode()

    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            weeks = cal["weeks"]
            total = cal["totalContributions"]

            grid = []
            for week in weeks:
                days = week["contributionDays"]
                week_data = []
                for day in days:
                    week_data.append({
                        "date": day["date"],
                        "count": day["contributionCount"],
                        "level": LEVEL_MAP.get(day["contributionLevel"], 0),
                    })
                grid.append(week_data)

            return grid, total
    except Exception as e:
        print(f"[warn] GitHub API failed: {e}, using mock data", file=sys.stderr)
        return generate_mock_data()


def generate_mock_data():
    grid = []
    base = datetime.date.today() - datetime.timedelta(days=364)
    for w in range(53):
        week = []
        for d in range(7):
            dt = base + datetime.timedelta(weeks=w, days=d)
            seed = (w * 31 + d * 7) % 100
            if seed < 28:
                lv = 0
            elif seed < 48:
                lv = 1
            elif seed < 68:
                lv = 2
            elif seed < 84:
                lv = 3
            else:
                lv = 4
            count = [0, 1, 3, 6, 10][lv]
            week.append({"date": str(dt), "count": count, "level": lv})
        grid.append(week)
    return grid, sum(d["count"] for w in grid for d in w)


def pick_sprites(grid):
    chosen = {}
    sprite_idx = 0
    rng = random.Random(42)
    for wi, week in enumerate(grid):
        for di, day in enumerate(week):
            if sprite_idx >= len(SPRITES):
                break
            sp = SPRITES[sprite_idx]
            if day["level"] >= sp["level_min"] and rng.random() < 0.15:
                chosen[(wi, di)] = sp
                sprite_idx += 1
    return chosen


def build_month_labels(grid):
    labels = []
    prev_month = None
    for wi, week in enumerate(grid):
        if not week:
            continue
        month = week[0]["date"][5:7]
        if month != prev_month:
            month_name = datetime.date(2000, int(month), 1).strftime("%b")
            labels.append((wi, month_name))
            prev_month = month
    return labels


def render_svg(grid, total, sprites):
    num_weeks = len(grid)
    max_days = 7

    W = MARGIN_LEFT + DAY_LABEL_W + num_weeks * STEP + MARGIN_RIGHT
    H = MARGIN_TOP + max_days * STEP + MARGIN_BOTTOM + 28

    month_labels = build_month_labels(grid)

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

    lines.append("""
<defs>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&amp;display=swap');
    .px { font-family: 'Press Start 2P', monospace; }
  </style>
</defs>""")

    # Background
    lines.append(f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117"/>')

    # Stars background
    rng2 = random.Random(99)
    for _ in range(60):
        sx = rng2.randint(5, W - 5)
        sy = rng2.randint(5, H - 20)
        op = rng2.uniform(0.2, 0.6)
        lines.append(f'<circle cx="{sx}" cy="{sy}" r="0.8" fill="white" opacity="{op:.2f}"/>')

    # Title
    lines.append(f'<text x="{MARGIN_LEFT + DAY_LABEL_W}" y="16" class="px" font-size="7" fill="#484f58">✦ COMMIT ODYSSEY — {total} CONTRIBUTIONS ✦</text>')

    # Month labels
    for wi, mname in month_labels:
        x = MARGIN_LEFT + DAY_LABEL_W + wi * STEP
        lines.append(f'<text x="{x}" y="{MARGIN_TOP - 4}" class="px" font-size="6" fill="#484f58">{mname}</text>')

    # Day labels
    day_names = ["", "Mon", "", "Wed", "", "Fri", ""]
    for di, dname in enumerate(day_names):
        if dname:
            y = MARGIN_TOP + di * STEP + CELL - 1
            lines.append(f'<text x="{MARGIN_LEFT}" y="{y}" class="px" font-size="6" fill="#484f58">{dname}</text>')

    # Cells
    for wi, week in enumerate(grid):
        for di, day in enumerate(week):
            lv = day["level"]
            cx = MARGIN_LEFT + DAY_LABEL_W + wi * STEP
            cy = MARGIN_TOP + di * STEP
            fill = COLORS[lv]
            stroke = BORDERS[lv]
            lines.append(f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="0.5"/>')

            sp = sprites.get((wi, di))
            if sp:
                fx = cx - 1
                fy = cy + 12
                lines.append(f'<text x="{fx}" y="{fy}" font-size="13" dominant-baseline="auto">{sp["icon"]}</text>')

    # Legend
    legend_labels = ["Less", "More"]
    lx = W - MARGIN_RIGHT - 5 * STEP - 2 * 30 - 10
    ly = H - MARGIN_BOTTOM + 16
    lines.append(f'<text x="{lx}" y="{ly + 9}" class="px" font-size="7" fill="#484f58">Less</text>')
    lx += 34
    for i, (c, b) in enumerate(zip(COLORS, BORDERS)):
        lines.append(f'<rect x="{lx + i*STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2" fill="{c}" stroke="{b}" stroke-width="0.5"/>')
    lx += 5 * STEP + 4
    lines.append(f'<text x="{lx}" y="{ly + 9}" class="px" font-size="7" fill="#484f58">More</text>')

    # Sprite legend
    unique_sprites = list({sp["icon"]: sp for sp in sprites.values()}.values())
    if unique_sprites:
        lx2 = MARGIN_LEFT + DAY_LABEL_W
        ly2 = H - MARGIN_BOTTOM + 16
        for sp in unique_sprites[:6]:
            lines.append(f'<text x="{lx2}" y="{ly2 + 10}" font-size="11">{sp["icon"]}</text>')
            lines.append(f'<text x="{lx2 + 14}" y="{ly2 + 10}" class="px" font-size="6" fill="#484f58">{sp["label"]}</text>')
            lx2 += 90

    lines.append('</svg>')
    return "\n".join(lines)


def main():
    os.makedirs(os.path.dirname(OUTPUT) if os.path.dirname(OUTPUT) else ".", exist_ok=True)
    print(f"[info] Fetching contributions for @{USERNAME}...")
    grid, total = fetch_contributions()
    print(f"[info] Got {len(grid)} weeks, {total} total contributions")
    sprites = pick_sprites(grid)
    print(f"[info] Placed {len(sprites)} sprites")
    svg = render_svg(grid, total, sprites)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[done] Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
