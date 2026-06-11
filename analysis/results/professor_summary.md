# Professor Summary: Honest Improvement Audit

## What did we try to improve?

We tried to improve the capstone's honest model performance without using leakage or random-split scores as evidence. The audit focused on two tasks:

- NOW: predict current PM2.5 at a new sensor-less site, evaluated by leave-whole-sites-out validation.
- FUTURE: forecast PM2.5 +1 to +7 days at a known site, evaluated by chronological same-row comparison.

The main technical question was whether a finer k=6 site categorization could replace the accepted k=4 setting, and whether RandomForest / rolling-7 baselines could replace the LSTM forecaster.

## What improved honestly?

The audit improved understanding more than it improved the production model.

- k=6 does capture meaningful finer pollution regimes: it splits sites by pollution level, volatility, ventilation, and humidity.
- A 30-45 day short-deploy window works better than the inherited 60-day k=6 deploy window in the focused diagnostic.
- RandomForest and rolling-7 persistence are credible future-forecast challengers on identical rows, especially at longer horizons.

## What looked good but was not deployable?

k=6 full-history looked strong because it used the held-out site's complete PM2.5 history to assign its category. That is useful as an upper bound, but it is not deployable at a new sensor-less site. It is effectively an oracle regime label.

This is why the audit separates:

- non-deployable upper bounds, which explain the ceiling;
- short-deploy models, which use only early PM2.5 observations;
- zero-deploy models, which use geodata/weather only.

## What remains the accepted model?

The accepted production recommendation remains unchanged:

- NOW: keep the k=4 categorize-then-predict pipeline.
- SAFETY: keep the k=4 safety-tier framing, with a tunable Dangerous alert threshold.
- FUTURE: keep the LSTM as the headline forecaster, while adding RF and rolling-7 as challenger baselines.

## Most honest final conclusion

The audit strengthens the capstone because it shows restraint: we did not replace the model just because one diagnostic score looked better. k=6 is scientifically interesting, but with only 39 sites its fine clusters are too fragile and not recoverable enough from deployable early-window evidence. The accepted k=4 pipeline remains the most defensible model for real use.

## What Not To Claim

- Do not claim k=6 is the new production model.
- Do not claim RF beats LSTM overall.
- Do not claim random split performance as real-world performance.
- Do not claim full-history category assignment is deployable at a new site.
