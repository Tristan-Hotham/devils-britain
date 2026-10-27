"""Step 1. Build the points to measure.

Writes ../work/points.csv, one row per point:
  set = devil   OS Open Names features whose NAME1 or NAME2 matches the Devil rule (terms.py), plus named watercourses
                in OS Open Rivers that match it (one point per watercourse: the link midpoint nearest the middle)
        saint   OS Open Names features that are not settlements and whose name matches the saint rule (terms.py)
        match   matched ordinary names: for each Devil or saint feature, K features of the same OS local type drawn at
                random from the same 50 km grid square (100 km, then country, as fallbacks when fewer than 20), leaving out
                every Devil and saint name. Watercourses are matched with other named watercourses.
        rand    random land points: for each Devil or saint feature, K points on land in the same 50 km square
Also writes ../work/landmarks.json (named Devil monuments, landmarks.py), ../work/ireland.json (OpenStreetMap Devil
names in the Republic of Ireland) and ../work/counts.json.
Shared inputs are read in place from the folder above this repository (set HIST to change it).
Run: python3 code/01_points.py
"""
import gzip, json, os, re, sqlite3
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
import shapely
from shapely import wkb
from shapely.geometry import shape
from terms import DEVIL, NEAR_MISS, SAINT, SCOTS, GAELIC, head_word, word_class, saint_of
from landmarks import collect

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
WORK = os.path.join(ROOT, "work"); os.makedirs(WORK, exist_ok=True)
K = 50
rng = np.random.default_rng(20261027)
TI = Transformer.from_crs(27700, 4326, always_xy=True)
TR = Transformer.from_crs(4326, 27700, always_xy=True)

os_ = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", dtype=str, keep_default_na=False)
for c in ("lat", "lon", "x", "y"):
    os_[c] = os_[c].astype(float)
os_["fid"] = np.arange(len(os_))
os_["src"] = "OS Open Names"

# ---------- OS Open Rivers: one point per named watercourse (per name and 50 km square) ----------
con = sqlite3.connect(os.path.join(HIST, "osrivers", "Data", "oprvrs_gb.gpkg"))
wl = []
for blob, name, alt in con.execute("select geometry, watercourse_name, watercourse_name_alternative from watercourse_link where watercourse_name is not null"):
    env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(blob[3] >> 1) & 7]
    g = wkb.loads(bytes(blob[8 + env:]))
    p = g.interpolate(0.5, normalized=True)
    wl.append((name, alt or "", p.x, p.y))
con.close()
W = pd.DataFrame(wl, columns=["name1", "name2", "x", "y"])
W["cell"] = (W.x // 50000).astype(int).astype(str) + "_" + (W.y // 50000).astype(int).astype(str)
reps = []
for (nm, cell), g in W.groupby(["name1", "cell"]):
    mx, my = g.x.mean(), g.y.mean()
    j = np.argmin((g.x - mx) ** 2 + (g.y - my) ** 2)
    reps.append((nm, g.x.iloc[j], g.y.iloc[j]))
WR = pd.DataFrame(reps, columns=["name1", "x", "y"])
WR["lon"], WR["lat"] = TI.transform(WR.x.values, WR.y.values)
WR["name2"] = ""; WR["type"] = "hydrography"; WR["local_type"] = "Watercourse"; WR["src"] = "OS Open Rivers"
# region, county, country from the nearest OS Open Names feature
t = cKDTree(np.c_[os_.x, os_.y])
_, ii = t.query(np.c_[WR.x, WR.y])
for c in ("region", "country", "county", "district"):
    WR[c] = os_[c].values[ii]
WR["populated_place"] = ""; WR["lang1"] = ""; WR["lang2"] = ""
WR["fid"] = np.arange(len(WR)) + 10_000_000
ALL = pd.concat([os_, WR[os_.columns]], ignore_index=True)
for s in (50000, 100000):
    ALL[f"c{s//1000}"] = (ALL.x // s).astype(int).astype(str) + "_" + (ALL.y // s).astype(int).astype(str)

ALL["devil"] = ALL.name1.str.contains(DEVIL) | ALL.name2.str.contains(DEVIL)
ALL["saint_word"] = [saint_of(a) or saint_of(b) for a, b in zip(ALL.name1, ALL.name2)]
ALL["saint"] = ALL.saint_word.notna() & (ALL.type != "populatedPlace") & (ALL.src == "OS Open Names") & ~ALL.devil
ALL["near_miss"] = (ALL.name1.str.contains(NEAR_MISS) | ALL.name2.str.contains(NEAR_MISS)) & ~ALL.devil
pool = ALL[~ALL.devil & ALL.saint_word.isna()]
groups = {s: pool.groupby([f"c{s}", "local_type"]).indices for s in (50, 100)}
gc = pool.groupby(["country", "local_type"]).indices

# a saint feature "borrows a parish name" when a settlement within 5 km has a name beginning with the same "St X"
pp = ALL[(ALL.type == "populatedPlace") & ALL.saint_word.notna()]
ppt = cKDTree(np.c_[pp.x, pp.y])


def parish_named(r):
    for j in ppt.query_ball_point([r.x, r.y], 5000):
        if pp.saint_word.iloc[j] == r.saint_word:
            return True
    return False


cty = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "counties.geojson")))
land = shapely.union_all([shape(f["geometry"]) for f in cty["features"]])
shapely.prepare(land)
rows = []


def controls(r, key, set_):
    idx = None
    for s in (50, 100):
        ii = groups[s].get((getattr(r, f"c{s}"), r.local_type))
        if ii is not None and len(ii) >= 20:
            idx, st = ii, f"{s} km"; break
    if idx is None:
        idx, st = gc[(r.country, r.local_type)], "country"
    for j in rng.choice(idx, K, replace=len(idx) < K):
        q = pool.iloc[j]
        rows.append(dict(set="match", parent=key, pset=set_, fid=int(q.fid), name=q.name1, name2=q.name2, local_type=q.local_type,
                         type=q.type, lat=q.lat, lon=q.lon, x=q.x, y=q.y, country=q.country, region=q.region,
                         county=q.county or q.district, stratum=st))
    # random land in the same 50 km square; squares with almost no land widen to 150 km, then 350 km, centred on it
    got, side, tries = [], 50000, 0
    while len(got) < K:
        cx, cy = (r.x // 50000) * 50000 - (side - 50000) / 2, (r.y // 50000) * 50000 - (side - 50000) / 2
        xs = cx + rng.random(400) * side; ys = cy + rng.random(400) * side
        lo, la = TI.transform(xs, ys)
        ok = shapely.contains_xy(land, lo, la)
        got += [(a, b, c, d) for a, b, c, d, o in zip(xs, ys, la, lo, ok) if o]
        tries += 1
        if tries in (5, 10) and len(got) < K:
            side = {5: 150000, 10: 350000}[tries]
    for a, b, c, d in got[:K]:
        rows.append(dict(set="rand", parent=key, pset=set_, fid=-1, name="", name2="", local_type="", type="", lat=c, lon=d,
                         x=a, y=b, country=r.country, region=r.region, county="", stratum=f"{side // 1000} km"))
    return st


DV = ALL[ALL.devil]
# a watercourse that crosses a 50 km square line gets two points above: keep one per Devil watercourse name
keep = []
for r in DV.itertuples():
    if r.src == "OS Open Rivers" and any(k.src == "OS Open Rivers" and k.name1 == r.name1 and np.hypot(k.x - r.x, k.y - r.y) < 30000 for k in keep):
        continue
    keep.append(r)
DV = DV.loc[[r.Index for r in keep]]
for r in DV.itertuples():
    st = controls(r, r.fid, "devil")
    hw = head_word(r.name1, r.name2)
    nm = r.name1 + r.name2
    rows.append(dict(set="devil", parent=r.fid, pset="devil", fid=r.fid, name=r.name1, name2=r.name2, local_type=r.local_type, type=r.type,
                     lat=r.lat, lon=r.lon, x=r.x, y=r.y, country=r.country, region=r.region, county=r.county or r.district,
                     stratum=st, src=r.src, head=hw, wclass=word_class(hw),
                     form="Gaelic" if GAELIC.search(nm) else ("Scots Deil" if SCOTS.search(nm) else "English Devil")))
print("devil", len(DV), DV.src.value_counts().to_dict())
SA = ALL[ALL.saint]
for r in SA.itertuples():
    st = controls(r, r.fid, "saint")
    rows.append(dict(set="saint", parent=r.fid, pset="saint", fid=r.fid, name=r.name1, name2=r.name2, local_type=r.local_type, type=r.type,
                     lat=r.lat, lon=r.lon, x=r.x, y=r.y, country=r.country, region=r.region, county=r.county or r.district,
                     stratum=st, src=r.src, saint_name=r.saint_word, parish_named=parish_named(r)))
print("saint", len(SA))
P = pd.DataFrame(rows)
P.insert(0, "pid", np.arange(len(P)))
P.to_csv(os.path.join(WORK, "points.csv"), index=False)
print(P.groupby("set").size().to_dict())
print("strata", P[P.set == "match"].groupby(["pset", "stratum"]).size().to_dict())

# ---------- landmarks ----------
LM = collect(HIST)
pl = os_[os_.local_type.isin(["Village", "Town", "Hamlet", "City", "Suburban Area"])]
pt = cKDTree(np.c_[pl.x, pl.y])
for o in LM:
    x, y = TR.transform(o["lon"], o["lat"])
    d, j = pt.query([x, y])
    o["x"], o["y"] = x, y
    o["near"] = pl.name1.iloc[j]
    o["county"] = pl.county.iloc[j] or pl.district.iloc[j]
    o["country"] = pl.country.iloc[j]
    o["region"] = pl.region.iloc[j]
json.dump(LM, open(os.path.join(WORK, "landmarks.json"), "w"), indent=1)
print("landmarks", len(LM))

# ---------- Ireland (OpenStreetMap names, Republic of Ireland) ----------
B = json.load(gzip.open(os.path.join(HIST, "_data10", "wd_osm_bundle10.json.gz")))
IE = []
NOT_PLACE = re.compile(r"Burger|Holiday|Equestrian|Car Park|Parking|Walk|Route|cross$", re.I)
for line in B["osm_ie_folk_names"].split("\n")[1:]:
    f = line.split("\t")
    if len(f) < 3: continue
    nm = f[1].strip('"')
    if not DEVIL.search(nm) or NOT_PLACE.search(nm): continue
    pts = re.findall(r"(-?\d+\.\d+) (-?\d+\.\d+)", f[-1])
    if not pts: continue
    a = np.array(pts, float)
    IE.append(dict(osm=f[0].strip("<>"), name=nm, name_ga=f[2].strip('"') if len(f) > 3 else "", lon=float(a[:, 0].mean()), lat=float(a[:, 1].mean())))
# one point per name within 3 km
ded = []
for r in IE:
    base = re.sub(r" (Wood|Waterfall|Far North Top|North Top|South Top)$", "", r["name"])
    if any(re.sub(r" (Wood|Waterfall|Far North Top|North Top|South Top)$", "", d["name"]) == base and abs(d["lat"] - r["lat"]) < 0.03 and abs(d["lon"] - r["lon"]) < 0.05 for d in ded):
        continue
    ded.append(r)
json.dump(dict(raw=len(IE), points=ded), open(os.path.join(WORK, "ireland.json"), "w"), indent=1)
print("ireland", len(IE), "->", len(ded), [d["name"] for d in ded])

nm_ = ALL[ALL.near_miss]
json.dump({"n_os_features": int(len(os_)), "n_watercourses": int(len(WR)), "n_watercourse_links": int(len(W)),
           "near_miss": nm_.name1.value_counts().head(30).to_dict(), "n_near_miss": int(len(nm_)),
           "os_by_region": os_.groupby("region").size().to_dict(),
           "os_by_local_type": os_[os_.type != "populatedPlace"].local_type.value_counts().to_dict(),
           "n_os_nonsettlement": int((os_.type != "populatedPlace").sum())},
          open(os.path.join(WORK, "counts.json"), "w"), indent=1)
