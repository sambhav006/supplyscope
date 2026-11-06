# Architecture, lineage and grains

The project is a local analytical application: no authentication, microservices or external model service. FastAPI opens DuckDB read-only per request. Vite proxies /api in development; analytics calculations live server-side.

    Public pinned CSV mirror / local import
        -> data/raw + manifest (SHA-256, URLs, acquisition timestamp)
        -> pandas explicit schemas and typed conversion
        -> data/staging + data/quarantine (reason codes)
        -> SQL dimensional build -> data/supplyscope.duckdb
        -> ten processed CSV tables -> Power Query -> Power BI (manual assembly)
        -> shared aggregate SQL -> FastAPI -> React
        -> executable investigations -> reports and findings

See schema.json for every exported field/type and data_dictionary.md for descriptions.

| Table | Grain / key |
|---|---|
| fact_order | one accepted order / order_id |
| fact_item | one accepted line unit / order_id + order_item_id |
| fact_payment | one payment sequence / order_id + payment_sequential |
| fact_review | one accepted review record; review_id may repeat, no assumed unique review key |
| bridge_order_seller | one distinct order/seller |
| bridge_order_category | one distinct order/category |
| dim_seller | one seller |
| dim_category | one category label including unknown |
| dim_geography | one destination state |
| dim_date | one calendar date |

Order freight and seller counts are grouped before joining into orders. Customers and products are validated parent dimensions. No raw item/payment/review fanout can inflate order delivery counts. Seller bridge filtering uses EXISTS. Seller-specific attribution uses single_seller_id only.

## ER diagram

~~~mermaid
erDiagram
 dim_date ||--o{ fact_order : purchase_date_active
 dim_geography ||--o{ fact_order : destination
 fact_order ||--o{ fact_item : contains
 fact_order ||--o{ fact_payment : paid_by
 fact_order ||--o{ fact_review : reviewed
 fact_order ||--o{ bridge_order_seller : membership
 fact_order ||--o{ bridge_order_category : membership
 dim_seller ||--o{ bridge_order_seller : seller
 dim_category ||--o{ bridge_order_category : category
~~~

Delivery-date relationship is inactive in Power BI; all relationships are one-to-many with single-direction filters. Explicit DAX membership implements seller/category filtering without ambiguous bidirectional paths.

## Validation and quarantine

Required columns checked against schemas. IDs read as strings; numeric/date conversion errors, missing keys, duplicate keys after first, orphans, unknown status, negative price/freight/payment and invalid chronology are quarantined. Orders require purchase time. Approval/dispatch/actual/promise cannot precede purchase; actual cannot precede dispatch. Missing actual/promise remains accepted and explicitly unscorable. Source timestamps have second precision.

Quarantine propagates to dependent facts via foreign-key checks; counts across tables are rows, not unique orders. Exact review duplicates are rejected; repeated review IDs are not assumed invalid. First occurrence of a duplicate primary key is retained; all later occurrences are quarantined for inspection. Shipping-limit dates are parsed but not used as customer promises.

Database rebuild is transactional for SQL tables. Rebuild staging/exports in place, so stop the API and do not read partially written CSVs during rebuild. Re-running against unchanged raw files reproduces aggregates; pipeline timestamps change. Raw files are never overwritten automatically. Acquisition refuses changed checksums. Raw validation metadata and build SQL hash are recorded in reports/data_quality.json.

## API

GET /api/health, /summary, /trends (month/week), /sellers, /segments (region/lane/seller/category), /distributions, /scenario, /actions, /quality, /options, /export (csv/metadata). /docs is generated OpenAPI documentation. Inclusive start/end, basis=purchase|delivery, optional region/seller/category. Minimum 1-10000; limit 1-500, offset 0-100000. All user data values are bound parameters; identifiers use enumerated allowlists. Date ranges and scenario bounds return HTTP 422 when invalid.

CSV is order-grain and formula-safe; metadata companion contains active filters, definitions and source lineage. The read-only API binds loopback; no public hosting or sensitive credentials are needed.

Monetary item price and freight use DECIMAL(18,2); order freight sums use DECIMAL(38,2). This prevents binary floating-point aggregation drift across rebuilds. Staging preserves original parsed source numbers.
