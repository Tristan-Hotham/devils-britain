# Where the Devil Lives

Devil's Dyke, Devil's Punch Bowl, Devil's Arrows, Devil's Bridge, Devil's Kitchen: where does the Devil live in Britain? This study collects every Devil, Scots Deil and Gaelic devil name on the Ordnance Survey's open gazetteer and river network (107 features), 23 named Devil monuments and landmarks in other national open records, and 393 saint-named natural features as the Christian counterpart. Each Devil and saint name is compared with 50 ordinary OS features of the same kind from the same 50 km square, and with random points of land.

**Interactive version:** https://tristan-hotham.github.io/devils-britain/

**Paper:** https://doi.org/10.5281/zenodo.23691878

**Blog post:** https://blog.tristanhotham.com/2026/10/27/devils-britain/

By Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Companion studies: [Here Be Dragons](https://tristan-hotham.github.io/here-be-dragons/) (the same matched-name method), [Whose Church Is It?](https://tristan-hotham.github.io/saints-and-wells/) (churches), [From Saint to Wish](https://tristan-hotham.github.io/holy-wells/), [Is the Barrow a European Thing?](https://tristan-hotham.github.io/barrows-of-europe/), [The Megalith Highway](https://tristan-hotham.github.io/megalith-highway/), [Within Sight](https://tristan-hotham.github.io/within-sight/) (hillforts).

## Headline results

- Names: 107 Devil names in Great Britain: 101 in OS Open Names and 6 watercourses in OS Open Rivers; 63 in England, 37 in Scotland, 7 in Wales. 16 are Scots Deil and 2 Gaelic.
- What the Devil owns: 24 names (22%) give him a household or trade (kitchen, chair, dining room, frying pan, oven, bellows, punch bowl); dens, holes and pools 21; woods 15. Valleys and hollows are 2.4 times and coastal features 2.1 times their share of all named OS features; hills 0.4 times.
- The old stones: 31% of Devil names lie within 1 km of a recorded prehistoric monument (barrow, megalith or hillfort), against 19% of matched places and 13% of random land (chance below 0.001). Northern names 39% against 21%.
- The saints: saint-named features (not borrowing a nearby parish name, n = 310) show no prehistoric excess (18% against 18%) but lie near churches (47% within 1 km against 31%) and holy wells (13% within 2 km against 4%), both chance below 0.001. Devil names: church 34% against 31%, holy well 6% against 3%.
- Ground: median slope at Devil names 2.9 degrees against 2.2 for matched places (chance 0.022) and 1.8 for random land; relief within 1 km no different from matched places (65 m against 68 m).
- Edges: no county-boundary effect (11% within 2 km of a county boundary against 13%).
- Famous Devils: 23 named Devil monuments and landmarks in national open records, 13 of them prehistoric and 7 bridges; only 3 have a Devil name in OS Open Names within 1.5 km. Where Wikipedia dates the name, it is late: Devil's Arrows 1687, Devil's Bridge (Ceredigion) 1734, Devil's Jumps 1765.

## Files

- `index.html`: the interactive page (Leaflet map, charts). Data are embedded.
- `header.png`: social card (1200 by 630).
- `data/devil_names.csv`: one row per Devil name: OS row number (`os_feature_row`; watercourses are numbered from 10,000,000), names, the word after Devil (`devil_owns`) and its class, form (English, Scots Deil, Gaelic), OS local type, source, coordinates (WGS84 and British National Grid), region, county, control stratum, and every measure: nearest church, holy well, barrow, megalith, hillfort (names and km), nearest prehistoric monument, named watercourse, coast and county boundary (km), elevation, relief within 1 km (m) and slope (degrees).
- `data/saint_names.csv`: the same for the saint-named features, with the saint and whether a settlement within 5 km shares it (`parish_named`).
- `data/devil_landmarks.csv`: the named Devil monuments and landmarks with kind, coordinates, nearest OS settlement, the record(s) they come from, and the Wikipedia note on when the name or legend is first recorded.
- `data/ireland_devil_names.csv`: OpenStreetMap Devil names in the Republic of Ireland (map only, not tested).
- `data/controls.csv.gz`: the 50 matched names and 50 random land points for each Devil and saint name, with the same measures.
- `data/test_results.csv`: every test: group, measure, control type, observed value, control value, 95% range of the replicate controls, chance value.
- `data/results.json`: every number used on the page, in the paper, the blog post and the collage.
- `code/terms.py`: the matching rules and word classes, with tests. `code/landmarks.py`: the landmark records.
- `code/01_points.py`, `code/02_measure.py`, `code/03_analyse.py`, `code/04_build_site.py`, `code/05_header.py`: run in that order. `release/` holds the paper and blog figure scripts and `reddit/` the collage.

## Method in brief

Matching rule (NAME1 and NAME2 of OS Open Names; watercourse names of OS Open Rivers): Devil as a word with or without 's, s or s' (not Mandeville or Devilla); Devils- fused to a following word (Devilsden, Devilsmouth, Devilspit, Devilsrest); Scots Deil, Deil's, Deils as a word (not Welsh Deildre or Deilo); Gaelic Deamhain, Diabhail, Dhiabhail. 11 near misses are listed in `results.json`. Hell, Satan, Old Nick and similar were not searched. Saint rule: features that are not settlements with St, St. or Saint followed by a capitalised word; 83 that share their saint with a settlement within 5 km are reported separately. Controls: 50 OS names of the same local type from the same 50 km grid square (100 km, then country, when fewer than 20), excluding every Devil and saint name; watercourses matched with named watercourses; 50 random land points in the same square; 2,000 replicate control sets, one control per name, two-sided chance values. Monuments: 12,387 barrows and cairns (OpenStreetMap and Wikidata, via Is the Barrow a European Thing?), 1,194 megaliths and stone circles (OpenStreetMap and Wikidata, via The Megalith Highway and Same Shape, Different Millennia), 3,610 hillforts (Atlas of Hillforts); 36,435 Wikidata churches; 367 holy wells (From Saint to Wish and Whose Church Is It?). Terrain: AWS Terrain Tiles at zoom 10 (about 100 m cells), relief = highest minus lowest ground on rings out to 1 km, slope across 200 m. County boundaries: ONS 2025 (ceremonial counties in England, preserved counties in Wales, council areas in Scotland).

Caveats: few names (107), so class results are suggestive; names record stories, not dates, and many may be recent; OS Open Names leaves out antiquities, so the famous monument Devils are counted separately and not tested; monument records vary by area and holy wells are thin; coastal promontory forts drive the coastal result; modern counties are not parishes; 15 measures on many groups, so isolated chance values near 0.05 deserve caution.

## Rerun

Needs Python 3 with pandas, numpy, scipy, shapely 2 and pyproj (and playwright for the header). Place these one folder above this repository (or set `HIST`): `osnames_gb.tsv` (OS Open Names extract), `osrivers/Data/oprvrs_gb.gpkg` (OS Open Rivers), `how-roman-is-your-road/data/counties.geojson`, `saints-and-wells/data/churches.csv.gz` and `holy_wells.csv`, `holy-wells/data/wells.csv`, `barrows-of-europe/data/barrows.csv`, `megalith-highway/data/megaliths.csv`, `stone-circles/data/stone_circles.csv`, `within-sight/data/forts_visibility.csv` and `within-sight/code/dem.py`, `_data8/uk_bundle_wikidata_osm.json`, `_data10/wikipedia_batch10.json.gz` and `_data10/wd_osm_bundle10.json.gz`; the DEM (`hist_dem_z10.bin` and its index, set `DEM_BIN` and `DEM_IDX`). Then run the scripts in `code/` in order.

## Sources and licence

- Place names and rivers: OS Open Names and OS Open Rivers. Contains OS data © Crown copyright and database right 2026. Open Government Licence v3.0.
- County boundaries: Office for National Statistics, OGL v3.0, via https://github.com/Tristan-Hotham/how-roman-is-your-road
- Barrows, megaliths, stone circles, holy wells: © OpenStreetMap contributors (ODbL 1.0) and Wikidata (CC0), via https://github.com/Tristan-Hotham/barrows-of-europe, https://github.com/Tristan-Hotham/megalith-highway, https://github.com/Tristan-Hotham/stone-circles and https://github.com/Tristan-Hotham/holy-wells
- Churches and holy wells: Wikidata, CC0, via https://github.com/Tristan-Hotham/saints-and-wells
- Bridges: Wikidata, CC0.
- Hillforts: Lock, G. and Ralston, I. (2017) Atlas of Hillforts of Britain and Ireland, https://hillforts.arch.ox.ac.uk, CC BY-SA 4.0, via https://github.com/Tristan-Hotham/within-sight
- Landmark notes: English Wikipedia, CC BY-SA 4.0 (articles linked in `data/devil_landmarks.csv`).
- Ireland: © OpenStreetMap contributors, ODbL 1.0.
- Terrain: AWS Terrain Tiles (Mapzen/Tilezen), https://registry.opendata.aws/terrain-tiles/
- Base map tiles on the page: Esri. Map library: Leaflet.

Because the Wikipedia text and the Atlas of Hillforts data are CC BY-SA, the derived data (`data/`) and the text are released under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/); distances to OpenStreetMap features and the Irish names derive from data under the ODbL. Code (`code/`) is MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) *Where the Devil Lives: Devil place names, prehistoric monuments and saints in Britain.* Data study and paper. Zenodo. https://doi.org/10.5281/zenodo.23691878

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
