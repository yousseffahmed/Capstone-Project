# 4th-cap-handover — folder map

**Status: ✅ CLOSED / FINALIZED (2026-06-07).** Nothing pending; no handover carries over.
**Reorganized 2026-06-07** into a clean tree (index at root · HTML in `pages/` · docs in `docs/` · build
system in `build/`), all references corrected.

**▶ Human entry point: open `index.html`** (at the deliverable root) — the START-HERE page that maps
everything and tells you how to traverse the findings and results. Every page has a global nav bar.

---

## What this is
The finalized 4th-cap deliverable: a **categorize-then-predict** pipeline for Kampala PM2.5 turned into a
**planner safety-tier tool** — nowcast a sensor-less place, forecast a week ahead, graded by the EPA tier a
planner acts on. Every headline number is honest (out-of-sample / out-of-time).

## Layout
```
4th-cap-handover/
├── index.html              ← START HERE (the only HTML at root) · built by build/build_home.py
├── README.txt              ← plain-text handover note
├── pages/                  ← all the interactive HTML (self-contained, offline)
│   ├── capstone_pyramid.html     the 4-view switcher
│   │   ├── index_consolidated.html   📚 whole story (10 stages)   · build_4th.py + stages_4th.js
│   │   ├── index_session.html        ④ this iteration (3)         · build_session.py + stages_session.js
│   │   ├── index_forecast.html       🔮 the arc (7)               · build_forecast.py + stages_forecast.js
│   │   └── index_predictor.html      🎯 tool + planner map (6)     · build_predictor.py + stages_predictor.js
│   ├── kampala_planner_prototype.html  the interactive tool       · build_prototype.py
│   └── FINDINGS / FINAL_REPORT / DECISION_LOG .html  (rendered from docs/*.md via marked.js)
├── docs/                   ← writeups + deck + this map
│   ├── FINDINGS.md · FINAL_REPORT.md · DECISION_LOG.md · HANDOVER.md · STRATEGY_4th-cap.md · CONTEXT.md
│   └── capstone_presentation_v2.{pptx,pdf}                         · build_deck_4th.py
├── build/                  ← the HTML build system (only needed to rebuild the pages)
│   ├── build_home.py · build_4th.py · build_session.py · build_forecast.py · build_predictor.py
│   │   · build_prototype.py · build_deck_4th.py
│   ├── stages_{4th,session,forecast,predictor}.js   the per-view content
│   ├── index_src.html      the pyramid engine (build target — edit stages_*.js, not the built html)
│   └── _assets/marked.min.js   markdown renderer for the doc pages
├── analysis/               ← all data-science code + results/ (CSVs, figures, JSON) + models/
└── data/                   ← merged_kampala_complete.csv  (the one working table)
```

## Reproduce (venv at `../../working/.venv`, run from `analysis/`)
Core: `site_categorize → pipeline → bakeoff_now → fetch_external → eval_external → bakeoff_future →
lstm_future (own process) → finalize_now`.
Investigation + tool: `investigate_categorization → improve_blind_cat → fig_investigation →
fetch_basemap → predict_map → fig_safety_map → export_ref → predict_testcases → new_site_predict`.
Then rebuild the HTML from `build/`: `python build/build_home.py`, `build_4th.py`, `build_session.py`,
`build_forecast.py`, `build_predictor.py`, `build_prototype.py` (the build scripts are HERE-relative —
they read `../analysis` + `../docs`, write `../pages` + `../index.html`). Fixed seeds (42).

## Notes
- The global nav bar is **location-aware** (one definition; a small script computes correct relative
  links whether a page sits at root or in `pages/`, and hides itself inside the switcher's iframe).
- AOD is **not** a lever/roadmap item here; it appears only describing the Adong-2025 precedent.
- LSTM numbers are locked (re-train in its own process to refresh).
- 280 MB of raw source data + the 3rd-cap pipeline + superseded artifacts were quarantined to
  `../../trash/2026-06-07-cap4-finalize/` (recoverable); the kept `data/merged_kampala_complete.csv`
  is all the analysis needs.
