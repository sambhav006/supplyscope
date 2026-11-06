# Page layouts and interactions

Canvas 1440 x 900; background #F4F6F4; margins 32; Segoe UI. Header y=0 h=80; slicers y=90 h=75; four KPI cards y=185 h=110; charts y=320 h=280; matrix y=630 h=220. Use labels as well as color.

Global slicers: dim_date.date between (purchase basis), dim_geography.region, dim_seller.seller_id with search, dim_category.category with search. Sync across analytical pages. Reset bookmark restores all filters.

1. Executive: Orders, On Time Rate, Late, P90 Delivery Days cards. Monthly reliability line. Status bars: fact_order.status / Orders. Action matrix: region, Late, Eligible, Late Rate, Region Baseline Late Rate, Total Late Days, Action Flag. Sort total late days descending.
2. Trends: month/week bookmark switches dim_date.year_month/week_start. On Time Rate line; Orders columns. Table Eligible, Median Actual Days, Median Promised Days, P90 Delivery Days, Freight per Order. Mark recent cohorts as possibly immature.
3. Seller scorecards: seller ID, Eligible, On Time Rate, Wilson Lower/Upper, Late, Median/P90 Delay Days, Small Sample. Visual filter seller_count=1. MinimumVolume slicer default 30; flag small samples.
4. Regions & lanes: region and lane matrices with Late, Eligible, Late Rate, Median/P90 Delivery Days. MULTI origin is explicit. These are state pairs, not carrier routes.
5. Delay & promises: destination Pareto combo: Late bars, Region Pareto Cumulative line, percentage axis 0-100, sort Late descending. Category matrix warns overlapping populations; no category Pareto. Promise matrix: Median Promised Days, Median Actual Days, Median Early Margin, On Time Rate.
6. Scenario: disconnected ScenarioRegion single-select; Improvement 0-100; current rate, affected orders, scenario rate. Fixed denominator, no savings, assumption not prediction. Multiple regions disallowed.
7. Trust: source, licence, coverage, pipeline timestamp, quarantines from reports/data_quality.json. Import via Json.Document(File.Contents(RootPath & "\reports\data_quality.json")) and expand records, or copy values with explicit run timestamp. Dataset-wide metadata ignores slicers; Delivered Unscorable and missing-date cards respect filters.
8. Optional adjustment audit: disconnected seller_adjustment_audit.csv; unfiltered snapshot, 500-row limit, no interactions. Use React for interactive adjustment.

Tooltip page 320 x 260: Orders, Eligible, Late, missing dates, Wilson interval. Text: end-of-calendar-day promise, eligible delivered denominator.
Drill-through page: geography/seller/category dimension fields, keep all filters, back button. Show order_id, status, dates, late and delay_days; include Orders measure with visual filter >0 to honor bridge membership (raw columns alone do not propagate seller/category filters back to orders).
Cross-filter within analytical pages; do not cross-highlight. Scenario selector affects scenario cards only. Exclude static trust/audit visuals from interactions. Export active filter text with underlying order table; print Executive to PDF.
