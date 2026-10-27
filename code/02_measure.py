"""Step 2. Measure every point in ../work/points.csv.

Adds, for each point (distances in km, straight line on the British National Grid):
  church_km     nearest church building in Wikidata (Great Britain, any date), as parsed in Whose Church Is It?
  well_km       nearest holy well (Great Britain): holy wells in From Saint to Wish (OpenStreetMap, Wikidata) and
                Whose Church Is It? (Wikidata), merged
  barrow_km     nearest barrow, cairn or burial mound (OpenStreetMap and Wikidata, via Is the Barrow a European Thing?)
  stone_km      nearest megalith or stone circle: standing stones, stone rows, circles and chambered tombs
                (OpenStreetMap and Wikidata, via The Megalith Highway and Same Shape, Different Millennia)
  hillfort_km   nearest hillfort in the Atlas of Hillforts of Britain and Ireland
  prehist_km    nearest of the three above (any recorded prehistoric monument)
  water_km      nearest named watercourse in OS Open Rivers
  coast_km      distance to the coast (edge of the county land outline)
  edge_km       distance to the nearest county boundary shared with another county (ceremonial counties in England,
                preserved counties in Wales, council areas in Scotland; ONS 2025 boundaries)
  elev_m, relief_m, slope_deg   terrain from the AWS Terrain Tiles DEM at zoom 10 (about 100 m cells):
                elevation at the point, highest minus lowest ground within 1 km, and steepest slope across 200 m
Writes ../work/measured.csv and ../work/layers.json (small layers for the page).
Run: python3 code/02_measure.py
"""
import json, os, sqlite3, sys, time
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely import wkb
import shapely
from shapely.geometry import shape

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
WORK = os.path.join(ROOT, "work")
sys.path.insert(0, os.path.join(HIST, "within-sight", "code"))
from dem import DEM  # AWS Terrain Tiles reader from Within Sight

TR = Transformer.from_crs(4326, 27700, always_xy=True)
t0 = time.time()
P = pd.read_csv(os.path.join(WORK, "points.csv"), keep_default_na=False, na_values=[""], low_memory=False)
XY = np.c_[P.x.values, P.y.values]
cty = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "counties.geojson")))
polys = [shape(f["geometry"]) for f in cty["features"]]
land = shapely.union_all(polys)
shapely.prepare(land)
layers, counts = {}, {}


def nearest(lon, lat):
    x, y = TR.transform(np.asarray(lon, float), np.asarray(lat, float))
    d, i = cKDTree(np.c_[x, y]).query(XY)
    return d / 1000, i


def gb(df):
    df = df.dropna(subset=["lon", "lat"])
    return df[shapely.contains_xy(land, df.lon.values, df.lat.values)].reset_index(drop=True)


# ---------- churches and holy wells ----------
C = pd.read_csv(os.path.join(HIST, "saints-and-wells", "data", "churches.csv.gz"))
C = gb(C[C.country == "GB"])
P["church_km"], i = nearest(C.lon, C.lat); P["church"] = C.label.values[i]
counts["n_churches"] = int(len(C))
W1 = pd.read_csv(os.path.join(HIST, "holy-wells", "data", "wells.csv"))
W1 = W1[W1.nation.isin(["England", "Scotland", "Wales"]) & (W1.holy.astype(str) == "True")][["name", "lon", "lat"]]
W2 = pd.read_csv(os.path.join(HIST, "saints-and-wells", "data", "holy_wells.csv"))
W2 = W2[W2.country == "GB"].rename(columns={"label": "name"})[["name", "lon", "lat"]]
WW = gb(pd.concat([W1, W2], ignore_index=True))
wx, wy = TR.transform(WW.lon.values, WW.lat.values)
dup = set()
for a, b in cKDTree(np.c_[wx, wy]).query_pairs(100):
    dup.add(max(a, b))
WW = WW.drop(index=sorted(dup)).reset_index(drop=True)
P["well_km"], i = nearest(WW.lon, WW.lat); P["well"] = WW.name.values[i]
counts["n_wells"] = int(len(WW))
print("churches, wells", len(C), len(WW), round(time.time() - t0))

# ---------- prehistoric monuments ----------
B = pd.read_csv(os.path.join(HIST, "barrows-of-europe", "data", "barrows.csv"), usecols=["name", "lon", "lat", "country"])
B = gb(B[B.country == "United Kingdom"])
P["barrow_km"], i = nearest(B.lon, B.lat); P["barrow"] = B.name.fillna("").values[i]
M = pd.read_csv(os.path.join(HIST, "megalith-highway", "data", "megaliths.csv"), usecols=["name", "lon", "lat", "country", "cls"])
M = M[(M.country == "United Kingdom")][["name", "lon", "lat"]]
SC = pd.read_csv(os.path.join(HIST, "stone-circles", "data", "stone_circles.csv"), usecols=["name", "lon", "lat", "country"])
SC = SC[SC.country == "United Kingdom"][["name", "lon", "lat"]]
ST = gb(pd.concat([M, SC], ignore_index=True))
sx, sy = TR.transform(ST.lon.values, ST.lat.values)
dup = set(max(a, b) for a, b in cKDTree(np.c_[sx, sy]).query_pairs(50))
ST = ST.drop(index=sorted(dup)).reset_index(drop=True)
P["stone_km"], i = nearest(ST.lon, ST.lat); P["stone"] = ST.name.fillna("").values[i]
H = pd.read_csv(os.path.join(HIST, "within-sight", "data", "forts_visibility.csv"), usecols=["name", "country", "lat", "lon"])
H = H[H.country.isin(["England", "Scotland", "Wales"])].reset_index(drop=True)
P["hillfort_km"], i = nearest(H.lon, H.lat); P["hillfort"] = H.name.values[i]
P["prehist_km"] = P[["barrow_km", "stone_km", "hillfort_km"]].min(axis=1)
counts.update(n_barrows=int(len(B)), n_stones=int(len(ST)), n_hillforts=int(len(H)))
layers["barrows"] = np.round(np.c_[B.lat.values, B.lon.values], 3).tolist()
layers["stones"] = np.round(np.c_[ST.lat.values, ST.lon.values], 3).tolist()
layers["hillforts"] = np.round(np.c_[H.lat.values, H.lon.values], 3).tolist()
layers["wells"] = np.round(np.c_[WW.lat.values, WW.lon.values], 4).tolist()
print("prehistoric", len(B), len(ST), len(H), round(time.time() - t0))


# ---------- watercourses ----------
def densify(lines, step=100.0):
    out = []
    for c in lines:
        a, b = c[:-1], c[1:]
        L = np.hypot(*(b - a).T)
        n = np.maximum(1, np.ceil(L / step).astype(int))
        for (ax, ay), (bx, by), k in zip(a, b, n):
            t = np.arange(k) / k
            out.append(np.c_[ax + (bx - ax) * t, ay + (by - ay) * t])
        out.append(c[-1:])
    return np.concatenate(out)


con = sqlite3.connect(os.path.join(HIST, "osrivers", "Data", "oprvrs_gb.gpkg"))
wat = []
for (blob,) in con.execute("select geometry from watercourse_link where watercourse_name is not null"):
    env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(blob[3] >> 1) & 7]
    wat.append(np.asarray(wkb.loads(bytes(blob[8 + env:])).coords)[:, :2])
con.close()
P["water_km"] = cKDTree(densify(wat)).query(XY)[0] / 1000
del wat
print("water", round(time.time() - t0))

# ---------- coast and county edges ----------
def ring_pts(geom, step=100.0):
    out = []
    for pg in shapely.get_parts(geom):
        if pg.geom_type != "Polygon": continue
        for ring in [pg.exterior, *pg.interiors]:
            c = np.asarray(ring.coords)
            x, y = TR.transform(c[:, 0], c[:, 1])
            out.append(densify([np.c_[x, y]], step))
    return np.concatenate(out)


bp, lab = [], []
for k, pg in enumerate(polys):
    q = ring_pts(pg)
    bp.append(q); lab.append(np.full(len(q), k))
bp = np.concatenate(bp); lab = np.concatenate(lab)
tb = cKDTree(bp)
# a boundary point is internal when another county's boundary lies within 200 m
internal = np.zeros(len(bp), bool)
for j, nb in enumerate(tb.query_ball_point(bp, 200)):
    internal[j] = any(lab[n] != lab[j] for n in nb)
P["edge_km"] = cKDTree(bp[internal]).query(XY)[0] / 1000
P["coast_km"] = cKDTree(bp[~internal]).query(XY)[0] / 1000
counts["edge_points"] = int(internal.sum())
print("edges", round(time.time() - t0))

# ---------- terrain ----------
dem = DEM()
lat, lon = P.lat.values, P.lon.values
P["elev_m"] = dem.elev(lat, lon)
mlat = 111320.0
mlon = 111320.0 * np.cos(np.radians(lat))
rel_lo = P.elev_m.values.copy(); rel_hi = P.elev_m.values.copy()
for rr in (250, 500, 750, 1000):
    for a in np.radians(np.arange(0, 360, 15)):
        e = dem.elev(lat + rr * np.sin(a) / mlat, lon + rr * np.cos(a) / mlon)
        rel_lo = np.minimum(rel_lo, e); rel_hi = np.maximum(rel_hi, e)
P["relief_m"] = rel_hi - rel_lo
d = 100.0
ex = dem.elev(lat, lon + d / mlon) - dem.elev(lat, lon - d / mlon)
ey = dem.elev(lat + d / mlat, lon) - dem.elev(lat - d / mlat, lon)
P["slope_deg"] = np.degrees(np.arctan(np.hypot(ex, ey) / (2 * d)))
del dem
print("terrain", round(time.time() - t0))
P.to_csv(os.path.join(WORK, "measured.csv"), index=False)
json.dump(dict(layers=layers, counts=counts), open(os.path.join(WORK, "layers.json"), "w"), separators=(",", ":"))
print("done", round(time.time() - t0))
