# Three-minute portfolio demo

0:00-0:30 — Open Executive overview. Explain the question: where do delivery promises fail and where should operations investigate? Clarify historical marketplace sellers, not suppliers or carriers.

0:30-1:00 — Read eligible denominator and exclusions. Show 93.22% on time and 6,532 late orders from generated evidence. Contrast SP volume with RJ's above-baseline rate. Open the action queue evidence and owner/follow-up details.

1:00-1:30 — Drill into RJ, inspect promise margins and P90 variability. Switch category and explain overlapping order membership. Return to sellers; show Wilson interval, volume flag, raw versus adjusted rate and destination coverage.

1:30-2:00 — Open scenario, select RJ and assume 25% of late orders become on time. Explain fixed eligible denominator, fractional expected counts, no prediction or savings. Export filtered CSV and metadata.

2:00-2:30 — Open Data trust. Explain chronology quarantine, source checksums, absent carrier/cost fields and why the watchlist is omitted. Show SQL and the one-order fact, separate payment/item facts and bridges.

2:30-3:00 — Open Power BI assembly package: typed M, one-to-many relationships, DAX filter scope and reconciliation totals. State clearly that Desktop/DAX validation remains manual. Close on a proposed investigation, not claimed impact.

# Interview talking points

- Grain: count orders before joining details; aggregation and EXISTS prevent fanout.
- SQL: shared row flags and aggregate contract avoid separate frontend definitions; quantile_cont matches inclusive percentiles.
- pandas: explicit schema conversion, reason-coded quarantine and foreign-key propagation improve trust without silently imputing operational dates.
- Power Query: configurable local root, UTF-8 CSV, promoted headers, blanks-to-null and explicit locale/type conversion.
- DAX: measure filter context versus calculated columns; bridges require explicit membership rather than bidirectional relationships; USERELATIONSHIP changes date role.
- Uncertainty: a perfect two-order record has wide Wilson bounds. Thresholds are visible, not a hidden score.
- Adjustment: direct standardization with common destination weights needs comparable support; expose coverage; remaining confounding remains.
- Promise calibration: apparent reliability can reflect generous promises. Do not tighten promises based solely on median early arrival.
- Causality: order-level timestamps cannot prove seller or carrier fault, especially on multi-seller orders.
- Reproducibility: pinned dependencies, source commit/checksums, transactional warehouse tables, generated findings and actual UI tests.
- Tradeoffs: local DuckDB is explainable and fast at this scale; rebuilds require stopping the Windows server; no unnecessary cloud architecture.
