# Metric contract

Canonical aggregate definitions are executable in sql/metrics.sql; row flags and durations in sql/build.sql. API and generated reports use those same expressions. DAX reproduces them but execution is unverified.

| Metric | Population / formula | Unit |
|---|---|---|
| Orders | Count accepted fact_order rows | orders |
| Status distribution | Orders grouped by source status | orders |
| Eligible | status delivered AND actual and promise present; invalid chronology already quarantined | orders |
| On time / late | actual calendar date <= / > promise date among eligible | orders |
| On-time / late rate | corresponding count / eligible; null if zero | fraction |
| Delivered unscorable | delivered status but not eligible | orders |
| Missing promise / actual | delivered with missing corresponding timestamp; counts can overlap | orders |
| Delivery duration median/P90 | delivered with actual; actual minus purchase / 86400 seconds | fractional days |
| Delay median/P90 | late only; actual date minus promise date | calendar days |
| Promised / actual comparison | eligible only; promise timestamp or actual timestamp minus purchase | fractional days |
| Early margin | promise date minus actual date, eligible; negative means late | calendar days |
| Cancellation rate | canceled / all accepted orders in selected cohort; unavailable is separate | fraction |
| Freight per order | sum item freight within each order, then mean across known orders; missing excluded | BRL |
| Dispatch duration | carrier timestamp minus purchase, nonmissing | fractional days |
| Post-dispatch duration | delivered actual minus carrier timestamp, nonmissing | fractional days |
| Total late days | sum calendar delay across late orders | order-days |
| Scenario | (on time + selected late * assumed percentage/100) / eligible | fraction |

Promise end-of-day uses calendar-date comparison, equivalent to actual < next midnight. Source midnight promise values are not literal start-of-day cutoffs. Promised lead time retains the original midnight timestamp; this deliberate distinction is explained in tooltips. All timestamps remain naive source-local civil values; DST/timezone offsets cannot be inferred.

Purchase cohorts describe demand intake and subsequent observed delivery outcomes. Delivery cohorts describe completions, exclude missing actual dates and are not suitable for all-order cancellation comparisons. Dates are inclusive. Recent cohorts may be right-censored. Never compare open orders to today's date.

Filters select one region and optional seller/category membership via EXISTS; intersections can match different items in the same order. Summary denominators remain orders. Category group rows may overlap. Seller scorecards and seller scenarios require exactly one seller. Lanes use one origin state, MULTI or UNKNOWN, plus destination.

Quantiles use DuckDB quantile_cont with linear interpolation; DAX PERCENTILEX.INC excludes blanks explicitly. Medians and stage medians are not additive. Empty counts are zero and undefined rates are null/blank; UI shows an em dash.

Wilson intervals: z=1.95996398454, denominator 1+z²/n; midpoint (p+z²/2n)/denominator; half-width z*sqrt(p(1-p)/n+z²/4n²)/denominator. Clip to [0,1]. Configurable minimum volume defaults to 30; no composite score.

Adjustment: pick the three largest destination states among filtered eligible single-seller orders, use their volume shares as common weights. Every compared seller needs >=5 eligible per state and total >= selected minimum. Weighted on-time rates use those states only; raw rates include all destinations. Display coverage and exclusions. With fewer than three common states no adjusted rate is shown. This standardizes destination mix only, not category, time or other confounders.

Recent seller trend: last 90 purchase days versus preceding 90 anchored at latest purchase in the filtered population. Show both sample sizes. Not a rolling window relative to today.

Pareto: late counts descending; cumulative share of the filtered late population. Category Pareto disabled. Seller shares exclude multi-seller attribution and may not reach 100%. UI displays first 12 loaded segments; subsequent pages are not a full-population cumulative curve.

Action rule: region >=30 eligible and late rate above filtered baseline; sort total late days descending. Each row includes evidence, baseline, owner role, action, limitation and measurable follow-up. No causal finding, predicted improvement or financial ROI.

Scenario: exactly one segment, 0-100%, same eligible denominator. Multiple overlapping category selections cannot be summed. Fractional affected counts are expectations under an assumption.
