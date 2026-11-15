<div align="center">

<img src="docs/img/hero.jpg" alt="FireSight home screen: a rotating 3D Earth with the ISS and live habitat-atmosphere cards" width="100%">

# 🔥 FireSight

### Fire-safety intelligence beyond Earth

**Decades of NASA microgravity fire experiments, unified into one verified dataset,<br>and turned into answers for Moon bases, rovers, spacecraft and Mars habitats.**

<br>

![NASA Space Apps 2026](https://img.shields.io/badge/NASA%20Space%20Apps-2026-0b3d91?style=for-the-badge)
![Team](https://img.shields.io/badge/Team-Astra%20ZGZ-4cc2ff?style=for-the-badge)
![Tests](https://img.shields.io/badge/unified%20tests-622-ff7a33?style=for-the-badge)
![Audit](https://img.shields.io/badge/math%20audit-52%2F52%20passed-36d39a?style=for-the-badge)

![Python](https://img.shields.io/badge/Python-FastAPI-3776ab?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61dafb?logo=react&logoColor=black)
![D3](https://img.shields.io/badge/charts-D3-f9a03c?logo=d3dotjs&logoColor=white)
![three.js](https://img.shields.io/badge/3D-three.js-000000?logo=threedotjs&logoColor=white)
![Offline](https://img.shields.io/badge/works-offline%20(PWA)-5a0fc8)
![License](https://img.shields.io/badge/open%20data-CC%20BY%204.0-lightgrey)

**[🚀 Live app](#-run-it) · [🎬 Tour](#-a-30-second-tour) · [🧪 How the data is processed](#-from-chaos-to-one-verified-dataset) · [📊 Results](#-what-the-data-says) · [🛠 Tools](#-the-tools) · [✅ Trust](#-why-you-can-trust-it)**

</div>

---

## 🎬 A 30-second tour

<div align="center">
<img src="docs/img/tour.gif" alt="Animated tour: home, habitat simulator, optimizer engine computing, optimum found, experiment designer, scenario briefing, 52/52 verification" width="90%">
</div>

---

## 🌑 The problem

> *"If you want to get somebody's attention really quick, make the fire alarm go off in your spacecraft when you're still about 80,000 miles from home."* · Artemis II commander, 2026

In space, **fire does not behave like on Earth**. With no buoyancy, hot gas does not rise, and a candle flame turns into a faint blue sphere. History shows what is at stake:

| 1967 | 1970 | 1997 | 2026 |
|:---:|:---:|:---:|:---:|
| 🔥 **Apollo 1**<br>cabin fire in 100% O₂ | 💥 **Apollo 13**<br>oxygen tank explosion | 🔥 **Mir**<br>oxygen-generator fire | 🚨 **Artemis II**<br>smoke alarm in deep space |

The planned **Moon base** will breathe **30% oxygen or more at 10.2 psi or less** (Earth: 21% at 14.7 psi). It makes spacewalks easier, and it makes materials burn more easily.

NASA has the experiments to study this, but they are spread across **24 investigations**, **176 reports** and dozens of spreadsheets in different formats. **FireSight brings them together.**

---

## 🧪 From chaos to one verified dataset

The core of FireSight is its **data pipeline**. Every number in the app traces back to a NASA source.

```mermaid
flowchart LR
    A["🗂️ ACQUIRE<br/>24 PSI investigations<br/>176 NTRS reports<br/>2,997 passages"]:::step --> B["📄 EXTRACT<br/>275 FLEX tests<br/>parsed from a PDF table"]:::step
    B --> C["🧹 CLEAN<br/>units → kPa · % · cm/s · mm<br/>'3400%' → 34%<br/>impossible values flagged"]:::step
    C --> D["🧩 UNIFY<br/>622 tests · 25 fields<br/>source + confidence label"]:::step
    D --> E["📈 ANALYZE<br/>model + 300 refits<br/>evidence · gaps · bounds"]:::step
    E --> F["✅ VERIFY<br/>52 / 52 independent checks"]:::ok
    classDef step fill:#0f1722,stroke:#4cc2ff,color:#e8edf4
    classDef ok fill:#0f1722,stroke:#36d39a,color:#e8edf4
```

<details>
<summary><b>🔍 Open the pipeline step by step</b></summary>
<br>

| Step | What happens | Numbers |
|---|---|---|
| **1 · Acquire** | Investigation records from the public PSI API; PSI experiment tables (BASS, Saffire-I/III, ACME BRE, ACME CFI-G); NASA reports, fact sheets and guides indexed for search | 24 investigations · 176 reports · 2,997 passages |
| **2 · Extract** | FLEX results only exist as *Table IX* inside NASA/TP-2015-216046. A validated parser pulls every row out; missing (–) and approximate (~) values are kept, not dropped | 275 tests |
| **3 · Clean** | Units unified; names normalized ("pmma 2 cm" → PMMA, 20 mm); spreadsheet errors fixed (`3400%` → `34%`); impossible values left blank and flagged, never guessed | 0 invented values |
| **4 · Unify** | One 25-field schema; every row carries its source and a label: **measured**, **extracted** or **estimated** | 622 tests |
| **5 · Analyze** | Coverage map, nearby evidence, FLEX model with bootstrap and cross-validation, CFI-G statistics, partial-gravity bounds, gaps, recommendations, three-level summaries | 300 model refits |
| **6 · Verify** | An independent script recomputes every published number by a different route | 52 / 52 pass |

<img src="docs/img/pipeline.jpg" alt="Processing pipeline cards in the app" width="100%">

</details>

<details>
<summary><b>🧩 What is inside the 622 tests</b></summary>
<br>

| Dataset | Tests | What burned | Conditions |
|---|---:|---|---|
| BASS | 121 | PMMA, SIBAL fabric, Nomex, waxes | cabin air, forced flow |
| Saffire-I · Saffire-III | 2 + 2 | large fabric samples in Cygnus | cabin air |
| ACME BRE | 43 | gas burner emulating solids | 21–40% O₂ |
| ACME CFI-G | 179 | gaseous flames | 18–40% O₂ · 0.5–3 bar |
| FLEX | 275 | heptane and methanol droplets (+ CO₂ / He suppression) | 12–34% O₂ · 70–309 kPa |

Missing fields are shown as missing:

<img src="docs/img/completeness.jpg" alt="Data completeness matrix by field and dataset" width="100%">

</details>

---

## 📊 What the data says

<table>
<tr>
<td align="center" width="25%"><h1>97%</h1>a droplet flame keeps burning at the <b>Moon-base</b> atmosphere<br><sub>90% interval 94–99% · vs <b>66%</b> in ISS air</sub></td>
<td align="center" width="25%"><h1>5.5×</h1>longer gas flames at 30–36% O₂<br><sub>median <b>8 s → 44 s</b> · measured, ACME CFI-G</sub></td>
<td align="center" width="25%"><h1>0</h1>microgravity tests of fabrics or plastics at Moon-base oxygen<br><sub>all 125 solid tests in NASA's PSI data ran in cabin air</sub></td>
<td align="center" width="25%"><h1>8.2 psi</h1>34% O₂: the optimum under NASA's own crew limits<br><sub>NASA's chosen Exploration Atmosphere</sub></td>
</tr>
</table>

> [!IMPORTANT]
> **The materials habitats are made of have never been tested in microgravity at Moon-base oxygen in NASA's PSI data.** That is FireSight's top-priority recommended experiment: fabrics and plastics at **30% O₂ / 70.3 kPa**.

---

## 🛠 The tools

### 🌍 Habitat Simulator: what would fire do in a Moon base?

Set oxygen, pressure, gravity, ventilation and material. The engine scans **622 measured tests**, runs **300 model refits** and checks the documented gaps, live.

<img src="docs/img/simulator-engine.jpg" alt="Simulation engine running with a progress bar and log" width="100%">
<img src="docs/img/simulator.jpg" alt="Habitat simulator with KPIs, atmosphere map and flame preview" width="100%">

<details>
<summary><b>How to read it</b></summary>

- **O₂ partial pressure 21.1 kPa:** the Moon base breathes like sea level (21.2).
- **Inert gas 49.2 kPa** vs 80.0 on Earth: less nitrogen to absorb heat, so hotter flames.
- **56 nearby tests:** real measurements within distance 1.5 (1 unit = 5 O₂ points or a ×1.28 pressure ratio).
- **97% (94–99%):** droplet-flame persistence, median and 90% interval of 300 refits.
- The **red panel** appears when the chosen material has never been tested near this atmosphere.

</details>

### ⚖️ Atmosphere Optimizer: the safest air the crew can live with

Lower pressure makes spacewalks faster, and pushes oxygen (and fire) up. The optimizer searches **2,401 atmospheres × 300 models** against NASA's crew limits:
- breathing: inspired O₂ ≥ 128 mmHg;
- spacewalk readiness: N₂ ratio ≤ 1.26.

<img src="docs/img/optimizer-engine.jpg" alt="Optimizer engine at 32 percent, 462,300 model evaluations" width="100%">

> **It independently lands on 34% O₂ at 8.2 psi**, the atmosphere NASA itself selected, and it shows the price: 99% droplet-flame persistence there.

<img src="docs/img/optimizer.jpg" alt="Optimizer result: 810,059 evaluations, optimum 34 percent O2 at 56.5 kPa, heatmap and trade-off curve" width="100%">

### 🧠 Experiment Designer: which test should fly next?

Active learning on the model's uncertainty: it scores **1,092 candidate test conditions** and plans the campaign that shrinks habitat uncertainty most, then exports it as CSV. It also lists what no model can replace:

<img src="docs/img/designer-solids.jpg" alt="Solid materials table with zero existing tests at habitat atmospheres" width="100%">

<details>
<summary><b>See the full designer</b></summary>
<img src="docs/img/designer.jpg" alt="Experiment designer with information map and recommended campaign" width="100%">

*Method: the 300 bootstrap refits give a coefficient covariance Σ. A test adds Fisher information n·p(1−p)·c·cᵀ, and Σ is updated with Sherman–Morrison. Tests are picked greedily to minimize the summed prediction variance at the habitat targets.*
</details>

### 🔬 Model Lab: train it yourself, live

The model is not a fixed table. **Model Lab retrains it on the server, in real time, with Python and scikit-learn**, and streams every cross-validation fold and bootstrap refit to the screen.

- **NASA FLEX only:** reproduces the official model exactly (AUC 0.859, Brier 0.138).
- **NASA + your tests:** upload a CSV in the template format (`o2_pct, pressure_kpa, co2_pct, he_pct, fuel, flame_persists`); every row is validated and rejected rows are reported. Nothing is stored and the official model never changes.
- **Permutation test:** shuffle the outcomes and the AUC falls to **≈ 0.46**, which is chance level, and the curve goes flat. That is the proof that it learns from the data.

<img src="docs/img/model-lab.jpg" alt="Model Lab: live training log, cross-validated AUC 0.859, official vs retrained curves" width="100%">

<details>
<summary><b>See the permutation test and a training with uploaded tests</b></summary>
<img src="docs/img/model-lab-shuffle.jpg" alt="Permutation test: AUC 0.461 with shuffled outcomes and a flat curve" width="100%">
<img src="docs/img/model-lab-user.jpg" alt="Training on NASA plus four user tests" width="100%">

*API: `POST /api/train` streams NDJSON events (one per fold and refit, then the result); `GET /api/train/template.csv` returns the 274 FLEX tests in the upload format. One training at a time per server, 8 per minute per visitor, 5,000 rows maximum.*
</details>

### 💾 Your scenarios: save, compare, brief

<table>
<tr>
<td width="30%"><img src="docs/img/save-scenario.jpg" alt="Save as scenario button"></td>
<td><b>1 · Save</b> any atmosphere (up to 30).<br><br><b>2 · Pick one</b> in the briefing: the evidence recomputes for it.<br><br><b>3 · Compare</b> them all side by side.</td>
</tr>
</table>

<img src="docs/img/briefing-scenarios.jpg" alt="Mission briefing recomputed for the saved scenario Rover EVA prep" width="100%">

<details>
<summary><b>See the comparison view</b></summary>
<img src="docs/img/comparison.jpg" alt="Mission comparison including saved scenarios" width="100%">
</details>

### 🧭 And much more

<table>
<tr>
<td width="50%"><img src="docs/img/materials.jpg" alt="Materials intelligence matrix"><br><b>Materials Intelligence:</b> every material class × habitat; the zeros are the gaps.</td>
<td width="50%"><img src="docs/img/gaps.jpg" alt="Data gaps coverage heatmap"><br><b>Data Gaps & Priorities:</b> what has never been measured, ranked.</td>
</tr>
<tr>
<td><img src="docs/img/explorer.jpg" alt="Data explorer"><br><b>Data Explorer:</b> 24 investigations, 622 records, filters, CSV/JSON export.</td>
<td><img src="docs/img/graph.jpg" alt="Knowledge graph"><br><b>Knowledge Graph:</b> investigations linked by hardware, fuel and measurement.</td>
</tr>
<tr>
<td><img src="docs/img/ask.jpg" alt="Ask FireSight assistant"><br><b>Ask FireSight:</b> plain-language answers, every sentence cited to NASA.</td>
<td><img src="docs/img/earth-mode.jpg" alt="Earth Mode"><br><b>Earth Mode:</b> airliner cabins, mountain cities, oxygen-rich rooms, hyperbaric chambers.</td>
</tr>
<tr>
<td><img src="docs/img/lessons.jpg" alt="Lessons learned"><br><b>Lessons Learned:</b> Apollo 1, Apollo 13, Mir, Artemis II.</td>
<td><img src="docs/img/how-to.jpg" alt="How to use guide"><br><b>How to Use:</b> a 3-minute guided example and a glossary.</td>
</tr>
</table>

### 📱 Anywhere, even offline

<p align="center">
<img src="docs/img/mobile-home.jpg" alt="FireSight home on a phone" width="30%">
&nbsp;&nbsp;
<img src="docs/img/mobile-sim.jpg" alt="Habitat simulator on a phone" width="30%">
</p>

Works on any phone. Once opened, it can be **installed** from the browser and keeps working **without internet**; only the AI-written answers need a connection.

---

## ✅ Why you can trust it

<img src="docs/img/models.jpg" alt="Predictive intelligence: AUC, Brier score, calibration and uncertainty bands" width="100%">

| Check | Result |
|---|---|
| Tested on flames it never saw (5-fold cross-validation, scaler fitted inside each fold) | **AUC 0.86**, vs 0.81 with oxygen alone |
| Probability error (Brier score) | **0.138**, vs 0.219 for a no-skill guess |
| Uncertainty on every estimate | **300** bootstrap refits → 90% intervals |
| Oxygen effect | each +1 point of O₂ multiplies the odds by **×1.41** (1.29–1.54) |
| Model rejected when the data does not support it | CFI-G shown as measured statistics only |
| Independent audit of every published number | **52 / 52** checks pass |

<img src="docs/img/verification.jpg" alt="Mathematical verification card: 52 of 52 checks passed" width="100%">

<details>
<summary><b>🔬 What the 52 checks cover</b></summary>

- Physiology formulas against the NASA report's own values (128, 127, 117 and 149 mmHg; R = 1.26)
- Standard atmosphere (8,000 ft = 75.3 kPa; 5,000 m = 54.05 kPa)
- Model refit from scratch: AUC, Brier, accuracy, standardization
- Bootstrap medians and intervals for 7 habitats
- Nearby-test counts and CFI-G medians recounted from raw rows
- Buoyant-flow bounds for the Moon, Mars and Earth
- Optimizer re-solved on a continuous 0.05-step grid (34% O₂, 56.5 kPa)
- Experiment-designer update against direct matrix inversion (difference < 10⁻⁸)

Run it yourself: `python pipeline/audit_math.py` in the full source.
</details>

<details>
<summary><b>⚠️ Limits we state openly</b></summary>

- Results cover the NASA PSI tables and reports we could access. NASA may have 1 g ground flammability data at elevated oxygen that is not in PSI.
- The FLEX model is for **droplet flames** (12–34% O₂, 70–309 kPa). It does not transfer directly to fabrics or plastics; outside its range, results are flagged as extrapolated.
- No partial-gravity combustion data exist in PSI: the Moon and Mars are **bounded** with buoyant-flow physics, not measured.
- BASS per-test oxygen and flow were not in the accessible tables; nominal cabin values are used and flagged.
- ACME CFI-G burn times partly depend on when operators cut the fuel, so they are descriptive only.
- FireSight is **decision support**, not a replacement for NASA materials certification.

</details>

---

## 🚀 Run it

| Option | How |
|---|---|
| 🌐 **Online** | Live link: *added once the deployment is live* |
| 🐳 **Docker / Render** | This repository deploys as-is: `render.yaml` (free plan) + `Dockerfile` |
| 💻 **Locally** | `pip install -r backend/requirements.txt` then `python -m uvicorn backend.app.main:app --port 7860` and open http://localhost:7860 |

Optional AI answers: set `FIRESIGHT_LLM_API_KEY` (an OpenAI-compatible key, Groq free tier by default) as an environment variable on the server. Without it, the assistant answers with exact cited sentences.

<details>
<summary><b>🏗 Architecture and stack</b></summary>

```
backend/   FastAPI · read-only SQLite · TF-IDF search · cited assistant
data/      firesight.db (622 tests, 24 investigations, 2,997 passages, analytics)
frontend/  React + TypeScript + D3 + three.js (prebuilt in frontend/dist)
```

- **API:** `/api/health`, `/api/investigations`, `/api/tests`, `/api/export/tests.csv`, `/api/analytics`, `/api/compare`, `/api/rank`, `/api/search`, `/api/ask`.
- **Hardening:** path-traversal protection, input validation, rate limits on AI answers, security headers.
- **Footprint:** about 175 MB of server memory.

</details>

---

## 🤝 Who built it and how

**The idea is Team Astra ZGZ's.** The team conceived FireSight, chose the challenge and set the goals: one link for the judges, free hosting, offline use, and no invented data. The team wrote the product requirements, obtained the NASA PSI study files, set the visual direction with its own reference designs and brand, decided every feature, and reviewed every result.

**Programming:** an SI coding assistant (Claude, by Anthropic) was used to write most of the code, under the team's direction.

**No data value is AI-generated.** Every number comes from NASA PSI tables, NASA technical reports or a model fitted to them. Photographs are NASA originals; the station drawing, flame preview and logo are SI-assisted graphics and are marked in the app.

---

<div align="center">

**Data:** NASA Physical Sciences Informatics · NASA Technical Reports Server · NASA/TP-2015-216046 · NASA HRP Evidence Report on hypobaric hypoxia (2015) · NASA images (public domain)

*Independent project for the NASA Space Apps Challenge 2026. Not endorsed by NASA.*

**FireSight · Team Astra ZGZ · Dream · Analyze · Explore**

</div>
