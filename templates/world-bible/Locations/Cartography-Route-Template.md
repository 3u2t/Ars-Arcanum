<!-- AI-GENERATED EDUCATIONAL NON-COMMERCIAL CREATIVE WORKFLOW TEMPLATE -->
---
fileClass: JourneyRoute
type: journey_route
name: "<% tp.file.title %>"
route_name: "High Pass Road"
tags:
  - world/journey
  - world/cartography
origin_node: "[[Locations/Location-Template|High-Sanctuary]]"
destination_node: "[[Locations/Location-Template|Whispering-Vale]]"
total_distance_km: 185
elevation_gain_m: 650
elevation_loss_m: 1200
terrain_friction_index: 1.45
choke_points:
  - "The Razor Gap (Hex 35-19)"
  - "The Silver Bridge (Hex 36-21)"
primary_transport: "Horseback / Marching Infantry"
standard_march_days: 7.5
forced_march_days: 4.8
daily_ration_kg_per_person: 1.2
daily_water_liters_per_person: 3.5
baggage_train_speed_km_day: 18
cavalry_scout_speed_km_day: 42
---

# <% tp.file.title %> — Cartography & Journey Route

> [!NOTE] ⚠️ EDUCATIONAL TEMPLATE (AI-GENERATED)
> **Notice**: This template was AI-generated for educational demonstration and craft guidance within the Ars Arcanum operating system. It is strictly non-commercial and provided solely to demonstrate system features, mechanical schemas, and engine capabilities. Authors should replace placeholder values with their original worldbuilding details.

<details>
<summary>💡 <b>Ars Arcanum Engine Guidance & Feature Breakdown (Click to Expand)</b></summary>

### Features Demonstrated in This Template:
- **Dijkstra Journey Router**: `cartography` (`arcanum cartography --route 'High-Sanctuary' 'Whispering-Vale'`) — Finds lowest-friction travel path across rivers, roads, and mountain passes using Tobler's Hiking Function.
- **Obsidian Leaflet Route Overlay**: `obsidian-leaflet-plugin` — Direct polyline route rendering with milestone pins and distance rulers.
- **Voronoi Realm Border Generator**: `cartography` (`arcanum cartography --realm-borders`) — Computes organic territorial influence boundaries from castle and capital coordinates.
- **March Duration Calculator**: `journey` (`arcanum journey --distance-km 185 --terrain mountain --cavalry`) — Computes realistic travel durations based on troop count, encumbrance, elevation changes, and weather.
- **Supply & Feed Burn Auditor**: `journey` (`arcanum journey --party-size 12 --horses 8 --days 14`) — Calculates water and grain wagon consumption curves per soldier and mount, identifying supply exhaustion checkpoints.

### How to Use for Your Projects:
1. Specify the `origin_node` and `destination_node` along with intermediate waypoints.
2. Adjust the `terrain_friction_index` (e.g. 1.0 = paved imperial highway, 1.4 = rocky mountain trail, 2.2 = trackless swamp/jungle).
3. Use the Waypoint Stage Ledger to structure realistic travel chapters in your manuscript.
</details>

---

## 1. Route Topography & Cartographic Waypoints

```
[High-Sanctuary] (Elev: 1,450m) Hex 34-18
        |
        v  (32 km, Friction: 1.2 — Paved Switchbacks)
[The Razor Gap] (Elev: 1,620m) Hex 35-19 — *Choke Point & Toll Post*
        |
        v  (58 km, Friction: 1.8 — Glacial Scree Trail)
[Shattered Basin Outpost] (Elev: 1,100m) Hex 36-20 — *Freshwater Spring*
        |
        v  (45 km, Friction: 1.5 — River Canyon Road)
[The Silver Bridge] (Elev: 620m) Hex 36-21 — *Fortified River Crossing*
        |
        v  (50 km, Friction: 1.0 — Valley Highway)
[Whispering-Vale] (Elev: 250m) Hex 37-23
```

```leaflet
id: high-pass-route-map
image: [[Aethelgard_Regional_Map.png]]
lat: 50.4
long: 34.2
minZoom: 1
maxZoom: 6
defaultZoom: 3
unit: leagues
scale: 1
marker: default, 50.4, 34.2, [[Locations/Location-Template|High-Sanctuary]]
marker: default, 48.8, 37.1, [[Locations/Location-Template|Whispering-Vale]]
```

---

## 2. Marching Schedule & Logistical Requirements

### For a Standard Company (100 Infantry, 20 Cavalry, 10 Pack Mules):
- **Total Route Distance**: 185 km
- **Expected Duration (Standard March)**: 7.5 days (avg 24.6 km/day)
- **Total Rations Consumed**: 900 kg grain/hard-tack (1.2 kg/person/day)
- **Total Water Consumed**: 3,150 liters (3.5 L/person/day; pack mules require 25 L/day)
- **Critical Foraging Window**: Between Hex 35-19 and Hex 36-20 (glaciers; zero forage for mounts).

---

## 3. Tactical Choke Points & Narrative Hazards

| Waypoint | Distance | Terrain Hazard | Tactical Ambush Risk |
| :--- | :--- | :--- | :--- |
| **The Razor Gap** | 32 km | 3-meter wide defile flanked by 80m scree walls; prone to rockfalls. | Extremely High: 20 archers can hold against 500 infantry. |
| **Glacial Scree Run**| 78 km | Loose shale; pack mules lose shoes; travel speed reduced to 12 km/day. | Moderate: Poor visibility during mountain storms. |
| **The Silver Bridge**| 135 km | 60-meter timber and iron span over a 40-meter gorge. | High: Bridge destruction forces a 5-day detour around the lake. |

---

## 4. Manuscript Scene Hooks & Pacing Rails
- **Scene Hook 1 (Act I Travel)**: The company reaches the Razor Gap at twilight only to find the royal toll post abandoned and smeared with fresh blood.
- **Scene Hook 2 (Act II Fatigue)**: On Day 4, a supply mule plunges into a crevasse, destroying half the water casks and forcing the characters to ration water at 1.0 L/day during forced march.

<!-- ARS_ARCANUM_COMPREHENSIVE_CRAFT_AND_ENGINE_SHOWCASE -->
<details>
<summary><strong>⚙️ Ars Arcanum Deterministic Engine &amp; Craft Doctrine Integration Guide (Click to Expand)</strong></summary>

### How the CLI Compilers &amp; Craft Engines Use This Template
- **Unified VaultIndex (`arcanum vault-index`)**: Indexes YAML frontmatter (including `|` and `>` multiline block scalars), `@directives`, `[[Wikilinks]]`, multi-paragraph dialogue ratios, and SHA-256 paragraph hashes (`CACHE_VERSION = 3`).
- **Epistemic POV Firewall (`arcanum validate-epistemic`)**: Compares character `knows:` baselines against chapter `learns:` and `references:` (`EPI-201..203`).
- **Planetary Calendar &amp; Route Solver (`arcanum timeline-audit`)**: Audits `world.yaml` month lengths and `Locations/` route distances (`TIME-301..302`).
- **PolyGlot Conlang Linter (`arcanum conlang-check`)**: Validates lexicon terms and phonotactics (`CON-401..402`).
- **Resource Conservation Ledger (`arcanum ledger-audit`)**: Audits `resource_pools` and chapter `state_delta` transitions (`LED-501..502`).
- **Multi-POV Narrative Braid (`arcanum braid`)**: Tracks POV word shares, tension curves, and drought alerts (`BRD-601`).
- **Phase-Aware Effort (`arcanum sprint-effort`)**: Weights First Draft (`1.00x`), On-Phase Outline (`1.00x`), Worldbuilding (`0.50x`), Revision (`0.20x`), and blocks premature editing during Drafting (`0.00x`).
- **Live Obsidian Bridge (`arcanum continuity-suite`)**: Generates `_Arcanum_Diagnostics.md` inside your vault root.

</details>
