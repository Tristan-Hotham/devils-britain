"""Step 5. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: set FONT_DIR to a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf and IBMPlexMono-Regular.ttf
(from github.com/google/fonts); otherwise system serif fonts are used.
Usage: FONT_DIR=/path/to/fonts python3 code/05_header.py
"""
import json, math, os
import numpy as np, shapely
from shapely.geometry import shape
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
S = json.load(open(os.path.join(ROOT, "work", "site.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")
proj = lambda lat, lon: (lon * math.cos(math.radians(54.5)), -lat)
nm = [proj(r[0], r[1]) for r in S["dv"]]
lg = [proj(r[0], r[1]) for r in S["lm"] if r[3] in ("barrow", "stone", "circle", "tomb", "hillfort")]
lb = [proj(r[0], r[1]) for r in S["lm"] if r[3] not in ("barrow", "stone", "circle", "tomb", "hillfort")]
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
land = shapely.union_all([shape(f["geometry"]) for f in json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "counties.geojson")))["features"]]).simplify(0.01)
bx0, by0, bx1, by1 = land.bounds
xs, ys = zip(proj(by0, bx0), proj(by1, bx1))
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
H, PAD = 600, 14
sc = (H - 2 * PAD) / (y1 - y0)
P = lambda p: ((p[0] - x0) * sc + PAD, (p[1] - y0) * sc + PAD)
W = (x1 - x0) * sc + 2 * PAD
path = ""
for pg_ in shapely.get_parts(land):
    if pg_.geom_type != "Polygon" or pg_.area < 0.003: continue
    pts = [P(proj(la, lo)) for lo, la in np.array(pg_.exterior.coords)]
    path += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4"/>' for x, y in map(P, nm))
dia = lambda x, y, c: f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{c}" stroke="#F1ECE4" stroke-width="1.5" transform="rotate(45 {x:.1f} {y:.1f})"/>'
legs = "".join(dia(x, y, "#B42B17") for x, y in map(P, lg)) + "".join(dia(x, y, "#1D1915") for x, y in map(P, lb))
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:#F1ECE4;color:#1D1915;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:66px;font:400 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#665D54;display:flex;gap:12px;align-items:center}}
.k b{{background:#B42B17;color:#fff;padding:7px 9px;font-weight:400}}
h1{{position:absolute;left:64px;top:108px;margin:0;font:900 104px/.88 Fraunces,Georgia,serif;letter-spacing:-.02em}}
h1 em{{font-style:normal;color:#B42B17;display:block}}
p{{position:absolute;left:70px;top:420px;width:600px;margin:0;font-size:27px;line-height:1.36}}
.f{{position:absolute;left:70px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#665D54}}
.rule{{position:absolute;left:70px;right:520px;top:400px;border-top:3px double #1D1915}}
svg{{position:absolute;right:40px;top:15px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Folklore × landscape</span></div>
<h1>Where the<em>Devil</em>lives</h1>
<div class="rule"></div>
<p>{R['n_devil']} Devil names in Britain. {R['groups']['devil']['prehist_1']['match']['obs'] * 100:.0f}% lie within 1 km of a prehistoric monument, against {R['groups']['devil']['prehist_1']['match']['base'] * 100:.0f}% of matched places. The saints get the churches.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{W:.0f}" height="{H}" viewBox="0 0 {W:.0f} {H}"><path d="{path}" fill="#E2D9CC" stroke="#BFB3A3" stroke-width="1"/><g fill="#D8641E" fill-opacity=".85">{dots}</g>{legs}</svg>
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html")
open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
