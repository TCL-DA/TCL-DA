"""Vẽ mục "02 meters" + dải footer cho profile README (phong cách teenage engineering, tờ sáng Canvas Mist):
tổng đóng góp 12 tháng, streak hiện tại, streak dài nhất. Lưới ô không vẽ lại vì GitHub đã hiện ngay bên dưới.

Chạy: GITHUB_TOKEN=... python .github/scripts/meter.py [login]   ->  assets/meters.svg
"""
import base64, datetime as dt, json, os, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
LOGIN = sys.argv[1] if len(sys.argv) > 1 else "TCL-DA"
W, PAD = 860, 33
MIST, INK, CARBON, STEEL, GRAPHITE = "#f6f8f7", "#000000", "#0f0e12", "#e5e5e5", "#b2b2b2"
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def fetch(token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def streaks(counts: list[int]) -> tuple[int, int]:
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:  # hôm nay chưa commit thì chưa tính là đứt chuỗi
        i -= 1
    while i >= 0 and counts[i]:
        cur += 1; i -= 1
    return cur, longest


def font_css() -> str:
    css = []
    for wt in (100, 300):
        b64 = base64.b64encode((ASSETS / "font" / f"inter-{wt}.woff2").read_bytes()).decode()
        css.append(f"@font-face{{font-family:te;font-weight:{wt};src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    css.append("text{font-family:te,Inter,'Helvetica Neue',Arial,sans-serif}.t{font-weight:100}.l{font-weight:300}")
    return "".join(css)


def text(x, y, s, size, cls, fill, anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" fill="{fill}" text-anchor="{anchor}">{s}</text>'


def rule(y, color, x1=PAD, x2=W - PAD):
    return f'<line x1="{x1}" y1="{y + 0.5}" x2="{x2}" y2="{y + 0.5}" stroke="{color}"/>'


def render(cal: dict, today: str) -> str:
    counts = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
    cur, longest = streaks(counts)
    readouts = [(f'{cal["totalContributions"]:,}', "contributions", "last 12 months"),
                (str(cur), "current streak", "days in a row"),
                (str(longest), "longest streak", "days, last 12 months")]
    FOOT = 96
    body_h = 236
    H = body_h + FOOT
    b = [f'<rect width="{W}" height="{body_h}" fill="{MIST}"/>',
         rule(14, INK),
         text(PAD, 50, "02", 13, "l", INK), text(PAD + 44, 50, "meters", 13, "l", INK),
         text(W - PAD, 50, f"updated {today}", 13, "l", INK, "end"),
         rule(70, STEEL)]
    col = (W - 2 * PAD) / 3
    for i, (num, lab, sub) in enumerate(readouts):
        x0 = PAD + round(i * col)
        x = x0 + (0 if i == 0 else 22)
        b.append(text(x, 140, num, 64, "t", INK))
        b.append(text(x, 172, lab, 13, "l", INK))
        b.append(text(x, 192, sub, 13, "l", INK))
        if i:
            b.append(f'<line x1="{x0 + 0.5}" y1="86" x2="{x0 + 0.5}" y2="198" stroke="{STEEL}"/>')
    b.append(rule(214, STEEL))
    fy = body_h
    b += [f'<rect y="{fy}" width="{W}" height="{FOOT}" fill="{CARBON}"/>',
          text(PAD, fy + 54, "tcl-da", 13, "l", MIST),
          text(PAD + 80, fy + 54, "github.com/TCL-DA", 13, "l", MIST),
          text(W - PAD, fy + 54, "flat. hairline. zero radius.", 13, "l", GRAPHITE, "end")]
    label = (f"{cal['totalContributions']} contributions in the last 12 months, "
             f"current streak {cur} days, longest streak {longest} days")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{label}"><style>{font_css()}</style>{"".join(b)}</svg>')


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set")
    cal = fetch(token)
    (ASSETS / "meters.svg").write_text(render(cal, dt.date.today().isoformat()), encoding="utf-8")
    print(f"total={cal['totalContributions']}")


if __name__ == "__main__":
    main()
