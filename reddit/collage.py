"""r/dataisbeautiful collage for Where the Devil Lives (2400 x 3000 px).
Every number comes from ../data/results.json and the data files. Run from this folder: python3 collage.py
Fonts: FONT_DIR with FrauncesVar.ttf, SourceSerif4-*.ttf and IBMPlexMono-*.ttf (github.com/google/fonts).
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts") + "/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND = "#EFE8DC", "#1D1915", "#665D54", "#DCD2C3"
HOT, EMBER, SAINT, BAND = "#B42B17", "#D8641E", "#3F6C8E", "#B7AC9E"

R = json.load(open(os.path.join(ROOT, "data", "results.json")))
G = R["groups"]
DV = pd.read_csv(os.path.join(ROOT, "data", "devil_names.csv"), keep_default_na=False, na_values=[""])
LM = pd.read_csv(os.path.join(ROOT, "data", "devil_landmarks.csv"))
base = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", usecols=["x", "y"]).sample(150000, random_state=1)
pc = lambda v: f"{v * 100:.0f}%"

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
for inset, lw in ((0.012, 2.4), (0.018, 0.9)):
    fig.add_artist(Rectangle((inset, inset * 0.8), 1 - 2 * inset, 1 - 1.6 * inset, transform=fig.transFigure, fill=False, ec=FG, lw=lw))

fig.text(0.045, 0.968, "Where does the", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(0.045, 0.918, "Devil", fontproperties=DISP, fontsize=50, color=HOT, va="top")
fig.text(0.215, 0.918, "live in Britain?", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(0.045, 0.856, f"{R['n_devil']} Devil, Deil and Gaelic devil names on the Ordnance Survey's open map, each compared with 50 ordinary\n"
         f"places of the same kind nearby; and {R['n_saint_own']} saint-named features, tested the same way, as the Christian counterpart.",
         family=SER, fontsize=14, color=FG, va="top", linespacing=1.4)

# hero map: ember dots with a glow, monuments as diamonds
ax = fig.add_axes([0.02, 0.27, 0.56, 0.505])
ax.scatter(base.x, base.y, s=0.3, c=LAND, lw=0, rasterized=True)
ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(40000, 680000); ax.set_ylim(5000, 990000)
ax.scatter(DV.x, DV.y, s=260, c=EMBER, alpha=0.13, lw=0, zorder=2)
ax.scatter(DV.x, DV.y, s=26, c=HOT, lw=0.5, edgecolors=BG, zorder=3, label=f"Devil place name  {len(DV)}")
pre = LM[LM.prehistoric]; oth = LM[~LM.prehistoric]
ax.scatter(pre.x, pre.y, s=120, marker="D", c=FG, edgecolors=BG, lw=1.2, zorder=5, label=f"Devil monument, prehistoric  {len(pre)}")
ax.scatter(oth.x, oth.y, s=90, marker="D", c=BG, edgecolors=FG, lw=1.4, zorder=5, label=f"Devil's Bridge or landmark  {len(oth)}")
LBL = {"Devil's Arrows": (520000, 470000), "Devil's Dyke|hillfort": (560000, 40000), "Devil's Punch Bowl": (430000, 15000),
       "Devil's Den": (255000, 40000), "Devil's Quoits": (520000, 300000), "Devil's Bridge|52.3768": (60000, 330000)}
BOX = dict(boxstyle="round,pad=0.15", fc=BG, ec="none", alpha=0.85)
for r in LM.itertuples():
    for k, (dx, dy) in LBL.items():
        nm, _, cond = k.partition("|")
        if r.label == nm and (not cond or cond == r.kind or cond in f"{r.lat:.4f}"):
            ax.annotate(nm, xy=(r.x, r.y), xytext=(dx, dy), family=SER, fontsize=11.5, color=FG, style="italic", bbox=BOX,
                        arrowprops=dict(arrowstyle="-", color=FG, lw=0.6, shrinkA=0, shrinkB=4), zorder=6)
for nm, dx, dy in [("The Devil's Point", 50000, 840000), ("Devil's Kitchen", 50000, 140000)]:
    q = DV[(DV.name2 == nm) | (DV.name == nm)].iloc[0]
    ax.annotate(nm, xy=(q.x, q.y), xytext=(dx, dy), family=SER, fontsize=11.5, color=FG, style="italic", bbox=BOX,
                arrowprops=dict(arrowstyle="-", color=FG, lw=0.6, shrinkA=0, shrinkB=4), zorder=6)
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="upper left", bbox_to_anchor=(0.045, 0.813), frameon=False, prop={"family": MONO, "size": 10.5},
           labelcolor=FG, handletextpad=0.3, labelspacing=0.5)

# right column: big numbers
g = G["devil"]; s = G["saint_own"]
notes = [
    (pc(g["prehist_1"]["match"]["obs"]), HOT, f"of Devil names lie within 1 km of a\nrecorded barrow, standing stone or hillfort.\nMatched ordinary places: {pc(g['prehist_1']['match']['base'])}.\nRandom land: {pc(g['prehist_1']['rand']['base'])}."),
    (pc(s["church_1"]["match"]["obs"]), SAINT, f"of saint-named features lie within 1 km\nof a church (matched: {pc(s['church_1']['match']['base'])}), and {pc(s['well_2']['match']['obs'])}\nwithin 2 km of a holy well ({pc(s['well_2']['match']['base'])}). Saints\nshow no pull to the old stones ({pc(s['prehist_1']['match']['obs'])} v {pc(s['prehist_1']['match']['base'])})."),
    (f"{R['word_class']['household']['n']}", HOT, f"names make the Devil a householder:\nkitchen, chair, dining room, frying pan,\nkettle, oven, bellows, punch bowl. {R['wc_household_coastal']} of\nthem are coastal rocks, coves and beaches."),
    ("1687", FG, f"is the earliest record of a famous Devil\nname in the Wikipedia articles I checked\n(the Devil's Arrows, Stone Age stones).\nThen 1734 (Devil's Bridge), 1765 (Jumps)."),
]
tx = fig.add_axes([0.6, 0.275, 0.37, 0.545]); tx.axis("off")
for (big, col, small), y in zip(notes, [1.0, 0.75, 0.50, 0.25]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=40, color=col, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# bottom row: Devil v saint against matched places
fig.text(0.045, 0.252, "DEVIL AND SAINT NAMES AGAINST 50 MATCHED PLACES EACH  (whiskers: 95% range of 2,000 draws)", family=MONO, fontsize=10.5, color=MUT)
P4 = [("prehist_1", "Prehistoric site, 1 km"), ("hillfort_2", "Hillfort, 2 km"), ("church_1", "Church, 1 km"), ("well_2", "Holy well, 2 km")]
for i, (k, lab) in enumerate(P4):
    a = fig.add_axes([0.06 + i * 0.235, 0.13, 0.195, 0.092], facecolor=BG)
    vals, cols, errs = [], [], []
    for grp, col in (("devil", HOT), ("saint_own", SAINT)):
        x = G[grp][k]["match"]
        vals += [x["obs"], x["base"]]; cols += [col, BAND]; errs += [None, (x["base_lo"], x["base_hi"])]
    pos = [0, 0.85, 2.1, 2.95]
    a.bar(pos, [v * 100 for v in vals], color=cols, width=0.75)
    for j, (v, e) in enumerate(zip(vals, errs)):
        if e: a.errorbar(pos[j], (e[0] + e[1]) * 50, yerr=(e[1] - e[0]) * 50, color=FG, lw=1, capsize=3)
        a.text(pos[j], max(v, e[1] if e else 0) * 100 + 2.5, pc(v), ha="center", family=MONO, fontsize=10, color=FG)
    a.set_ylim(0, 62); a.set_xticks([0.425, 2.525]); a.set_xticklabels(["Devil", "Saint"], family=MONO, fontsize=10.5)
    a.set_yticks([]); [a.spines[q].set_visible(False) for q in ("top", "right", "left")]; a.spines["bottom"].set_color(MUT)
    a.tick_params(length=0, colors=FG)
    a.set_title(lab, family=SER, fontsize=13, color=FG, pad=4, fontweight="semibold")
fig.text(0.045, 0.093, "Coloured bar: the names. Grey bar beside it: their matched ordinary places (same OS feature type, same 50 km square).",
         family=MONO, fontsize=9.2, color=MUT)

fig.text(0.045, 0.026,
         "Data: OS Open Names and OS Open Rivers (contains OS data © Crown copyright and database right 2026, OGL v3). Barrows, megaliths,\n"
         "stone circles, holy wells: OpenStreetMap (ODbL) and Wikidata (CC0). Hillforts: Atlas of Hillforts of Britain and Ireland (CC BY-SA 4.0).\n"
         "Churches, bridges: Wikidata. Dates and legends: English Wikipedia (CC BY-SA 4.0). Names record stories, not dates: many may be recent.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=8.8, color=MUT, linespacing=1.45)
fig.savefig(os.path.join(HERE, "where_the_devil_lives.png"), facecolor=BG, dpi=200)
print("ok")
