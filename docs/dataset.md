# Source evaluation and capability matrix

Evaluated 2026-11-04.

- Selected: Olist Brazilian E-Commerce Public Dataset, https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce. Olist and collaborators; licence CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). Noncommercial use with attribution and share-alike; do not imply a commercial data licence.
- Accessible mirror: https://github.com/anggid/Brazilian-E-Commerce-Public-Dataset-by-Olist. Acquisition resolves main once, pins the full commit in data/raw/manifest.json and downloads raw.githubusercontent.com/<repo>/<commit>/<file>. Every downloaded URL, byte count and SHA-256 is recorded. This is a third-party copy of Olist, not an independently certified official checksum.
- Alternative: UCI Online Retail, https://archive.ics.uci.edu/dataset/352/online+retail, has transaction dates/products/quantities but lacks promised and actual delivery timestamps. Rejected for delivery reliability.
- Official local-file path: acquire --local D:\SupplyScope\data\incoming. A user-provided official export requires no credentials in this application.
- No geolocation file is acquired: state-level pairs suffice, and no geographic map is claimed. Category names remain source Portuguese labels. Reviews are acquired, typed and retained separately; free-text review content is excluded.

Seven acquired tables: orders, items, customers, sellers, products, payments and reviews. Exact raw/accepted counts and observed date coverage are generated in reports/data_quality.json. Raw purchases span 2016-09-04 through 2018-10-17; these are historical events, not a current service feed. Source extraction date and historical status changes are unavailable. File acquisition date is not a business snapshot.

| Capability | Observed field(s) | Supported interpretation / limit |
|---|---|---|
| Order identifiers/status | order_id, order_status | Accepted orders and state distribution; no status event history |
| Purchase/approval | order_purchase_timestamp, order_approved_at | Local civil times, timezone unspecified |
| Dispatch | order_delivered_carrier_date | Order-level carrier handoff timestamp; no carrier identity |
| Promise | order_estimated_delivery_date | Calendar-date deadline; end-of-day convention |
| Actual | order_delivered_customer_date | Order-level delivery; cannot isolate a seller's fault |
| Seller | seller_id | Marketplace seller, not verified supplier |
| Origin | seller_state, seller_city | MULTI when more than one origin state |
| Destination | customer_state, customer_city | State-level performance; no observed route geometry |
| Carrier / shipping method | absent | Omitted |
| Freight charged | order_items.freight_value | Sum across accepted items once per order; BRL, not actual logistics cost |
| Categories | product_category_name | Order/category bridge; multi-category populations overlap |
| Reviews | review_score | Optional review fact, potentially multiple reviews per order; no fanout into delivery metrics |
| Inventory / procurement cost | absent | Omitted |
| Historical overdue watchlist | status and dates, but no credible as-of snapshot | Omitted; max event date is not sufficient evidence of status as of that date |

Checksums support repeatability of the chosen mirror, not authentication against the publisher's unavailable hashes. Source files are excluded from Git because of size and licence handling; retain the manifest and attribution when sharing derived work.
