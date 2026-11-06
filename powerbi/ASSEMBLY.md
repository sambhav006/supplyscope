# Power BI build package - Desktop validation outstanding

This is a source/build package, not a PBIX or validated PBIP. Desktop was not found in standard Program Files or installed Appx packages. M and DAX have not run in the Power BI engine.

## Windows assembly

1. Run the root pipeline. Open Power BI Desktop; create a blank report.
2. Options > Data Load: disable automatic relationship detection and Auto date/time.
3. Transform Data > New Source > Blank Query > Advanced Editor. Create RootPath from queries/RootPath.m, then LoadTable from queries/LoadTable.m. Disable load for both.
4. Create a blank query for each remaining .m file; name it after the filename and paste the expression. These read D:\SupplyScope\data\processed. Headers are promoted, blanks normalized to null and types explicitly applied using en-US. Preserve identifiers as text. Close & Apply.
5. Create relationships below, all single direction from the one side. Mark dim_date[date] as the date table.
6. Create each calculated table in calculated_tables.dax separately. Create every measure in measures.dax separately (each name = block); measures.json contains descriptions. Rates: 0.0%; days: 0.0; freight: BRL.
7. View > Themes > import theme.json. Build pages from page_layouts.md.
8. Run reconciliation.dax in DAX Query View. Compare expected_totals.json and SQL reports: exact counts, rates/durations within 1e-8. Test SP, seller/category intersections, empty filters and date boundaries against API exports.
9. Save D:\SupplyScope\powerbi\SupplyScope.pbix. Capture screenshots only after validation. Record Desktop version and results in validation.md (currently outstanding).

## Relationships

| One side | Many side | Active |
|---|---|---|
| dim_date.date | fact_order.purchase_date | yes |
| dim_date.date | fact_order.delivery_date | no |
| dim_geography.region | fact_order.region | yes |
| fact_order.order_id | fact_item.order_id | yes |
| fact_order.order_id | fact_payment.order_id | yes |
| fact_order.order_id | fact_review.order_id | yes |
| fact_order.order_id | bridge_order_seller.order_id | yes |
| fact_order.order_id | bridge_order_category.order_id | yes |
| dim_seller.seller_id | bridge_order_seller.seller_id | yes |
| dim_category.category | bridge_order_category.category | yes |

No direct dim_seller-to-order relationship; no bidirectional filtering. The supplied measures apply explicit seller/category order membership using their bridges. Without a seller/category filter, orders without items remain included. Seller and category selections mean independent membership in the same order, not necessarily the same item, matching API semantics.

For seller scorecards apply fact_order[seller_count]=1 as a visual filter for every metric. Use dim_seller rows. Category groups overlap; distinct-order grand totals need not equal row sums.

## Date roles

Purchase cohorts are the default. Delivery-cohort pages must use USERELATIONSHIP wrappers for every measure, not just change the axis caption. Duplicate the supplied delivery-rate pattern for counts and durations; exclude blank delivery dates. That cancellation rate is not the all-order cancellation rate.

## Distinctive features and limitations

DAX includes Wilson intervals, minimum-volume flags, regional Pareto, promise/actual medians, P90 variability, action flags and a single-region scenario. Dynamic adjusted seller comparisons and 90-day trends are implemented in React/API. seller_adjustment_audit.csv is a disconnected, unfiltered snapshot of the first 500 sellers by late volume; weights are in reports/seller_adjustment.json. Keep it on a separately labelled audit page with no slicer interactions.

Official references:
- https://learn.microsoft.com/en-us/powerquery-m/csv-document
- https://learn.microsoft.com/en-us/power-bi/guidance/relationships-active-inactive
- https://learn.microsoft.com/en-us/dax/percentilex-inc-function-dax
