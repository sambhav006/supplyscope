"""Read-only, order-grain analytics. All user values are bound parameters."""
import os,json,math
from pathlib import Path
from datetime import date
from typing import Literal
import duckdb
from pydantic import BaseModel,Field,model_validator
ROOT=Path(__file__).resolve().parents[1]
DB=os.environ.get("SUPPLYSCOPE_DB",str(ROOT/"data/supplyscope.duckdb"))
AGG=(ROOT/"sql/metrics.sql").read_text()
class Filters(BaseModel):
    start:date|None=None
    end:date|None=None
    basis:Literal["purchase","delivery"]="purchase"
    region:str|None=Field(None,max_length=100)
    seller:str|None=Field(None,max_length=100)
    category:str|None=Field(None,max_length=100)
    @model_validator(mode="after")
    def valid_range(self):
        if self.start and self.end and self.start>self.end: raise ValueError("start must be on or before end")
        return self
def query(sql,args=None):
    with duckdb.connect(DB,read_only=True) as c:
        result=c.execute(sql,args or []); names=[d[0] for d in result.description]
        return [dict(zip(names,row)) for row in result.fetchall()]
def population(f):
    clauses=["1=1"]; args=[]
    # Delivery basis explicitly excludes orders without an actual delivery timestamp.
    col="purchase_date" if f.basis=="purchase" else "delivery_date"
    if f.basis=="delivery": clauses.append("delivery_date IS NOT NULL")
    for value,op in [(f.start,">="),(f.end,"<=")]:
        if value: clauses.append(f"{col} {op} ?"); args.append(value)
    if f.region: clauses.append("region=?"); args.append(f.region)
    if f.seller:
        clauses.append("EXISTS(SELECT 1 FROM bridge_order_seller b WHERE b.order_id=o.order_id AND b.seller_id=?)"); args.append(f.seller)
    if f.category:
        clauses.append("EXISTS(SELECT 1 FROM bridge_order_category b WHERE b.order_id=o.order_id AND b.category=?)"); args.append(f.category)
    return "SELECT o.* FROM fact_order o WHERE "+" AND ".join(clauses),args
def summary(f):
    p,a=population(f); result=query(f"SELECT {AGG} FROM ({p})",a)[0]
    result["status_distribution"]=query(f"SELECT status,count(*) AS orders FROM ({p}) GROUP BY status ORDER BY orders DESC",a)
    result["filters"]=f.model_dump(mode="json")
    return result
def wilson(k,n):
    if not n: return None,None
    z=1.95996398454; p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den; half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0,mid-half),min(1,mid+half)
GROUPS={"region":"region","lane":"lane","seller":"single_seller_id","category":"category"}
def segments(f,group="region",minimum=30,limit=100,offset=0):
    p,a=population(f); col=GROUPS[group]
    if group=="category":
        p=f"SELECT x.*,b.category FROM ({p}) x JOIN bridge_order_category b USING(order_id)"
    condition="WHERE single_seller_id IS NOT NULL" if group=="seller" else ""
    rows=query(f"SELECT {col} AS segment,{AGG} FROM ({p}) {condition} GROUP BY {col} ORDER BY late_count DESC,orders DESC,segment LIMIT ? OFFSET ?",a+[limit,offset])
    baseline=summary(f)
    for r in rows:
        r["ci_low"],r["ci_high"]=wilson(r["on_time_count"],r["eligible"])
        r["small_sample"]=r["eligible"]<minimum
        r["baseline_late_rate"]=baseline["late_rate"]
        r["late_share"]=r["late_count"]/baseline["late_count"] if baseline["late_count"] else None
    return rows
def trends(f,interval="month"):
    p,a=population(f); col="purchase_at" if f.basis=="purchase" else "delivered_at"
    return query(f"SELECT CAST(date_trunc('{interval}',{col}) AS DATE) AS period,{AGG} FROM ({p}) GROUP BY 1 ORDER BY 1",a)
def sellers(f,minimum=30,limit=100,offset=0):
    rows=segments(f,"seller",minimum,limit,offset); p,a=population(f)
    # Latest 90-day vs previous 90-day purchase cohorts within active filters.
    recent=query(f"""WITH p AS ({p}), anchor AS (SELECT max(purchase_at) AS t FROM p)
    SELECT single_seller_id AS seller,
    avg(CAST(on_time AS INT)) FILTER(WHERE eligible AND purchase_at>t-INTERVAL 90 DAY) AS recent_rate,
    count(*) FILTER(WHERE eligible AND purchase_at>t-INTERVAL 90 DAY) AS recent_n,
    avg(CAST(on_time AS INT)) FILTER(WHERE eligible AND purchase_at<=t-INTERVAL 90 DAY AND purchase_at>t-INTERVAL 180 DAY) AS prior_rate,
    count(*) FILTER(WHERE eligible AND purchase_at<=t-INTERVAL 90 DAY AND purchase_at>t-INTERVAL 180 DAY) AS prior_n
    FROM p CROSS JOIN anchor WHERE single_seller_id IS NOT NULL GROUP BY 1""",a)
    lookup={r["seller"]:r for r in recent}
    for r in rows: r.update(lookup.get(r["segment"],{}))
    # Direct standardization: same top 3 destination regions, same weights for every qualifying seller.
    strata=query(f"""SELECT region,count(*) AS n FROM ({p}) WHERE eligible AND single_seller_id IS NOT NULL GROUP BY region ORDER BY n DESC,region LIMIT 3""",a)
    total=sum(r["n"] for r in strata); weights={r["region"]:r["n"]/total for r in strata} if total else {}
    cells=query(f"""SELECT single_seller_id AS seller,region,count(*) AS n,avg(CAST(on_time AS INT)) AS rate
    FROM ({p}) WHERE eligible AND single_seller_id IS NOT NULL GROUP BY 1,2""",a)
    cells={(r["seller"],r["region"]):r for r in cells}
    for r in rows:
        selected=[cells.get((r["segment"],region)) for region in weights]
        valid=len(selected)==3 and all(x and x["n"]>=5 for x in selected) and not r["small_sample"]
        r["adjusted_rate"]=sum(cells[(r["segment"],region)]["rate"]*weight for region,weight in weights.items()) if valid else None
        r["adjustment_exclusion"]=None if valid else "Requires 3 shared regions, >=5 eligible orders per region and minimum total volume"
        r["comparison_coverage"]=sum(x["n"] for x in selected if x)/r["eligible"] if r["eligible"] else 0
    return {"rows":rows,"weights":weights,"minimum_per_stratum":5,"excluded_multi_seller_orders":query(f"SELECT count(*) AS n FROM ({p}) WHERE seller_count>1",a)[0]["n"],"method":"Direct destination standardization; top three regions of filtered single-seller eligible population. Raw rate uses all destinations. Not causal."}
def distributions(f):
    p,a=population(f)
    return query(f"""SELECT CASE WHEN NOT late THEN 'On time' WHEN delay_days<=3 THEN '1-3 days' WHEN delay_days<=7 THEN '4-7 days' WHEN delay_days<=14 THEN '8-14 days' ELSE '15+ days' END AS bucket,count(*) AS orders
    FROM ({p}) WHERE eligible GROUP BY 1 ORDER BY min(delay_days)""",a)
def scenario(f,group,segment,percent):
    p,a=population(f)
    if group=="category": condition="EXISTS(SELECT 1 FROM bridge_order_category b WHERE b.order_id=p.order_id AND category=?)"
    else: condition=GROUPS[group]+"=?"
    b=summary(f); n=query(f"SELECT count(*) AS n FROM ({p}) p WHERE late AND {condition}",a+[segment])[0]["n"]
    affected=n*percent/100
    return {"eligible":b["eligible"],"baseline_rate":b["on_time_rate"],"segment_late":n,"affected_orders":affected,"scenario_rate":(b["on_time_count"]+affected)/b["eligible"] if b["eligible"] else None,"assumed_percent":percent,"label":"Scenario, not prediction. Expected affected orders can be fractional. Exactly one segment; no overlapping sums."}
def actions(f):
    base=summary(f); rows=segments(f,"region",30,100)
    ranked=sorted([r for r in rows if not r["small_sample"] and r["late_rate"] is not None and r["late_rate"]>(base["late_rate"] or 0)],key=lambda r:r["total_delay_days"] or 0,reverse=True)
    return [{"segment":r["segment"],"late_count":r["late_count"],"eligible":r["eligible"],"late_rate":r["late_rate"],"baseline":base["late_rate"],"priority_late_days":r["total_delay_days"],"action":"Review dispatch handoffs and promise calibration for this destination; validate within seller and category before a pilot.","owner":"Regional operations lead","limitation":"Descriptive association; no carrier, cost or capacity data.","follow_up_kpi":"Reduce eligible late rate in the next comparable, fully observed purchase cohort without increasing promised lead time."} for r in ranked[:8]]
