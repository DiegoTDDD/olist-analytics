# Olist E-Commerce Analytics

An end-to-end analytics engineering project on the Brazilian Olist e-commerce dataset. It builds a dimensional model with dbt and DuckDB, then uses it to answer a concrete business question: **how does late delivery affect customer satisfaction, and where does the damage actually happen?**

## Key finding

Customer satisfaction does not decline gradually when an order is late — it collapses. A single day past the promised delivery date is enough to drop the average review score from 4.29 to around 3, and once an order is more than a week late, customers give close to the lowest possible rating.

| Delivery outcome | Orders | Avg. review score |
|---|---:|---:|
| On time or early | 89,448 | 4.29 |
| 1–5 days late | 2,722 | 2.99 |
| 6–15 days late | 2,480 | 1.74 |
| 15+ days late | 1,180 | 1.73 |

The business implication is direct: for Olist, preventing *any* delay matters far more than reducing the size of a delay. Almost all of the reputational damage happens in the first days past the deadline, so operational effort is best spent on hitting the promised date rather than on shortening already-late deliveries.

## Business questions

The dimensional model is built to support three analytical areas, with delivery vs. satisfaction as the anchor:

- **Delivery performance and satisfaction** (anchor) — do late orders receive worse reviews, and how much worse?
- **Customer behavior** — repeat purchase patterns and cohort retention.
- **Seller and category performance** — which sellers and product categories drive value or drag down operations.

## Data model

The project follows a layered dbt architecture and a star schema.

**Staging layer** — one lightly cleaned view per source table: columns renamed to a consistent English convention, types adjusted, and the original dataset's typo (`product_name_lenght`) corrected. No business logic.

**Marts layer** — a star schema:

- `fct_orders` — one row per order, with measures: order value, payment installments, item count, freight, review score, delivery days, delay days, and an `is_delayed` flag.
- `dim_customers` — customer identity and location (preserving both `customer_id` per order and `customer_unique_id` per person).
- `dim_products` — product attributes joined to the English category translation.
- `dim_sellers` — seller identity and location.
- `dim_dates` — a date spine with year, quarter, month, day of week, and weekend flag.

The `delay_days` measure (actual delivery date minus the estimated date) is the metric that links operations to customer satisfaction.

## Tech stack

- **DuckDB** — in-process analytical database
- **dbt** (dbt-core + dbt-duckdb) — transformations, lineage, and modeling
- **Python** — data loading and analysis scripts
- **Git / GitHub** — version control

## Project structure

```
olist-analytics/
├── load_data.py            # Loads the raw CSVs into DuckDB
├── explore.py              # Quick data integrity checks
├── analysis.py             # Delivery vs. satisfaction analysis
├── olist_dbt/
│   └── models/
│       ├── staging/        # Cleaned source views (stg_*)
│       └── marts/          # Dimensional model (fct_*, dim_*)
└── README.md
```

## How to run

The raw data is not versioned (see `.gitignore`). Download the dataset first.

1. **Get the data** — download the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle and place the nine CSV files in `data/raw/`.

2. **Set up the environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   pip install duckdb pandas dbt-core dbt-duckdb
   ```

3. **Load the data into DuckDB**
   ```bash
   python load_data.py
   ```

4. **Build the dimensional model**
   ```bash
   cd olist_dbt
   dbt deps
   dbt run
   ```

5. **Run the analysis**
   ```bash
   python analysis.py
   ```

## Data source

Brazilian E-Commerce Public Dataset by Olist — ~100,000 real, anonymized orders placed between 2016 and 2018, made publicly available on Kaggle.
