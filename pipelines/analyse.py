"""Execute ten SQL investigations and materialize reproducible evidence."""
import json
from pathlib import Path
import pandas as pd
from backend import analytics as a
def main():
    root=a.ROOT; agg=a.AGG
    investigations={
    "01_overall":f"SELECT {agg} FROM fact_order",
    "02_monthly":f"SELECT date_trunc('month',purchase_at) AS month,{agg} FROM fact_order GROUP BY 1 ORDER BY 1",
    "02_weekly":f"SELECT date_trunc('week',purchase_at) AS week,{agg} FROM fact_order GROUP BY 1 ORDER BY 1",
    "03_sellers":f"SELECT single_seller_id AS seller,{agg} FROM fact_order WHERE single_seller_id IS NOT NULL GROUP BY 1 ORDER BY late_count DESC",
    "04_regions":f"SELECT region,{agg} FROM fact_order GROUP BY 1 ORDER BY late_count DESC",
    "05_lanes":f"SELECT lane,{agg} FROM fact_order GROUP BY 1 ORDER BY late_count DESC",
    "06_severity":"SELECT delay_days,count(*) AS orders FROM fact_order WHERE late GROUP BY 1 ORDER BY 1",
    "07_freight":f"SELECT CASE WHEN freight_charged IS NULL THEN 'unknown' WHEN freight_charged<10 THEN '<10 BRL' WHEN freight_charged<25 THEN '10-25 BRL' WHEN freight_charged<50 THEN '25-50 BRL' ELSE '50+ BRL' END AS freight_band,{agg} FROM fact_order GROUP BY 1",
    "08_category":f"SELECT b.category,{agg} FROM fact_order o JOIN bridge_order_category b USING(order_id) GROUP BY 1 ORDER BY late_count DESC",
    "09_status":"SELECT status,count(*) AS orders,count(*) FILTER(WHERE promise_at IS NULL) AS missing_promise,count(*) FILTER(WHERE delivered_at IS NULL) AS missing_actual FROM fact_order GROUP BY 1 ORDER BY orders DESC",
    "10_dispatch":"SELECT region,count(dispatch_days) AS dispatch_n,median(dispatch_days) AS median_dispatch_days,quantile_cont(dispatch_days,0.9) AS p90_dispatch_days,count(post_dispatch_days) AS post_dispatch_n,median(post_dispatch_days) AS median_post_dispatch_days,quantile_cont(post_dispatch_days,0.9) AS p90_post_dispatch_days FROM fact_order GROUP BY 1 ORDER BY post_dispatch_n DESC"}
    comments={"03_sellers":"Single-seller attribution only; descriptive, not seller fault.","05_lanes":"State pairs, not observed carrier routes.","07_freight":"Customer charges, not logistics costs. Unadjusted association.","08_category":"One row per order/category; overlapping category groups are NOT additive.","10_dispatch":"Dispatch is order-level carrier handoff; stage medians need not sum to total median."}
    for name,sql in investigations.items():
        (root/f"sql/{name}.sql").write_text("-- "+comments.get(name,"Accepted order grain; end-of-day promise; historical source-local times.")+"\n"+sql+";\n")
        pd.DataFrame(a.query(sql)).to_csv(root/f"reports/{name}.csv",index=False)
    summary=a.summary(a.Filters()); actions=a.actions(a.Filters())
    (root/"reports/reconciliation.json").write_text(json.dumps(summary,indent=2))
    (root/"reports/actions.json").write_text(json.dumps(actions,indent=2))
    (root/"reports/seller_adjustment.json").write_text(json.dumps(a.sellers(a.Filters(),limit=500),indent=2))
    regions=a.segments(a.Filters(),"region")
    top=regions[0]; lines=[
    "# SupplyScope: executive findings",
    "Historical Olist data; no production deployment or realized business impact is claimed.",
    f"Accepted population: {summary['orders']:,} orders. Eligible delivered population: {summary['eligible']:,}; on time: {summary['on_time_count']:,} ({summary['on_time_rate']:.2%}); late: {summary['late_count']:,} ({summary['late_rate']:.2%}).",
    f"Median delivery duration: {summary['median_delivery_days']:.2f} days; P90: {summary['p90_delivery_days']:.2f}. Among late orders, median delay is {summary['median_delay_days']:.0f} calendar days and P90 is {summary['p90_delay_days']:.0f}.",
    f"Eligible orders have median promised lead time {summary['median_promised_days']:.2f} days versus median actual {summary['median_actual_days']:.2f}; median early margin is {summary['median_early_margin']:.0f} calendar days. High reliability can coexist with generous promises.",
    f"{summary['canceled']:,} cancellations / {summary['orders']:,} accepted orders ({summary['cancellation_rate']:.2%}); {summary['delivered_unscorable']} delivered orders lack an actual timestamp. Freight charged averages BRL {summary['freight_per_order']:.2f} among {summary['freight_known_orders']:,} orders with known accepted items. This is not logistics cost.",
    f"Largest late-order contributor: {top['segment']}, with {top['late_count']:,} late / {top['eligible']:,} eligible ({top['late_rate']:.2%}). Contribution volume alone is not proof of unusually poor reliability.",
    "Evidence: [overall](01_overall.csv), [regions](04_regions.csv), [lanes](05_lanes.csv), [monthly](02_monthly.csv), [dispatch](10_dispatch.csv), [reconciliation](reconciliation.json).",
    "## Prioritized investigations"]
    for i,r in enumerate(actions[:5],1):
        lines.append(f"{i}. **{r['segment']}**: {r['late_count']:,}/{r['eligible']:,} late ({r['late_rate']:.2%}) vs {r['baseline']:.2%} baseline; {r['priority_late_days']:,} total late days. Owner role: {r['owner']}. {r['action']} Follow-up: {r['follow_up_kpi']}")
    lines+=["## Hypotheses and limitations","Handoff delays, destination mix and promise calibration are hypotheses to investigate, not proven causes. Compare within seller/destination/category and inspect source records before a pilot. Quarantine changes the analyzed population. Recent cohorts may be immature. The source lacks carriers, true costs, inventory and a reliable extraction snapshot; an overdue watchlist is therefore omitted. See data_quality.json for exclusions and source checksums."]
    (root/"reports/executive_findings.md").write_text("\n\n".join(lines),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
