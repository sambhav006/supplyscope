import csv,io,json
from typing import Annotated,Literal
from fastapi import FastAPI,Query,HTTPException,Depends
from datetime import date
from pydantic import ValidationError
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from backend import analytics as a
app=FastAPI(title="SupplyScope",version="1.0.0",description="Historical Olist delivery analysis. Inclusive dates; existential seller/category filters preserve order grain.")
app.add_middleware(CORSMiddleware,allow_origins=["http://127.0.0.1:5173","http://localhost:5173"],allow_methods=["GET"],allow_headers=["*"])
def filter_dependency(start:date|None=None,end:date|None=None,basis:Literal["purchase","delivery"]="purchase",region:str|None=Query(None,max_length=100),seller:str|None=Query(None,max_length=100),category:str|None=Query(None,max_length=100)):
    try: return a.Filters(start=start,end=end,basis=basis,region=region,seller=seller,category=category)
    except ValidationError: raise HTTPException(422,"Invalid date range: start must be on or before end")
F=Annotated[a.Filters,Depends(filter_dependency)]
Group=Literal["region","lane","seller","category"]
@app.get("/api/health")
def health():
    return {"status":"ok","orders":a.query("SELECT count(*) AS n FROM fact_order")[0]["n"]}
@app.get("/api/summary")
def summary(f:F): return a.summary(f)
@app.get("/api/trends")
def trends(f:F,interval:Literal["month","week"]="month"): return a.trends(f,interval)
@app.get("/api/segments")
def segments(f:F,group:Group="region",minimum:int=Query(30,ge=1,le=10000),limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=100000)): return a.segments(f,group,minimum,limit,offset)
@app.get("/api/sellers")
def sellers(f:F,minimum:int=Query(30,ge=1,le=10000),limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=100000)): return a.sellers(f,minimum,limit,offset)
@app.get("/api/distributions")
def distributions(f:F): return a.distributions(f)
@app.get("/api/scenario")
def scenario(f:F,segment:str=Query(max_length=100),group:Group="region",percent:float=Query(25,ge=0,le=100)): return a.scenario(f,group,segment,percent)
@app.get("/api/actions")
def actions(f:F): return a.actions(f)
@app.get("/api/quality")
def quality(): return json.loads((a.ROOT/"reports/data_quality.json").read_text())
@app.get("/api/options")
def options():
    return {name:[r["v"] for r in a.query(f"SELECT DISTINCT {col} AS v FROM {table} ORDER BY 1")] for name,table,col in [("regions","dim_geography","region"),("sellers","dim_seller","seller_id"),("categories","dim_category","category")]}
@app.get("/api/export")
def export(f:F,format:Literal["csv","metadata"]="csv"):
    if format=="metadata":
        return {"filters":f.model_dump(mode="json"),"grain":"one row per accepted order","definitions":"Eligible = delivered status with valid actual and promise dates. Promise is end of calendar day. Durations in 24h days; delay in calendar days. Freight charged in BRL, not logistics cost.","lineage":quality()["source"]}
    p,args=a.population(f); rows=a.query(p+" ORDER BY order_id",args)
    cols=list(rows[0]) if rows else ["order_id","status","eligible","on_time","late"]
    out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=cols); writer.writeheader()
    for row in rows:
        # Prevent spreadsheet formula execution when importing exports.
        writer.writerow({k:("'"+v if isinstance(v,str) and v.startswith(("=","+","-","@")) else v) for k,v in row.items()})
    return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=supplyscope-investigation.csv","X-Metric-Definitions":"See /api/export?format=metadata with identical filters","X-Active-Filters":json.dumps(f.model_dump(mode="json"))})
