# Presentation Talking Points: Honest Improvement Audit

## Simple Story

We did a final audit to see if we could honestly improve the model.

The important point is that we did not replace the model just because one score looked better. We separated deployable models from oracle/non-deployable upper bounds.

## What We Tested

- We tested whether k=6 site categories are better than the accepted k=4 categories.
- We tested whether a new site can recover those k=6 categories using only early deploy data.
- We tested whether RandomForest or rolling-7 persistence can beat the LSTM forecast on the same rows.

## What We Found

- k=6 is meaningful: it captures finer pollution regimes.
- But k=6 is fragile with only 39 sites.
- k=6 full-history is not deployable because it uses the full PM2.5 history of the held-out site.
- Deployable k=6 improves with a 30-45 day window, but it still does not beat accepted k=4.
- The accepted model remains k=4 because it generalizes better.

## Future Forecasting

- RandomForest is a strong challenger.
- Rolling-7 persistence is also surprisingly strong at +7 days.
- But RF does not beat LSTM overall.
- LSTM remains the headline forecaster, with RF and rolling-7 added as honest challengers.

## Verbal Defense

If asked why we did not switch to k=6:

> k=6 gave a better-looking upper bound only when the model was allowed to know the held-out site's full pollution history. That is not available at a new site. Once we restricted the model to deployable information, k=6 no longer beat k=4. So the honest decision is to keep k=4 and treat k=6 as future research.

If asked why this audit matters:

> It shows that the final result is not overclaimed. We tested stronger alternatives, separated real deployable gains from oracle upper bounds, and kept the model that generalizes best under the honest validation setup.

## What Not To Claim

- Do not claim k=6 is the new production model.
- Do not claim RF beats LSTM overall.
- Do not claim random split performance as real-world performance.
- Do not claim full-history category assignment is deployable at a new site.
