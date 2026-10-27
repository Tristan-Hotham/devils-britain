"""Step 3. Compare the Devil names and the saint names with their controls and write the results.

For each group and each measure, the observed statistic (a median or a share) is compared with 2,000 replicate
control sets. Each replicate takes one control at random for every feature:
  match   an ordinary OS name of the same local type (wood with wood, cove with cove) from the same 50 km square
  rand    a random land point in the same 50 km square
Chance values are two-sided: twice the share of replicates on the far side of the observed value.

Writes ../data/results.json, ../data/devil_names.csv, ../data/saint_names.csv, ../data/devil_landmarks.csv,
../data/ireland_devil_names.csv, ../data/test_results.csv, ../data/controls.csv.gz and ../work/site.json.
Run: python3 code/03_analyse.py
"""
import json, os, warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
import numpy as np, pandas as pd
from terms import CLASS_LABEL, CLASS_ORDER

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
WORK = os.path.join(ROOT, "work"); DATA = os.path.join(ROOT, "data")
NREP = 2000
rng = np.random.default_rng(666)
P = pd.read_csv(os.path.join(WORK, "measured.csv"), keep_default_na=False, na_values=[""], low_memory=False)
LAY = json.load(open(os.path.join(WORK, "layers.json")))
CNT = json.load(open(os.path.join(WORK, "counts.json")))
LM = json.load(open(os.path.join(WORK, "landmarks.json")))
IE = json.load(open(os.path.join(WORK, "ireland.json")))
NORTH = {"North East", "North West", "Yorkshire and the Humber", "Scotland"}
COASTAL = {"Other Coastal Landform", "Beach", "Bay", "Coastal Headland", "Tidal Water", "Sea", "Channel", "Island", "Group Of Islands"}

# each feature is preceded by its 50 matched and 50 random controls (see 01_points.py)
isobs = P.set.isin(["devil", "saint"]).values
P["blk"] = np.r_[0, np.cumsum(isobs)[:-1]]
obs = P[isobs].copy().reset_index(drop=True)
for c in ("name2", "head", "wclass", "form", "county"):
    obs[c] = obs[c].fillna("")
assert (P[~isobs].groupby("blk").size() == 100).all() and len(obs) == P.blk.nunique()
K = 50

MEAS = {
    "prehist_1":  ("prehist_km", "lt", 1.0, "Share within 1 km of a recorded prehistoric monument (barrow, megalith or hillfort)"),
    "prehist_med": ("prehist_km", "median", None, "Median distance to a prehistoric monument (km)"),
    "barrow_1":   ("barrow_km", "lt", 1.0, "Share within 1 km of a barrow or burial cairn"),
    "stone_2":    ("stone_km", "lt", 2.0, "Share within 2 km of a standing stone, stone circle or chambered tomb"),
    "hillfort_2": ("hillfort_km", "lt", 2.0, "Share within 2 km of a hillfort"),
    "church_1":   ("church_km", "lt", 1.0, "Share within 1 km of a church"),
    "church_med": ("church_km", "median", None, "Median distance to a church (km)"),
    "well_2":     ("well_km", "lt", 2.0, "Share within 2 km of a holy well"),
    "water_025":  ("water_km", "lt", 0.25, "Share within 250 m of a named watercourse"),
    "relief_med": ("relief_m", "median", None, "Median relief within 1 km (m)"),
    "slope_med":  ("slope_deg", "median", None, "Median slope (degrees)"),
    "steep":      ("slope_deg", "gt", 10.0, "Share on ground steeper than 10 degrees"),
    "elev_med":   ("elev_m", "median", None, "Median elevation (m)"),
    "edge_2":     ("edge_km", "lt", 2.0, "Share within 2 km of a county boundary"),
    "edge_med":   ("edge_km", "median", None, "Median distance to a county boundary (km)"),
}
cols = sorted(set(m[0] for m in MEAS.values()))
CM = {}
for s in ("match", "rand"):
    q = P[P.set == s].sort_values(["blk", "pid"])
    CM[s] = {c: q[c].values.astype(float).reshape(len(obs), K) for c in cols}


def stat(v, kind, thr):
    ok = ~np.isnan(v)
    if kind == "median": return np.nanmedian(v, -1)
    if kind == "lt": return np.where(ok, v < thr, False).sum(-1) / ok.sum(-1)
    if kind == "gt": return np.where(ok, v > thr, False).sum(-1) / ok.sum(-1)


def test(mask, mk, cs):
    col, kind, thr, _ = MEAS[mk]
    o = obs[col].values.astype(float)[mask]
    ov = float(stat(o[None], kind, thr)[0])
    C = CM[cs][col][mask]
    pick = rng.integers(0, K, size=(NREP, C.shape[0]))
    b = stat(np.take_along_axis(np.broadcast_to(C, (NREP,) + C.shape), pick[..., None], 2)[..., 0], kind, thr)
    allc = float(stat(C.ravel()[None], kind, thr)[0])
    p = min(1.0, 2 * min((b >= ov).mean(), (b <= ov).mean()))
    return dict(obs=ov, base=allc, base_lo=float(np.percentile(b, 2.5)), base_hi=float(np.percentile(b, 97.5)), p=float(p),
                n=int(mask.sum()), ratio=(ov / allc if allc else None))


isd = (obs.set == "devil").values
iss = ~isd
coastal = obs.local_type.isin(COASTAL).values
north = obs.region.isin(NORTH).values
own = iss & ~obs.parish_named.astype(str).eq("True").values
GROUPS = {
    "devil": isd,
    "devil_inland": isd & ~coastal,
    "devil_coastal": isd & coastal,
    "devil_english": isd & obs.form.eq("English Devil").values,
    "devil_scots": isd & ~obs.form.eq("English Devil").values,
    "devil_north": isd & north,
    "devil_south": isd & ~north,
    "saint": iss,
    "saint_own": own,
    "saint_parish": iss & ~own,
    "saint_inland": own & ~coastal,
}
for c in CLASS_ORDER:
    GROUPS["wc_" + c] = isd & obs.wclass.eq(c).values

R = {"n_rep": NREP, "k_controls": K, "groups": {}, "n_measures": len(MEAS)}
rows = []
for g, mask in GROUPS.items():
    R["groups"][g] = {"n": int(mask.sum())}
    if mask.sum() < 5: continue
    for mk in MEAS:
        R["groups"][g][mk] = {}
        for cs in ("match", "rand"):
            r = test(mask, mk, cs)
            R["groups"][g][mk][cs] = r
            rows.append(dict(group=g, measure=mk, label=MEAS[mk][3], control=cs, **r))
    print(g, int(mask.sum()))
pd.DataFrame(rows).to_csv(os.path.join(DATA, "test_results.csv"), index=False, float_format="%.4f")

# ---------- counts ----------
dv = obs[isd]; sa = obs[iss]
R["n_os_features"] = CNT["n_os_features"]
R["n_os_nonsettlement"] = CNT["n_os_nonsettlement"]
R["n_watercourses"] = CNT["n_watercourses"]
R["n_near_miss"] = CNT["n_near_miss"]
R["near_miss"] = CNT["near_miss"]
R["n_devil"] = int(len(dv))
R["n_devil_os"] = int((dv.src == "OS Open Names").sum())
R["n_devil_rivers"] = int((dv.src == "OS Open Rivers").sum())
R["devil_rivers"] = dv[dv.src == "OS Open Rivers"].name.tolist()
R["devil_by_form"] = dv.form.value_counts().to_dict()
R["devil_by_country"] = dv.country.value_counts().to_dict()
R["devil_settlements"] = dv[dv.type == "populatedPlace"].apply(lambda r: f"{r['name2'] or r['name']} ({r['local_type']}, {r['county']})", axis=1).tolist()
R["devil_coastal"] = int(coastal[isd].sum())
R["devil_north"] = int(north[isd].sum())
R["n_saint"] = int(len(sa))
R["n_saint_own"] = int(own.sum())
R["n_saint_parish"] = int((iss & ~own).sum())
R["saint_top"] = sa.saint_name.value_counts().head(10).to_dict()
R["saint_by_country"] = sa.country.value_counts().to_dict()
# word classes
wc = dv.wclass.value_counts()
R["word_class"] = {c: dict(n=int(wc.get(c, 0)), label=CLASS_LABEL[c], share=float(wc.get(c, 0) / len(dv)),
                           heads=dv[dv.wclass == c]["head"].value_counts().to_dict(),
                           examples=sorted(set((dv[dv.wclass == c].name2.where(dv[dv.wclass == c].name2 != "", dv[dv.wclass == c].name)).tolist()))[:40])
                   for c in CLASS_ORDER}
R["wc_household_coastal"] = int((dv.wclass.eq("household") & dv.local_type.isin(COASTAL | {"Cliff Or Slope", "Beach"})).sum())
R["heads_top"] = dv["head"].value_counts().head(12).to_dict()

# feature types: Devil, saint (own name) and all OS features that are not settlements
TYPEG = {"Coast": COASTAL | {"Cliff Or Slope"}, "Woods": {"Woodland Or Forest"}, "Valleys and hollows": {"Valley", "Cirque Or Hollow"},
         "Hills": {"Hill Or Mountain", "Spot Height", "Other Landform"}, "Water": {"Inland Water", "Waterfall", "Watercourse"},
         "Wetland and other land": {"Wetland", "Other Landcover", "Urban Greenspace"}, "Settlements": {"Village", "Hamlet", "Town", "City", "Suburban Area", "Other Settlement"}}
tg = lambda lt: next((k for k, v in TYPEG.items() if lt in v), "Wetland and other land")
dvn = dv[dv.src == "OS Open Names"]
allt = pd.Series(CNT["os_by_local_type"])
R["types"] = {}
for k in TYPEG:
    if k == "Settlements": continue
    nd = int(dvn[dvn.type != "populatedPlace"].local_type.map(tg).eq(k).sum())
    ns = int(sa[own[iss]].local_type.map(tg).eq(k).sum())
    na = int(allt[[tg(t) == k for t in allt.index]].sum())
    R["types"][k] = dict(devil=nd, saint=ns, all=na)
td = sum(v["devil"] for v in R["types"].values()); ts = sum(v["saint"] for v in R["types"].values()); ta = sum(v["all"] for v in R["types"].values())
for k, v in R["types"].items():
    v.update(devil_share=v["devil"] / td, saint_share=v["saint"] / ts, all_share=v["all"] / ta,
             devil_ratio=(v["devil"] / td) / (v["all"] / ta), saint_ratio=(v["saint"] / ts) / (v["all"] / ta))
R["types_n"] = dict(devil=td, saint=ts, all=ta)
R["devil_local_types"] = dv.local_type.value_counts().to_dict()
R["saint_local_types"] = sa[own[iss]].local_type.value_counts().head(12).to_dict()

# regions (OS Open Names only), per 100,000 features
reg = CNT["os_by_region"]
R["rate_by_region"] = {r: dict(n=int((dvn.region == r).sum()), os=int(reg[r]), per100k=float((dvn.region == r).sum() / reg[r] * 1e5),
                               deil=int(((dvn.region == r) & ~dvn.form.eq("English Devil")).sum()),
                               landmarks=int(sum(1 for o in LM if o["region"] == r))) for r in reg}
R["layers"] = LAY["counts"]

# ---------- landmarks ----------
LMD = pd.DataFrame(LM)
R["n_landmarks"] = int(len(LMD))
R["landmarks_by_kind"] = LMD.kind_label.value_counts().to_dict()
R["landmarks_prehistoric"] = int(LMD.prehistoric.sum())
R["landmarks_bridges"] = int((LMD.kind == "bridge").sum())
R["landmarks_in_osnames"] = []
on = dvn
for o in LM:
    d = np.hypot(on.x - o["x"], on.y - o["y"])
    if d.min() < 1500:
        R["landmarks_in_osnames"].append(o["label"])
R["n_landmarks_in_osnames"] = len(R["landmarks_in_osnames"])
R["landmark_rows"] = [dict(label=o["label"], kind=o["kind_label"], near=o["near"], county=o["county"], name_first=o["name_first"], note=o["note"], url=o["url"])
                      for o in LM]
R["landmarks_dated"] = [dict(label=o["label"] + (", " + o["place_note"] if o["place_note"] else ""), first=o["name_first"], note=o["note"], url=o["url"])
                        for o in LM if o["note"]]
LMD[["label", "name", "kind", "kind_label", "prehistoric", "lat", "lon", "x", "y", "near", "county", "country", "region", "n_records",
     "source", "name_first", "note", "url"]].round(5).to_csv(os.path.join(DATA, "devil_landmarks.csv"), index=False)

# ---------- Ireland ----------
IED = pd.DataFrame(IE["points"])
IED.to_csv(os.path.join(DATA, "ireland_devil_names.csv"), index=False)
R["ireland"] = dict(n_raw=IE["raw"], n=int(len(IED)), names=IED.name.tolist())

# ---------- curves for charts ----------
def hist(col, edges, mask, cs="match"):
    ob = obs[col].values.astype(float)[mask]
    cb = CM[cs][col][mask].ravel()
    clip = lambda v: np.clip(v, edges[0], edges[-1] - 1e-9)
    return dict(edges=list(map(float, edges)), obs=(np.histogram(clip(ob), edges)[0] / len(ob)).round(4).tolist(),
                ctrl=(np.histogram(clip(cb), edges)[0] / len(cb)).round(4).tolist(), n_obs=int(len(ob)))


R["curves"] = {
    "devil_relief": hist("relief_m", np.arange(0, 330, 30), GROUPS["devil"]),
    "saint_relief": hist("relief_m", np.arange(0, 330, 30), GROUPS["saint_own"]),
    "devil_prehist": hist("prehist_km", np.arange(0, 11, 1.0), GROUPS["devil"]),
    "saint_prehist": hist("prehist_km", np.arange(0, 11, 1.0), GROUPS["saint_own"]),
}

# ---------- tables ----------
keep_d = ["name", "name2", "head", "wclass", "form", "local_type", "src", "lat", "lon", "x", "y", "country", "region", "county", "stratum",
          "church", "church_km", "well", "well_km", "barrow", "barrow_km", "stone", "stone_km", "hillfort", "hillfort_km", "prehist_km",
          "water_km", "coast_km", "edge_km", "elev_m", "relief_m", "slope_deg"]
dvo = dv.copy(); dvo["os_feature_row"] = dvo.fid
dvo[["os_feature_row"] + keep_d].rename(columns={"head": "devil_owns", "wclass": "word_class", "src": "source"}).round(4).to_csv(os.path.join(DATA, "devil_names.csv"), index=False)
sao = sa.copy(); sao["os_feature_row"] = sao.fid
sao[["os_feature_row", "name", "name2", "saint_name", "parish_named", "local_type", "lat", "lon", "x", "y", "country", "region", "county", "stratum",
     "church", "church_km", "well_km", "barrow_km", "stone_km", "hillfort_km", "prehist_km", "water_km", "coast_km", "edge_km", "elev_m", "relief_m", "slope_deg"]].round(4).to_csv(
    os.path.join(DATA, "saint_names.csv"), index=False)
cc = P[P.set.isin(["match", "rand"])].copy()
cc["parent_set"] = cc.pset
cc["parent_os_feature_row"] = obs.fid.values[cc.blk.values]
cc[["set", "parent_set", "parent_os_feature_row", "name", "local_type", "lat", "lon", "church_km", "well_km", "barrow_km", "stone_km", "hillfort_km",
    "prehist_km", "water_km", "edge_km", "elev_m", "relief_m", "slope_deg"]].round(3).to_csv(os.path.join(DATA, "controls.csv.gz"), index=False, compression="gzip")

# a few named examples used in the text
def row(name, county=None):
    q = dv[(dv.name == name) | (dv.name2 == name)]
    if county: q = q[q.county == county]
    r = q.iloc[0]
    return {k: (round(float(r[k]), 3) if isinstance(r[k], (float, np.floating)) else r[k]) for k in ["name", "name2", "county", "local_type", "prehist_km", "barrow_km", "stone_km", "hillfort_km", "church_km", "relief_m", "slope_deg", "barrow", "stone", "hillfort"]}


R["ex"] = {"dyke_hill": row("Devil's Dyke", "West Sussex"), "punchbowl_arran": row("The Devil's Punchbowl"), "point": row("The Devil's Point"),
           "bridge_village": row("Devil's Bridge", "Sir Ceredigion - Ceredigion")}
R["devil_prehist_close"] = [dict(name=r.name2 or r.name, county=r.county, km=round(float(r.prehist_km), 3), what=(r.barrow if r.prehist_km == r.barrow_km else r.stone if r.prehist_km == r.stone_km else r.hillfort))
                            for r in dv.sort_values("prehist_km").head(10).itertuples()]
R["devil_steepest"] = [dict(name=r.name2 or r.name, county=r.county, relief=round(float(r.relief_m)), slope=round(float(r.slope_deg), 1))
                       for r in dv.sort_values("relief_m", ascending=False).head(8).itertuples()]
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, default=lambda v: None if v != v else (bool(v) if isinstance(v, np.bool_) else (int(v) if isinstance(v, np.integer) else float(v))))

# ---------- compact data for the page ----------
f2 = lambda v: None if pd.isna(v) else round(float(v), 2)
site = dict(
    dv=[[round(r.lat, 5), round(r.lon, 5), r.name + (f" ({r.name2})" if isinstance(r.name2, str) and r.name2 else ""), r.wclass, r.local_type, r.county or r.country,
         r.head, f2(r.prehist_km), f2(r.church_km), f2(r.well_km), int(round(r.relief_m)), r.src, r.form] for r in dv.itertuples()],
    sa=[[round(r.lat, 5), round(r.lon, 5), r.name + (f" ({r.name2})" if isinstance(r.name2, str) and r.name2 else ""), r.local_type, r.county or r.country,
         int(str(r.parish_named) == "True"), f2(r.prehist_km), f2(r.church_km), f2(r.well_km), int(round(r.relief_m))] for r in sa.itertuples()],
    lm=[[round(o["lat"], 5), round(o["lon"], 5), o["label"], o["kind"], o["kind_label"], o["near"], o["county"], o["source"], o["note"], o["url"]] for o in LM],
    ie=[[round(r["lat"], 5), round(r["lon"], 5), r["name"], r["name_ga"], r["osm"]] for r in IE["points"]],
    stones=LAY["layers"]["stones"], barrows=LAY["layers"]["barrows"], hillforts=LAY["layers"]["hillforts"], wells=LAY["layers"]["wells"],
)
json.dump(site, open(os.path.join(WORK, "site.json"), "w"), separators=(",", ":"))
print("results written")
