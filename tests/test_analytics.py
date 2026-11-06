"""Synthetic fixtures are isolated here; never exported into real-data analysis."""
import json
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend import analytics as a
from pipelines.build import clean
client=TestClient(app)
def test_sql_api_agree():
    api=client.get("/api/summary").json()
    sql=a.query("SELECT "+a.AGG+" FROM fact_order")[0]
    for k,v in sql.items(): assert api[k]==v
def test_all_endpoints():
    for url in ["/api/health","/api/summary","/api/trends?interval=week","/api/sellers?limit=3","/api/segments?group=lane","/api/distributions","/api/options","/api/quality","/api/actions","/api/export?region=AC","/api/export?format=metadata"]:
        assert client.get(url).status_code==200,url
def test_empty_safe():
    s=client.get("/api/summary?region=NO_SUCH_REGION").json()
    assert s["orders"]==0 and s["on_time_rate"] is None and s["cancellation_rate"] is None
    assert client.get("/api/scenario?region=NONE&segment=SP").json()["scenario_rate"] is None
def test_validation_and_injection():
    for url in ["/api/scenario?segment=SP&percent=101","/api/scenario?segment=SP&percent=-1","/api/segments?limit=501","/api/segments?group=bad","/api/summary?start=2018-01-01&end=2017-01-01","/api/summary?start=bad"]:
        assert client.get(url).status_code==422,url
    assert client.get("/api/summary",params={"region":"' OR 1=1 --"}).json()["orders"]==0
def test_multi_item_and_multi_seller_no_inflation():
    total=a.query("SELECT count(*) AS n,count(DISTINCT order_id) AS u FROM fact_order")[0]; assert total["n"]==total["u"]
    row=a.query("SELECT order_id FROM fact_order WHERE seller_count>1 LIMIT 1")[0]
    sellers=a.query("SELECT seller_id FROM bridge_order_seller WHERE order_id=?",[row["order_id"]])
    assert len(sellers)>1
    f=a.Filters(seller=sellers[0]["seller_id"]);p,args=a.population(f)
    assert a.query(f"SELECT count(*) AS n,count(DISTINCT order_id) AS u FROM ({p})",args)[0]["n"]==a.query(f"SELECT count(DISTINCT order_id) AS n FROM ({p})",args)[0]["n"]
def test_scenario_bounds_and_single_population():
    b=a.summary(a.Filters())
    zero=a.scenario(a.Filters(),"region","SP",0); full=a.scenario(a.Filters(),"region","SP",100)
    assert zero["scenario_rate"]==b["on_time_rate"]
    assert full["scenario_rate"]==pytest.approx((b["on_time_count"]+full["segment_late"])/b["eligible"])
    assert full["scenario_rate"]<=1
    assert client.get("/api/scenario?segment=SP,RJ").json()["segment_late"]==0
def test_small_sample_wilson():
    lo,hi=a.wilson(2,2);assert 0<lo<.5 and hi==pytest.approx(1)
    assert a.wilson(0,0)==(None,None)
    result=a.sellers(a.Filters(),minimum=10000,limit=5)
    assert all(r["small_sample"] and r["adjusted_rate"] is None for r in result["rows"])
def test_chronology_quarantine():
    raw=pd.DataFrame([dict(order_id="fixture",customer_id="c",order_status="delivered",order_purchase_timestamp="2018-01-02 00:00:00",order_approved_at=None,order_delivered_carrier_date=None,order_delivered_customer_date="2018-01-01 23:00:00",order_estimated_delivery_date="2018-01-03 00:00:00")],dtype="string")
    good,bad=clean("orders",raw,{})
    assert good.empty and "before_purchase" in bad.iloc[0].reason
def test_calendar_boundary_and_nulls():
    # Exercise the actual build SQL against isolated in-memory source relations.
    import duckdb
    c=duckdb.connect()
    c.execute("""CREATE TABLE stg_orders AS SELECT * FROM (VALUES
    ('same','c','delivered',TIMESTAMP '2018-01-01 10:00:00',NULL::TIMESTAMP,TIMESTAMP '2018-01-01 11:00:00',TIMESTAMP '2018-01-01 23:59:59',TIMESTAMP '2018-01-01'),
    ('late','c','delivered',TIMESTAMP '2018-01-01',NULL::TIMESTAMP,NULL::TIMESTAMP,TIMESTAMP '2018-01-02',TIMESTAMP '2018-01-01'),
    ('no_promise','c','delivered',TIMESTAMP '2018-01-01',NULL::TIMESTAMP,NULL::TIMESTAMP,TIMESTAMP '2018-01-02',NULL::TIMESTAMP),
    ('no_actual','c','delivered',TIMESTAMP '2018-01-01',NULL::TIMESTAMP,NULL::TIMESTAMP,NULL::TIMESTAMP,TIMESTAMP '2018-01-02'),
    ('cancel','c','canceled',TIMESTAMP '2018-01-01',NULL::TIMESTAMP,NULL::TIMESTAMP,NULL::TIMESTAMP,TIMESTAMP '2018-01-02'))
    t(order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date);
    CREATE TABLE stg_customers AS SELECT 'c' customer_id,'SP' customer_state;
    CREATE TABLE stg_sellers AS SELECT 's' seller_id,'RJ' seller_state,'city' seller_city;
    CREATE TABLE stg_products AS SELECT 'p' product_id,'cat' product_category_name;
    CREATE TABLE stg_order_items AS SELECT 'same' order_id,1 order_item_id,'p' product_id,'s' seller_id,10.0 price,1.0 freight_value,TIMESTAMP '2018-01-02' shipping_limit_date;
    INSERT INTO stg_order_items SELECT 'same',2,'p','s',10.0,1.0,TIMESTAMP '2018-01-02';
    CREATE TABLE stg_order_payments AS SELECT 'same' order_id;
    CREATE TABLE stg_order_reviews AS SELECT 'same' order_id;""")
    c.execute((a.ROOT/"sql/build.sql").read_text())
    r=c.execute("SELECT "+a.AGG+" FROM fact_order").fetchdf().iloc[0]
    assert r.orders==5 and r.eligible==2 and r.on_time_count==1 and r.late_count==1
    assert r.delivered_unscorable==2 and r.canceled==1 and r.cancellation_rate==.2
    assert c.execute("SELECT delay_days FROM fact_order WHERE order_id='late'").fetchone()[0]==1
    c.close()
def test_category_membership_distinct_and_nonadditive():
    p,args=a.population(a.Filters(category="cama_mesa_banho"))
    r=a.query(f"SELECT count(*) AS n,count(DISTINCT order_id) AS distinct_n FROM ({p})",args)[0]
    assert r["n"]==r["distinct_n"] and r["n"]>0
    assert a.query("SELECT count(*) AS n FROM (SELECT order_id FROM bridge_order_category GROUP BY order_id HAVING count(*)>1)")[0]["n"]>0
def test_adjustment_uses_disclosed_weights():
    result=a.sellers(a.Filters(),limit=10)
    assert sum(result["weights"].values())==pytest.approx(1)
    for r in result["rows"]:
        if r["adjusted_rate"] is not None:
            expected=0
            for region,weight in result["weights"].items():
                cell=a.query("SELECT count(*) AS n,avg(CAST(on_time AS INTEGER)) AS rate FROM fact_order WHERE eligible AND single_seller_id=? AND region=?",[r["segment"],region])[0]
                assert cell["n"]>=5
                expected+=weight*cell["rate"]
            assert r["adjusted_rate"]==pytest.approx(expected)
def test_duplicate_and_foreign_key_quarantine():
    raw=pd.DataFrame([dict(order_id="o",order_item_id="1",product_id="p",seller_id="s",shipping_limit_date="2018-01-01 00:00:00",price="5",freight_value="1")]*2,dtype="string")
    good,bad=clean("order_items",raw,{"orders":pd.DataFrame({"order_id":["o"]})})
    assert len(good)==1 and "duplicate_key" in bad.iloc[0].reason
    good,bad=clean("order_items",raw,{"orders":pd.DataFrame({"order_id":["other"]})})
    assert good.empty and bad.reason.str.contains("orphan").all()
def test_export_population_and_metadata():
    import csv,io
    response=client.get("/api/export?region=AC")
    rows=list(csv.DictReader(io.StringIO(response.text)))
    summary=client.get("/api/summary?region=AC").json()
    assert len(rows)==summary["orders"] and len(set(r["order_id"] for r in rows))==len(rows)
    meta=client.get("/api/export?format=metadata&region=AC").json()
    assert meta["filters"]["region"]=="AC" and "sha256" in meta["lineage"]["files"][0]
