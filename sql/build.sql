-- Each aggregate is reduced to order grain BEFORE joining to the order fact.
CREATE OR REPLACE TABLE dim_seller AS SELECT seller_id, seller_state AS origin, seller_city FROM stg_sellers;
CREATE OR REPLACE TABLE dim_category AS SELECT DISTINCT coalesce(product_category_name,'unknown') AS category FROM stg_products;
CREATE OR REPLACE TABLE dim_geography AS SELECT DISTINCT customer_state AS region FROM stg_customers;
CREATE OR REPLACE TABLE fact_item AS
SELECT i.order_id,i.order_item_id,i.product_id,i.seller_id,
coalesce(p.product_category_name,'unknown') AS category,s.origin,
CAST(i.price AS DECIMAL(18,2)) AS price,CAST(i.freight_value AS DECIMAL(18,2)) AS freight_value,i.shipping_limit_date
FROM stg_order_items i JOIN stg_products p USING(product_id) JOIN dim_seller s USING(seller_id);
CREATE OR REPLACE TABLE bridge_order_seller AS SELECT DISTINCT order_id,seller_id FROM fact_item;
CREATE OR REPLACE TABLE bridge_order_category AS SELECT DISTINCT order_id,category FROM fact_item;
CREATE OR REPLACE TABLE fact_payment AS SELECT * FROM stg_order_payments;
-- Review records are retained separately; never join raw reviews into delivery aggregates.
CREATE OR REPLACE TABLE fact_review AS SELECT * FROM stg_order_reviews;
CREATE OR REPLACE TABLE fact_order AS
WITH items AS (
 SELECT order_id,count(*) AS item_count,count(DISTINCT seller_id) AS seller_count,
 CASE WHEN count(DISTINCT seller_id)=1 THEN min(seller_id) END AS single_seller_id,
 CASE WHEN count(DISTINCT origin)=1 THEN min(origin) ELSE 'MULTI' END AS origin,
 sum(freight_value) AS freight_charged FROM fact_item GROUP BY order_id
), base AS (
 SELECT o.order_id, o.order_status AS status,c.customer_state AS region,
 o.order_purchase_timestamp AS purchase_at,CAST(o.order_purchase_timestamp AS DATE) AS purchase_date,
 o.order_approved_at AS approved_at,o.order_delivered_carrier_date AS dispatched_at,
 o.order_delivered_customer_date AS delivered_at,CAST(o.order_delivered_customer_date AS DATE) AS delivery_date,
 o.order_estimated_delivery_date AS promise_at,
 coalesce(i.item_count,0) AS item_count,coalesce(i.seller_count,0) AS seller_count,
 i.single_seller_id,coalesce(i.origin,'UNKNOWN') AS origin,
 coalesce(i.origin,'UNKNOWN') || ' -> ' || c.customer_state AS lane,i.freight_charged,
 (o.order_status='delivered' AND o.order_delivered_customer_date IS NOT NULL
 AND o.order_estimated_delivery_date IS NOT NULL) AS eligible
 FROM stg_orders o JOIN stg_customers c USING(customer_id) LEFT JOIN items i USING(order_id)
)
SELECT *,
 CASE WHEN eligible THEN CAST(delivered_at AS DATE)<=CAST(promise_at AS DATE) ELSE false END AS on_time,
 CASE WHEN eligible THEN CAST(delivered_at AS DATE)>CAST(promise_at AS DATE) ELSE false END AS late,
 CASE WHEN status='delivered' AND delivered_at IS NOT NULL THEN epoch(delivered_at-purchase_at)/86400 END AS delivery_days,
 CASE WHEN eligible THEN greatest(date_diff('day',CAST(promise_at AS DATE),CAST(delivered_at AS DATE)),0) END AS delay_days,
 epoch(promise_at-purchase_at)/86400 AS promised_days,
 CASE WHEN eligible THEN date_diff('day',CAST(delivered_at AS DATE),CAST(promise_at AS DATE)) END AS early_margin_days,
 epoch(dispatched_at-purchase_at)/86400 AS dispatch_days,
 CASE WHEN status='delivered' THEN epoch(delivered_at-dispatched_at)/86400 END AS post_dispatch_days
FROM base;
CREATE OR REPLACE TABLE dim_date AS
SELECT CAST(d AS DATE) AS date,year(d) AS year,month(d) AS month,strftime(d,'%Y-%m') AS year_month,
CAST(date_trunc('week',d) AS DATE) AS week_start
FROM generate_series((SELECT min(purchase_date) FROM fact_order),
(SELECT greatest(max(purchase_date),max(delivery_date),max(CAST(promise_at AS DATE))) FROM fact_order),INTERVAL 1 DAY) t(d);
