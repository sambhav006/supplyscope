# SupplyScope: executive findings

Historical Olist data; no production deployment or realized business impact is claimed.

Accepted population: 99,252 orders. Eligible delivered population: 96,282; on time: 89,750 (93.22%); late: 6,532 (6.78%).

Median delivery duration: 10.23 days; P90: 23.11. Among late orders, median delay is 7 calendar days and P90 is 22.

Eligible orders have median promised lead time 23.23 days versus median actual 10.23; median early margin is 12 calendar days. High reliability can coexist with generous promises.

625 cancellations / 99,252 accepted orders (0.63%); 8 delivered orders lack an actual timestamp. Freight charged averages BRL 22.82 among 98,477 orders with known accepted items. This is not logistics cost.

Largest late-order contributor: SP, with 1,819 late / 40,428 eligible (4.50%). Contribution volume alone is not proof of unusually poor reliability.

Evidence: [overall](01_overall.csv), [regions](04_regions.csv), [lanes](05_lanes.csv), [monthly](02_monthly.csv), [dispatch](10_dispatch.csv), [reconciliation](reconciliation.json).

## Prioritized investigations

1. **RJ**: 1,495/12,330 late (12.12%) vs 6.78% baseline; 20,216 total late days. Owner role: Regional operations lead. Review dispatch handoffs and promise calibration for this destination; validate within seller and category before a pilot. Follow-up: Reduce eligible late rate in the next comparable, fully observed purchase cohort without increasing promised lead time.

2. **BA**: 395/3,252 late (12.15%) vs 6.78% baseline; 4,755 total late days. Owner role: Regional operations lead. Review dispatch handoffs and promise calibration for this destination; validate within seller and category before a pilot. Follow-up: Reduce eligible late rate in the next comparable, fully observed purchase cohort without increasing promised lead time.

3. **CE**: 176/1,278 late (13.77%) vs 6.78% baseline; 2,672 total late days. Owner role: Regional operations lead. Review dispatch handoffs and promise calibration for this destination; validate within seller and category before a pilot. Follow-up: Reduce eligible late rate in the next comparable, fully observed purchase cohort without increasing promised lead time.

4. **SC**: 291/3,534 late (8.23%) vs 6.78% baseline; 2,419 total late days. Owner role: Regional operations lead. Review dispatch handoffs and promise calibration for this destination; validate within seller and category before a pilot. Follow-up: Reduce eligible late rate in the next comparable, fully observed purchase cohort without increasing promised lead time.

5. **ES**: 214/1,989 late (10.76%) vs 6.78% baseline; 2,418 total late days. Owner role: Regional operations lead. Review dispatch handoffs and promise calibration for this destination; validate within seller and category before a pilot. Follow-up: Reduce eligible late rate in the next comparable, fully observed purchase cohort without increasing promised lead time.

## Hypotheses and limitations

Handoff delays, destination mix and promise calibration are hypotheses to investigate, not proven causes. Compare within seller/destination/category and inspect source records before a pilot. Quarantine changes the analyzed population. Recent cohorts may be immature. The source lacks carriers, true costs, inventory and a reliable extraction snapshot; an overdue watchlist is therefore omitted. See data_quality.json for exclusions and source checksums.