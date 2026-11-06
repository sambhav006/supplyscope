"""Generate typed M queries and described DAX; engine validation remains manual."""
import json
from backend import analytics as a
def main():
    out=a.ROOT/"powerbi"; (out/"queries").mkdir(exist_ok=True)
    schema=json.loads((a.ROOT/"docs/schema.json").read_text())
    (out/"queries/RootPath.m").write_text('"D:\\SupplyScope" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n')
    (out/"queries/LoadTable.m").write_text("""(file as text, types as list) as table =>
let
 Source = Csv.Document(File.Contents(RootPath & "\\data\\processed\\" & file & ".csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
 Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
 EmptyToNull = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
 Typed = Table.TransformColumnTypes(EmptyToNull, types, "en-US")
in Typed
""")
    for table,cols in schema.items():
        types=[]
        for c in cols:
            t=c["type"];m="type datetime" if "TIMESTAMP" in t else "type date" if t=="DATE" else "type logical" if t=="BOOLEAN" else "Int64.Type" if "INT" in t else "type number" if t in ["DOUBLE","FLOAT"] or t.startswith("DECIMAL") else "type text"
            types.append('{"'+c["column"]+'", '+m+'}')
        (out/f"queries/{table}.m").write_text(f'LoadTable("{table}", {{'+", ".join(types)+'})\n')
    scope="""VAR SellerOrders = VALUES(bridge_order_seller[order_id])
VAR CategoryOrders = VALUES(bridge_order_category[order_id])
VAR Scope = FILTER(fact_order,
 (NOT ISFILTERED(dim_seller) || fact_order[order_id] IN SellerOrders) &&
 (NOT ISFILTERED(dim_category) || fact_order[order_id] IN CategoryOrders))
"""
    measures={}
    def add(name,expr,desc,scoped=True): measures[name]={"expression":scope+"RETURN "+expr if scoped else expr,"description":desc}
    add("Orders","COALESCE(COUNTROWS(Scope),0)","Accepted orders, distinct order grain; cancellation denominator.")
    add("Eligible","COALESCE(COUNTROWS(FILTER(Scope,fact_order[eligible])),0)","Delivered with valid actual and promised dates.")
    add("On Time","COALESCE(COUNTROWS(FILTER(Scope,fact_order[on_time])),0)","Actual calendar date <= promise calendar date.")
    add("Late","COALESCE(COUNTROWS(FILTER(Scope,fact_order[late])),0)","Actual calendar date > promise calendar date.")
    add("On Time Rate","DIVIDE([On Time],[Eligible])","Same denominator as late rate.",False)
    add("Late Rate","DIVIDE([Late],[Eligible])","Eligible delivered late fraction.",False)
    add("Delivered",'COALESCE(COUNTROWS(FILTER(Scope,fact_order[status]="delivered")),0)',"Delivered including unscorable.")
    add("Delivered Unscorable",'COALESCE(COUNTROWS(FILTER(Scope,fact_order[status]="delivered" && NOT fact_order[eligible])),0)',"Delivered excluded from rate.")
    add("Delivered Missing Promise",'COALESCE(COUNTROWS(FILTER(Scope,fact_order[status]="delivered" && ISBLANK(fact_order[promise_at]))),0)',"May overlap missing actual.")
    add("Delivered Missing Actual",'COALESCE(COUNTROWS(FILTER(Scope,fact_order[status]="delivered" && ISBLANK(fact_order[delivered_at]))),0)',"May overlap missing promise.")
    add("Canceled",'COALESCE(COUNTROWS(FILTER(Scope,fact_order[status]="canceled")),0)',"Canceled status, not unavailable.")
    add("Cancellation Rate","DIVIDE([Canceled],[Orders])","Canceled / accepted orders in cohort.",False)
    for name,col,elig in [("Delivery Days","delivery_days",False),("Delay Days","delay_days",True),("Promised Days","promised_days",True),("Actual Days","delivery_days",True),("Early Margin","early_margin_days",True),("Dispatch Days","dispatch_days",False),("Post Dispatch Days","post_dispatch_days",False)]:
        condition=f"NOT ISBLANK(fact_order[{col}])"+(" && fact_order[late]" if name=="Delay Days" else " && fact_order[eligible]" if elig else "")
        add("Median "+name,f"MEDIANX(FILTER(Scope,{condition}),fact_order[{col}])","Late delay uses late only; promise comparisons use eligible; blanks excluded.")
        if name in ["Delivery Days","Delay Days"]:
            add("P90 "+name,f"PERCENTILEX.INC(FILTER(Scope,{condition}),fact_order[{col}],0.9)","Inclusive interpolated percentile, matching quantile_cont.")
    add("Freight per Order","AVERAGEX(FILTER(Scope,NOT ISBLANK(fact_order[freight_charged])),fact_order[freight_charged])","BRL charged to customer, not logistics cost.")
    add("Freight Known Orders","COALESCE(COUNTROWS(FILTER(Scope,NOT ISBLANK(fact_order[freight_charged]))),0)","Freight average denominator.")
    add("Total Late Days","SUMX(FILTER(Scope,fact_order[late]),fact_order[delay_days])","Volume x severity priority, not money.")
    for side,sign in [("Lower","-"),("Upper","+")]:
        add("Wilson "+side,f"""VAR N=[Eligible]
VAR P=[On Time Rate]
VAR Z=1.95996398454
VAR Den=1+DIVIDE(Z*Z,N)
VAR Mid=DIVIDE(P+DIVIDE(Z*Z,2*N),Den)
VAR Half=DIVIDE(Z*SQRT(DIVIDE(P*(1-P),N)+DIVIDE(Z*Z,4*N*N)),Den)
RETURN IF(N>0,Mid {sign} Half)""","95% binomial Wilson interval; not selection-bias protection.",False)
    add("Small Sample",'IF([Eligible]<SELECTEDVALUE(MinimumVolume[Value],30),"Small sample","Meets threshold")',"Configurable minimum volume.",False)
    add("On Time Rate Delivery Cohort",'CALCULATE([On Time Rate],USERELATIONSHIP(dim_date[date],fact_order[delivery_date]))',"Activates delivery date role.",False)
    add("Seller Eligible",'CALCULATE([Eligible],KEEPFILTERS(fact_order[seller_count]=1))',"Single-seller scorecards.",False)
    add("Seller On Time Rate",'CALCULATE([On Time Rate],KEEPFILTERS(fact_order[seller_count]=1))',"Avoid attribution to multi-seller orders.",False)
    add("Scenario Affected Orders",'VAR Region=SELECTEDVALUE(ScenarioRegion[region])\nVAR Improvement=SELECTEDVALUE(Improvement[Value],0)/100\nRETURN IF(NOT ISBLANK(Region),CALCULATE([Late],KEEPFILTERS(TREATAS({Region},fact_order[region])))*Improvement)',"One disconnected region, intersects filters.",False)
    add("Scenario On Time Rate",'IF(HASONEVALUE(ScenarioRegion[region]),DIVIDE([On Time]+[Scenario Affected Orders],[Eligible]))',"Scenario not prediction.",False)
    add("Region Baseline Late Rate",'CALCULATE([Late Rate],ALLSELECTED(dim_geography[region]))',"Retains slicers, removes region row context.",False)
    add("Region Late Share",'DIVIDE([Late],CALCULATE([Late],ALLSELECTED(dim_geography[region])))',"Non-overlapping destination contribution.",False)
    add("Region Pareto Cumulative",'VAR CurrentLate=[Late]\nVAR Regions=ADDCOLUMNS(ALLSELECTED(dim_geography[region]),"N",[Late])\nRETURN DIVIDE(SUMX(FILTER(Regions,[N]>=CurrentLate),[N]),SUMX(Regions,[N]))',"Sort Late descending; ties share endpoint.",False)
    add("Action Flag",'IF([Eligible]>=30 && [Late Rate]>[Region Baseline Late Rate],"Investigate dispatch and promise calibration","Monitor")',"Sort Total Late Days descending; owner Regional operations lead.",False)
    (out/"measures.json").write_text(json.dumps(measures,indent=2))
    (out/"measures.dax").write_text("\n\n".join("// "+v["description"]+"\n"+k+" =\n"+v["expression"] for k,v in measures.items()))
    (out/"calculated_tables.dax").write_text("""// Create each table separately. No relationships for these controls.
MinimumVolume = GENERATESERIES(1,1000,1)
Improvement = GENERATESERIES(0,100,5)
ScenarioRegion = DISTINCT(dim_geography[region])
// dim_date is imported and contiguous; mark as date table.
""")
    (out/"theme.json").write_text(json.dumps({"name":"SupplyScope Forest and Sand","dataColors":["#26704D","#D49B55","#6E8B77","#AEBE9F","#765B3D","#294D46"],"background":"#F4F6F4","foreground":"#203B34","tableAccent":"#26704D","textClasses":{"title":{"fontFace":"Segoe UI","fontSize":18},"label":{"fontFace":"Segoe UI","fontSize":11}}},indent=2))
    import pandas as pd
    pd.DataFrame(a.sellers(a.Filters(),limit=500)["rows"]).to_csv(out/"seller_adjustment_audit.csv",index=False)
    (out/"expected_totals.json").write_text((a.ROOT/"reports/reconciliation.json").read_text())
    print(f"Generated {len(schema)} typed table queries and {len(measures)} described measures. Desktop/DAX NOT executed.")
if __name__=="__main__":main()
