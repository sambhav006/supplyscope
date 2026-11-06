"""Schema-controlled staging, quarantine and SQL warehouse build."""
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import duckdb
ROOT=Path(__file__).resolve().parents[1]
SCHEMAS={
"orders":{"order_id":"string","customer_id":"string","order_status":"string","order_purchase_timestamp":"date","order_approved_at":"date","order_delivered_carrier_date":"date","order_delivered_customer_date":"date","order_estimated_delivery_date":"date"},
"customers":{"customer_id":"string","customer_unique_id":"string","customer_zip_code_prefix":"string","customer_city":"string","customer_state":"string"},
"sellers":{"seller_id":"string","seller_zip_code_prefix":"string","seller_city":"string","seller_state":"string"},
"products":{"product_id":"string","product_category_name":"string"},
"order_items":{"order_id":"string","order_item_id":"number","product_id":"string","seller_id":"string","shipping_limit_date":"date","price":"number","freight_value":"number"},
"order_payments":{"order_id":"string","payment_sequential":"number","payment_type":"string","payment_installments":"number","payment_value":"number"},
"order_reviews":{"review_id":"string","order_id":"string","review_score":"number","review_creation_date":"date","review_answer_timestamp":"date"}}
KEYS={"orders":["order_id"],"customers":["customer_id"],"sellers":["seller_id"],"products":["product_id"],"order_items":["order_id","order_item_id"],"order_payments":["order_id","payment_sequential"]}
def clean(name,raw,parents):
    schema=SCHEMAS[name]
    missing=set(schema)-set(raw.columns)
    if missing: raise ValueError(f"{name}: missing fields {missing}")
    df=raw[list(schema)].copy(); reasons=pd.Series("",index=df.index)
    def flag(mask,reason):
        reasons.loc[mask.fillna(False)] += reason+";"
    for c,t in schema.items():
        if t=="date":
            df[c]=pd.to_datetime(df[c],format="%Y-%m-%d %H:%M:%S",errors="coerce")
        elif t=="number": df[c]=pd.to_numeric(df[c],errors="coerce")
        if t!="string": flag(raw[c].notna() & df[c].isna(),"invalid_"+c)
    keys=KEYS.get(name)
    if keys:
        flag(df[keys].isna().any(axis=1),"missing_key")
        flag(df.duplicated(keys,keep="first"),"duplicate_key")
    else: flag(df.duplicated(keep="first"),"exact_duplicate")
    if name=="orders":
        p="order_purchase_timestamp"
        flag(df[p].isna(),"missing_purchase")
        for c in ["order_approved_at","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]:
            flag(df[c]<df[p],"before_purchase_"+c)
        flag(df.order_delivered_customer_date < df.order_delivered_carrier_date,"delivery_before_dispatch")
        flag(~df.order_status.isin(["delivered","shipped","canceled","unavailable","invoiced","processing","approved","created"]),"unknown_status")
    if name in ("order_items","order_payments"):
        for c in (["price","freight_value"] if name=="order_items" else ["payment_value"]):
            flag(df[c].isna() | (df[c]<0),"invalid_"+c)
    if name=="order_reviews": flag(~df.review_score.between(1,5),"invalid_score")
    for col,parent in [("customer_id","customers"),("order_id","orders"),("seller_id","sellers"),("product_id","products")]:
        if col in df and parent in parents and parent!=name:
            flag(~df[col].isin(parents[parent][col]),"orphan_"+col)
    bad=df[reasons!=""].copy(); bad["reason"]=reasons[reasons!=""]
    return df[reasons==""].copy(),bad
def main():
    frames={}; quality={}
    for name in ["customers","sellers","products","orders","order_items","order_payments","order_reviews"]:
        raw=pd.read_csv(ROOT/f"data/raw/olist_{name}_dataset.csv",dtype="string")
        good,bad=clean(name,raw,frames); frames[name]=good
        good.to_csv(ROOT/f"data/staging/{name}.csv",index=False)
        bad.to_csv(ROOT/f"data/quarantine/{name}.csv",index=False)
        quality[name]={"raw":len(raw),"accepted":len(good),"quarantined":len(bad),"nulls":{c:int(v) for c,v in good.isna().sum().items()},"reasons":bad.reason.value_counts().to_dict()}
    con=duckdb.connect(str(ROOT/"data/supplyscope.duckdb"))
    con.execute("BEGIN")
    for name,frame in frames.items():
        con.register("incoming",frame); con.execute(f"CREATE OR REPLACE TABLE stg_{name} AS SELECT * FROM incoming"); con.unregister("incoming")
    con.execute((ROOT/"sql/build.sql").read_text())
    assert con.execute("SELECT count(*)=count(DISTINCT order_id) FROM fact_order").fetchone()[0]
    assert con.execute("SELECT count(*) FROM fact_order").fetchone()[0]==len(frames["orders"])
    tables=["fact_order","fact_item","fact_payment","bridge_order_seller","bridge_order_category","dim_seller","dim_category","dim_geography","dim_date","fact_review"]
    dictionary={}
    for table in tables:
        df=con.execute(f"SELECT * FROM {table}").df()
        df.to_csv(ROOT/f"data/processed/{table}.csv",index=False)
        dictionary[table]=[{"column":r[0],"type":r[1]} for r in con.execute(f"DESCRIBE {table}").fetchall()]
    con.execute("COMMIT")
    coverage=con.execute("SELECT min(purchase_at),max(purchase_at),max(delivered_at) FROM fact_order").fetchone()
    meta={"last_pipeline_run_utc":datetime.now(timezone.utc).isoformat(),"coverage":{"purchase_start":str(coverage[0]),"purchase_end":str(coverage[1]),"last_actual_delivery":str(coverage[2])},"quality":quality,"quarantined_rows":sum(x["quarantined"] for x in quality.values()),"source":json.loads((ROOT/"data/raw/manifest.json").read_text()),"snapshot":"Unknown extraction timestamp; no credible historical open-order watchlist. Latest event is not a status-history snapshot.","watchlist_supported":False,"timezone":"Naive source-local civil times; no timezone conversion; exact timezone undocumented.","checks":{"order_grain_unique":True,"accepted_order_count_preserved":True},"build_sql_sha256":hashlib.sha256((ROOT/"sql/build.sql").read_bytes()).hexdigest()}
    (ROOT/"reports/data_quality.json").write_text(json.dumps(meta,indent=2))
    (ROOT/"docs/schema.json").write_text(json.dumps(dictionary,indent=2))
    print(json.dumps({"coverage":meta["coverage"],"quality":{k:{j:v for j,v in q.items() if j in ["raw","accepted","quarantined"]} for k,q in quality.items()}},indent=2))
    con.close()
if __name__=="__main__": main()
