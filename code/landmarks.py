"""Named Devil monuments and landmarks from national open records already on disk, plus the Wikipedia articles
on the best-known ones. These are the Devil's famous addresses: most are NOT in OS Open Names, which leaves out
antiquities and most structures. Each landmark keeps the record(s) it came from, so its position can be checked.

Sources read in place (folder above this repository, or HIST):
  megalith-highway/data/megaliths.csv      OpenStreetMap (ODbL) and Wikidata (CC0), via The Megalith Highway
  stone-circles/data/stone_circles.csv     OpenStreetMap and Wikidata, via Same Shape, Different Millennia (stone circles)
  barrows-of-europe/data/barrows.csv       OpenStreetMap and Wikidata, via Is the Barrow a European Thing?
  within-sight/data/forts_visibility.csv   Atlas of Hillforts of Britain and Ireland (CC BY-SA 4.0)
  _data8/uk_bundle_wikidata_osm.json       Wikidata bridges (CC0)
  _data10/wikipedia_batch10.json.gz        English Wikipedia articles with coordinates (CC BY-SA 4.0)
Left out on purpose: records whose Devil word names a different thing nearby ("Round cairn ... 350m SSW of the
Devil's Chair"; Leckhampton Hill hillfort, whose alternative name is the Devil's Chimney rock stack; bridges over
Devil's Water and Devil's Brook, which take the river's name).
"""
import gzip, json, math, os, re
import pandas as pd

KIND_LABEL = {"barrow": "Barrow or cairn", "stone": "Standing stones", "circle": "Stone circle", "tomb": "Chambered tomb",
              "hillfort": "Hillfort", "dyke": "Linear earthwork", "bridge": "Bridge", "natural": "Natural hollow or hills"}
PREHIST = {"barrow", "stone", "circle", "tomb", "hillfort"}

# What the Wikipedia articles say about when the Devil name, or the legend, is first recorded (sentence quoted
# in short). Only what the article text on disk says; nothing added.
WP_NOTES = {
    "Devil's Arrows": dict(kind="stone", name_first="1687", note="The name is mentioned by John Aubrey, who visited and drew the stones in 1687; a legend that the Devil threw the stones at Aldborough goes back to 1721. The stones were erected in the Stone Age.",
                           url="https://en.wikipedia.org/wiki/Devil%27s_Arrows"),
    "Devil's Bridge, Ceredigion": dict(kind="bridge", name_first="1734", note="The first mention of the structure using the English name Devil's Bridge, in historical records, is from 1734.",
                                       url="https://en.wikipedia.org/wiki/Devil%27s_Bridge,_Ceredigion"),
    "Devil's Jumps, Churt": dict(kind="natural", name_first="1765", note="The first mention of the Devil's Jumps appears to be on a map by John Rocque, dating to 1765. Legend: the Devil leapt from hill to hill until Thor threw a boulder at him.",
                                 url="https://en.wikipedia.org/wiki/Devil%27s_Jumps,_Churt"),
    "Devil's Dyke, Cambridgeshire": dict(kind="dyke", name_first="", note="In medieval times it was simply called the dic (the ditch), le Micheldyche or magnum fossatum (great ditch). Thought most likely Anglo-Saxon, by analogy with Fleam Dyke (AD 330 to 510).",
                                         url="https://en.wikipedia.org/wiki/Devil%27s_Dyke,_Cambridgeshire"),
    "Devil's Dyke, Sussex": dict(kind="hillfort", name_first="", note="Used as a defensive site before and after the Iron Age (Atlas of Hillforts: Devil's Dyke, Poynings). Legend: the Devil dug a trench through the Downs so that the sea would drown the Christians of the Weald; St Cuthman of Steyning fooled him with a candle and a crowing cock, and he fled, leaving the dyke unfinished.",
                                 url="https://en.wikipedia.org/wiki/Devil%27s_Dyke,_Sussex"),
    "Devil's Punch Bowl": dict(kind="natural", name_first="", note="Legend: the Devil hurled lumps of earth at Thor, or Thor at the Devil, leaving the hollow.",
                               url="https://en.wikipedia.org/wiki/Devil%27s_Punch_Bowl"),
}
from terms import DEVIL as DEV


def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def core(n):
    n = n.replace("’", "'").replace("The ", "")
    n = re.sub(r",.*|\(.*", "", n).strip()
    return n.replace("Quoits", "Quoit").replace("Devils", "Devil's")


def collect(HIST):
    rows = []
    M = pd.read_csv(os.path.join(HIST, "megalith-highway", "data", "megaliths.csv"))
    M = M[(M.country == "United Kingdom") & M.name.fillna("").str.contains(DEV)]
    for r in M.itertuples():
        k = {"circle": "circle", "dolmen": "tomb", "menhir": "stone", "rows": "stone"}.get(r.cls, "stone")
        rows.append(dict(name=r.name, lat=r.lat, lon=r.lon, kind=k, src="Megalith Highway (OpenStreetMap " + r.osm + ")"))
    S = pd.read_csv(os.path.join(HIST, "stone-circles", "data", "stone_circles.csv"))
    S = S[(S.country == "United Kingdom") & S.name.fillna("").str.contains(DEV)]
    for r in S.itertuples():
        rows.append(dict(name=r.name, lat=r.lat, lon=r.lon, kind="circle", src="Same Shape, Different Millennia (OpenStreetMap " + str(r.osm) + ", Wikidata " + str(r.qid) + ")"))
    B = pd.read_csv(os.path.join(HIST, "barrows-of-europe", "data", "barrows.csv"), usecols=["src", "id", "name", "lon", "lat", "country", "cls"])
    B = B[(B.country == "United Kingdom") & B.name.fillna("").str.contains(DEV) & ~B.name.fillna("").str.contains("SSW of the Devil")]
    for r in B.itertuples():
        k = "tomb" if "chambered" in str(r.cls) else "barrow"
        rows.append(dict(name=r.name.replace("Bowl barrow on Nunwell Down known as ", ""), lat=r.lat, lon=r.lon, kind=k,
                         src=f"Is the Barrow a European Thing? ({'OpenStreetMap' if r.src == 'osm' else 'Wikidata'} {r.id})"))
    H = pd.read_csv(os.path.join(HIST, "within-sight", "data", "forts_visibility.csv"), usecols=["atlas_id", "name", "lat", "lon"])
    H = H[H.name.str.contains(DEV) & ~H.name.str.contains("Leckhampton")]
    for r in H.itertuples():
        rows.append(dict(name="Devil's Dyke hillfort, Poynings", lat=r.lat, lon=r.lon, kind="hillfort", src=f"Atlas of Hillforts, record {r.atlas_id}"))
    U = json.load(open(os.path.join(HIST, "_data8", "uk_bundle_wikidata_osm.json")))
    seen = set()
    for line in U["wd_structures_tsv"].split("\n")[1:]:
        f = line.split("\t")
        if len(f) < 5: continue
        lab = f[1].split('"')[1] if '"' in f[1] else f[1]
        if not re.search(r"Devil'?s (Backbone )?Bridge", lab) or f[0] in seen: continue
        seen.add(f[0])
        lo, la = map(float, re.findall(r"POINT\(([-\d.]+) ([-\d.]+)\)", f[4])[0])
        rows.append(dict(name=lab.replace(" SW of Horrace", "").replace(" Weston Park", ""), lat=la, lon=lo, kind="bridge",
                         src="Wikidata " + f[0].strip("<>").split("/")[-1]))
    W = json.load(gzip.open(os.path.join(HIST, "_data10", "wikipedia_batch10.json.gz")))["articles"]
    for t, v in WP_NOTES.items():
        a = W[t]
        rows.append(dict(name=t, lat=a["coord"]["lat"], lon=a["coord"]["lon"], kind=v["kind"], src="English Wikipedia: " + t))
    # merge records of the same landmark: same core name within 2 km
    out = []
    for r in rows:
        c = core(r["name"])
        for o in out:
            if (core(o["name"]) == c or c.startswith(core(o["name"])) or core(o["name"]).startswith(c)) and hav(o["lat"], o["lon"], r["lat"], r["lon"]) < 2.0:
                o["srcs"].append(r["src"]); o["n_records"] += 1
                if r["src"].startswith("English Wikipedia"):
                    o["wp"] = r["name"]
                break
        else:
            out.append(dict(r, srcs=[r["src"]], n_records=1, wp=r["name"] if r["src"].startswith("English Wikipedia") else ""))
    for o in out:
        if o["name"] in ("Devil's Dyke hillfort, Poynings",) or o["wp"] == "Devil's Dyke, Sussex":
            o["kind"] = "hillfort"
        o["label"] = re.sub(r"^The ", "", o["name"]).replace("\u2019", "'").split(",")[0] if not o["wp"] else o["wp"].split(",")[0]
        o["place_note"] = {"Devil's Dyke, Sussex": "Sussex", "Devil's Dyke, Cambridgeshire": "Cambridgeshire"}.get(o["wp"], "")
        if o["wp"]:
            o.update(name_first=WP_NOTES[o["wp"]]["name_first"], note=WP_NOTES[o["wp"]]["note"], url=WP_NOTES[o["wp"]]["url"])
        else:
            o.update(name_first="", note="", url="")
        o["kind_label"] = KIND_LABEL[o["kind"]]
        o["prehistoric"] = o["kind"] in PREHIST
        o["source"] = "; ".join(o.pop("srcs"))
        del o["src"]
    return out


if __name__ == "__main__":
    for o in collect(os.environ.get("HIST", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))):
        print(o["label"], "|", o["kind"], "|", round(o["lat"], 4), round(o["lon"], 4), "|", o["n_records"], "|", o["source"][:90])
