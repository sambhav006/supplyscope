# Data dictionary

Generated from the exported warehouse schema. Full machine-readable types: schema.json. Grains and keys: architecture.md.

## fact_order
| Column | DuckDB type | Meaning |
|---|---|---|
| order_id | VARCHAR | Anonymized order identifier; delivery fact primary key. |
| status | VARCHAR | Source order status; canceled differs from unavailable. |
| region | VARCHAR | Customer destination state abbreviation. |
| purchase_at | TIMESTAMP_NS | Naive source purchase timestamp; required. |
| purchase_date | DATE | Calendar purchase date; active date role. |
| approved_at | TIMESTAMP_NS | Payment approval time; may be missing. |
| dispatched_at | TIMESTAMP_NS | Order-level carrier handoff; no carrier identity. |
| delivered_at | TIMESTAMP_NS | Order-level customer delivery timestamp. |
| delivery_date | DATE | Calendar actual delivery date; inactive BI date role. |
| promise_at | TIMESTAMP_NS | Estimated calendar delivery date, stored at midnight; deadline interpreted end-of-day. |
| item_count | BIGINT | Number of accepted item rows linked to order. |
| seller_count | BIGINT | Distinct accepted sellers on order. |
| single_seller_id | VARCHAR | Seller ID only for exactly one seller, otherwise null. |
| origin | VARCHAR | Unique seller origin state; MULTI for multiple states, UNKNOWN if no accepted items. |
| lane | VARCHAR | Origin-state to destination-state pair, not observed carrier route. |
| freight_charged | DECIMAL(38,2) | Sum of accepted item freight charges, BRL; unknown if no items. |
| eligible | BOOLEAN | Delivered with valid actual and promised timestamps. |
| on_time | BOOLEAN | Eligible and actual date <= promise date; false outside eligible. |
| late | BOOLEAN | Eligible and actual date > promise date; false outside eligible. |
| delivery_days | DOUBLE | Delivered actual minus purchase in fractional days. |
| delay_days | BIGINT | Eligible nonnegative actual-date minus promise-date in calendar days. |
| promised_days | DOUBLE | Promise midnight minus purchase in fractional days. |
| early_margin_days | BIGINT | Promise date minus actual date among eligible; negatives are late. |
| dispatch_days | DOUBLE | Dispatch minus purchase in fractional days. |
| post_dispatch_days | DOUBLE | Delivered actual minus dispatch in fractional days. |
## fact_item
| Column | DuckDB type | Meaning |
|---|---|---|
| order_id | VARCHAR | Anonymized order identifier; delivery fact primary key. |
| order_item_id | BIGINT | Sequence within order; composite key with order_id. |
| product_id | VARCHAR | Anonymized product identifier. |
| seller_id | VARCHAR | Anonymized marketplace seller identifier, not verified supplier. |
| category | VARCHAR | Source category name or unknown; order categories overlap. |
| origin | VARCHAR | Unique seller origin state; MULTI for multiple states, UNKNOWN if no accepted items. |
| price | DECIMAL(18,2) | Item price, BRL; not shipping cost. |
| freight_value | DECIMAL(18,2) | Customer freight charge per item, BRL. |
| shipping_limit_date | TIMESTAMP_NS | Seller shipping deadline; not customer delivery promise. |
## fact_payment
| Column | DuckDB type | Meaning |
|---|---|---|
| order_id | VARCHAR | Anonymized order identifier; delivery fact primary key. |
| payment_sequential | BIGINT | Payment sequence within order. |
| payment_type | VARCHAR | Source payment method; not shipping method. |
| payment_installments | BIGINT | Number of payment installments. |
| payment_value | DOUBLE | Recorded payment amount, BRL; separate fact. |
## bridge_order_seller
| Column | DuckDB type | Meaning |
|---|---|---|
| order_id | VARCHAR | Anonymized order identifier; delivery fact primary key. |
| seller_id | VARCHAR | Anonymized marketplace seller identifier, not verified supplier. |
## bridge_order_category
| Column | DuckDB type | Meaning |
|---|---|---|
| order_id | VARCHAR | Anonymized order identifier; delivery fact primary key. |
| category | VARCHAR | Source category name or unknown; order categories overlap. |
## dim_seller
| Column | DuckDB type | Meaning |
|---|---|---|
| seller_id | VARCHAR | Anonymized marketplace seller identifier, not verified supplier. |
| origin | VARCHAR | Unique seller origin state; MULTI for multiple states, UNKNOWN if no accepted items. |
| seller_city | VARCHAR | Seller origin city source label. |
## dim_category
| Column | DuckDB type | Meaning |
|---|---|---|
| category | VARCHAR | Source category name or unknown; order categories overlap. |
## dim_geography
| Column | DuckDB type | Meaning |
|---|---|---|
| region | VARCHAR | Customer destination state abbreviation. |
## dim_date
| Column | DuckDB type | Meaning |
|---|---|---|
| date | DATE | Contiguous calendar date. |
| year | BIGINT | Calendar year. |
| month | BIGINT | Month number 1-12. |
| year_month | VARCHAR | Sortable YYYY-MM label. |
| week_start | DATE | Monday-start calendar week. |
## fact_review
| Column | DuckDB type | Meaning |
|---|---|---|
| review_id | VARCHAR | Review identifier; not assumed globally unique. |
| order_id | VARCHAR | Anonymized order identifier; delivery fact primary key. |
| review_score | BIGINT | Integer 1-5; optional review-level outcome. |
| review_creation_date | TIMESTAMP_NS | Review creation timestamp. |
| review_answer_timestamp | TIMESTAMP_NS | Review response timestamp. |