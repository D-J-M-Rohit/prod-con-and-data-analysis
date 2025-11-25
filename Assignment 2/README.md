# Retail Data Analysis — Functional Programming Assignment

A compact data analysis app that demonstrates functional programming patterns (map, filter, reduce, lambdas, higher-order functions) over CSV retail sales data using Python.

## Overview

The app reads a retail transactions CSV in the UCI Online Retail II schema, cleans and normalizes the data, then runs analytical queries such as total revenue, revenue by country, monthly trend, top products, top customers, average order value, units sold, weekday sales, and a cancellation summary.
Implementation favors a functional and streaming style with pure transforms and immutable outputs.

## Project Layout

```
retail-analysis-project/
├── data/
│   └── online_retail.csv
├── src/
│   ├── analysis.py
│   ├── io_utils.py
│   ├── models.py
│   └── __init__.py
├── tests/
│   └── test_analysis_small_unit.py    
├── main.py
├── Design_Decisions_and_Assumptions.md
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8+


## Dataset

- Expected CSV columns: `Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country`
- Src: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- Place the file at `data/online_retail.csv` or pass a custom path to `main.py`
Header variants are normalized automatically. For example Invoice maps to InvoiceNo and Price maps to UnitPrice.

## How to Run

From the project root:

```bash
python main.py data/online_retail.csv
```
This will:
- Stream the CSV into Transaction objects
- Build a sales view that excludes cancellations and non-positive quantities
- Print the results for each question in clearly labeled sections
- Limit long lists to the Top 10 by default

## Sample Output

Below is an excerpt of the console output for 
python main.py data/online_retail.csv

```
================================================================================
 TOTAL REVENUE (Sales view)
================================================================================
10,666,702.54

================================================================================
 REVENUE BY COUNTRY (Top 10)
================================================================================
United Kingdom       9,025,222.08
Netherlands          285,446.34
EIRE                 283,453.96
Germany              228,867.14
France               209,733.11
Australia            138,521.31
Spain                61,577.11
Switzerland          57,089.90
Belgium              41,196.34
Sweden               38,378.33

================================================================================
 MONTHLY REVENUE (Top 10 months by revenue)
================================================================================
2011-11  1,509,496.33
2011-10  1,154,979.30
2011-09  1,058,590.17
2010-12  823,746.14
2011-05  770,536.02
2011-06  761,739.90
2011-08  759,138.38
2011-07  719,221.19
2011-03  717,639.36
2011-01  691,364.56

================================================================================
 TOP 10 PRODUCTS BY REVENUE
================================================================================
DOTCOM POSTAGE                           206,248.77
REGENCY CAKESTAND 3 TIER                 174,484.74
PAPER CRAFT , LITTLE BIRDIE              168,469.60
WHITE HANGING HEART T-LIGHT HOLDER       106,292.77
PARTY BUNTING                            99,504.33
JUMBO BAG RED RETROSPOT                  94,340.05
MEDIUM CERAMIC TOP STORAGE JAR           81,700.92
POSTAGE                                  78,119.88
Manual                                   78,112.82
RABBIT NIGHT LIGHT                       66,964.99

================================================================================
 TOP 10 CUSTOMERS BY REVENUE
================================================================================
14646        280,206.02
18102        259,657.30
17450        194,550.79
16446        168,472.50
14911        143,825.06
12415        124,914.53
14156        117,379.63
17511        91,062.38
16029        81,024.84
12346        77,183.60

================================================================================
 AVERAGE ORDER VALUE (Sales view)
================================================================================
534.40

================================================================================
 UNITS SOLD PER PRODUCT (Top 10)
================================================================================
PAPER CRAFT , LITTLE BIRDIE              80995
MEDIUM CERAMIC TOP STORAGE JAR           78033
WORLD WAR 2 GLIDERS ASSTD DESIGNS        55047
JUMBO BAG RED RETROSPOT                  48474
WHITE HANGING HEART T-LIGHT HOLDER       37891
POPCORN HOLDER                           36761
ASSORTED COLOUR BIRD ORNAMENT            36461
PACK OF 72 RETROSPOT CAKE CASES          36419
RABBIT NIGHT LIGHT                       30788
MINI PAINT SET VINTAGE                   26633

================================================================================
 SALES BY DAY OF WEEK
================================================================================
Monday     1,779,575.04
Tuesday    2,178,632.61
Wednesday  1,851,147.81
Thursday   2,203,161.24
Friday     1,840,358.23
Saturday   0.00
Sunday     813,827.61

================================================================================
 CANCELLATION AND RETURNS SUMMARY
================================================================================
TotalCancellations:  5172
CancellationRate:    19.97%
CancelledNetAmount:  -896812.49
CancelledAbsAmount:  896812.49
```
Your numbers may differ if you use a reduced sample or a different file version.

## What the CLI Answers

1. Total revenue in the sales view
2. Revenue by country Top 10
3. Monthly revenue Top 10 months
4. Top products by revenue Top 10
5. Top customers by revenue Top 10
6. Average order value in the sales view
7. Units sold per product Top 10
8. Sales by day of week
9. Cancellation and returns summary based on the full stream

## Functional and Streaming Techniques

* **Generators** for streaming input without loading the full CSV into memory
* **Views as pure filters**

  * `valid_transactions` for the sales view
  * `returns_view` for cancellations and non-positive quantities
* **Map and filter** style loops with dictionary accumulation for group-bys
* **Lambdas** for sorting keys and compact transforms
* **Immutability** of inputs and outputs for each query

## Tests

Run with `unittest`:
```bash
python -m unittest -v tests.test_analysis_small_unit
```
## Sample Output for Unit tests
```
test_avg_order_value (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_avg_order_value) ... ok
test_avg_order_value_empty (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_avg_order_value_empty) ... ok
test_cancellation_rate (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_cancellation_rate) ... ok
test_cancellation_rate_all_cancellations (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_cancellation_rate_all_cancellations) ... ok
test_cancellation_rate_no_data (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_cancellation_rate_no_data) ... ok
test_cancellation_summary_basic (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_cancellation_summary_basic) ... ok
test_cancellation_summary_empty (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_cancellation_summary_empty) ... ok
test_monthly_revenue (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_monthly_revenue) ... ok
test_monthly_revenue_empty (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_monthly_revenue_empty) ... ok
test_returns_view_no_cancellations (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_returns_view_no_cancellations) ... ok
test_returns_view_only_cancellations_and_non_positive (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_returns_view_only_cancellations_and_non_positive) ... ok
test_revenue_by_country (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_revenue_by_country) ... ok
test_revenue_by_country_empty (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_revenue_by_country_empty) ... ok
test_sales_by_weekday_empty (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_sales_by_weekday_empty) ... ok
test_sales_by_weekday_single_day_totals (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_sales_by_weekday_single_day_totals) ... ok
test_top_n_customers_by_revenue (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_top_n_customers_by_revenue) ... ok
test_top_n_customers_with_less_than_n_customers (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_top_n_customers_with_less_than_n_customers) ... ok
test_top_n_customers_with_zero_n (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_top_n_customers_with_zero_n) ... ok
test_top_n_products_by_revenue (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_top_n_products_by_revenue) ... ok
test_top_n_products_with_less_than_n_items (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_top_n_products_with_less_than_n_items) ... ok
test_top_n_products_with_zero_n (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_top_n_products_with_zero_n) ... ok
test_total_revenue (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_total_revenue) ... ok
test_total_revenue_empty (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_total_revenue_empty) ... ok
test_units_sold_per_product (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_units_sold_per_product) ... ok
test_units_sold_per_product_no_description_still_counts (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_units_sold_per_product_no_description_still_counts) ... ok
test_valid_transactions_all_cancellations (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_valid_transactions_all_cancellations) ... ok
test_valid_transactions_filters_cancellations (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_valid_transactions_filters_cancellations) ... ok
test_valid_transactions_filters_zero_quantity_and_price (tests.test_analysis_small_unit.AnalysisSmallUnitTests.test_valid_transactions_filters_zero_quantity_and_price) ... ok

----------------------------------------------------------------------
Ran 28 tests in 0.000s

OK
```

## Notes and Tips

* **Why Saturday can be zero**
  The sales view excludes cancellations and non-positive quantities. In the UCI dataset many Saturday rows are postage or adjustments or are not present due to business hours. If a day aggregates to zero it means no rows in the **sales view** contributed revenue for that weekday.

* **Want all rows regardless of business rules**
  You can adapt the CLI to aggregate directly over the raw stream, or add a flag to switch between the raw stream and the sales view.

* **Reproducibility**
  Results depend on the exact CSV you use. The project normalizes headers and parses multiple date formats to reduce friction.







