SMART CITY CAPSTONE — Kampala PM2.5   ·   Team Handover
=======================================================

▶ START HERE:  open   index.html   in any web browser.

It is a self-contained landing page that maps everything and tells you how to
traverse the findings and results. Everything works OFFLINE — no install, no
internet needed. Every page has a top navigation bar, so you can jump between
the tool, the views, and the documents from anywhere.

The one-line story
------------------
Can free data give a Kampala planner trustworthy PM2.5 where there is no sensor,
and a few days ahead? Yes, with honest limits — we sort each place into a "kind",
predict on it, and grade by the EPA safety tier a planner acts on.

Folder layout
-------------
  index.html ........ START HERE — the navigator (links to everything)
  pages/ ............ all the interactive HTML pages:
        capstone_pyramid.html ............ the 4 "pyramid" views (the whole story)
        kampala_planner_prototype.html ... the interactive tool (safety map + predictor)
        FINDINGS / FINAL_REPORT / DECISION_LOG .html ... the writeups, rendered to read in a browser
  docs/ ............. the writeups (.md sources) + CONTEXT.md (folder map) + the slide deck (.pdf/.pptx)
  analysis/ ......... all the data-science code, result CSVs, figures, persisted models
  data/ ............. merged_kampala_complete.csv — the working table (39 sites x 13,944 site-days)
  build/ ............ the scripts that generate the HTML pages (only needed to rebuild them)

Reproduce the analysis (optional)
---------------------------------
  Python 3.9+  ·  pip install numpy pandas scikit-learn lightgbm joblib matplotlib scipy xgboost
  cd analysis  and run the scripts (fixed seeds; see docs/CONTEXT.md for the run order).

Honest methodology: every headline number is out-of-sample (NOW = leave-sites-out,
FUTURE = chronological). Leaky random-split numbers are labelled as such.

Finalized 2026-06-07.
