# Supported distinctive features

| Feature | Required fields / calculation | Interpretation / limit |
|---|---|---|
| Reliability | order_id, seller_id, status, promise, actual; eligible rate with Wilson interval, median/P90 late delay and 90-day purchase-cohort trend | Single-seller orders only; configurable minimum; uncertainty is not bias correction |
| Contribution | destination, seller, category, origin/purchase period; late count and late/eligible, filtered baseline | Descriptive contributors, not causal root causes; category populations overlap |
| Promise accuracy | purchase, promise, actual; promised/actual medians and calendar early margin | Generous promises can inflate reliability; insufficient evidence to tighten SLA |
| Adjustment | seller, destination, eligible outcomes; same top-three destination weights and >=5 per stratum | Common coverage required; raw vs adjusted populations differ; expose coverage; other confounding remains |
| Variability | actual/purchase and promise; median/P90 duration, late-delay distribution | High P90 can reveal unpredictability; extreme small cohorts are unstable |
| Watchlist | Would need credible snapshot and status history | Omitted: extraction/status as-of unknown |
| Scenario | eligible flags, late flag, one segment | Convert assumed 0-100% of late orders; fixed denominator, no overlaps or claimed savings |
| Action queue | region, eligible, late, delay | >=30 eligible, above baseline, rank sum late days; role/action/evidence/limitation/follow-up included |
| Trust | manifest, coverage, quality report | Dataset-wide metadata; eligibility cards respond to filters |
| Export | order-grain population and filter parameters | CSV plus companion metadata JSON; printable view includes filters |

See docs/metrics.md for exact formulas, docs/dataset.md for field provenance, and reports/actions.json for calculated recommendations.
