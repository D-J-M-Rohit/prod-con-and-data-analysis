from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from src.analysis import (
    avg_order_value,
    cancellation_rate,
    monthly_revenue,
    revenue_by_country,
    top_n_customers_by_revenue,
    top_n_products_by_revenue,
    total_revenue,
    units_sold_per_product,
    valid_transactions,
    sales_by_weekday,
    cancellation_summary,
)
from src.io_utils import load_transactions
from src.models import Transaction

TOP_N = 10  # fixed top size

def header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Online Retail CSV analysis using functional and streaming Python."
    )
    parser.add_argument("csv", type=Path, help="Path to Online Retail CSV (e.g., data/online_retail.csv)")
    args = parser.parse_args()

    raw_iter = load_transactions(args.csv)
    valid_list: List[Transaction] = list(valid_transactions(raw_iter))

    header("TOTAL REVENUE (Sales view)")
    print(f"{total_revenue(valid_list):,.2f}")

    header(f"REVENUE BY COUNTRY (Top {TOP_N})")
    by_country = revenue_by_country(valid_list)
    for country, amt in sorted(by_country.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]:
        print(f"{country:20s} {amt:,.2f}")

    header(f"MONTHLY REVENUE (Top {TOP_N} months by revenue)")
    by_month = monthly_revenue(valid_list)
    for month, amt in sorted(by_month.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]:
        print(f"{month}  {amt:,.2f}")

    header(f"TOP {TOP_N} PRODUCTS BY REVENUE")
    for name, amt in top_n_products_by_revenue(valid_list, n=TOP_N):
        print(f"{name[:40]:40s} {amt:,.2f}")

    header(f"TOP {TOP_N} CUSTOMERS BY REVENUE")
    for cust, amt in top_n_customers_by_revenue(valid_list, n=TOP_N):
        print(f"{str(cust)[:12]:12s} {amt:,.2f}")

    header("AVERAGE ORDER VALUE (Sales view)")
    print(f"{avg_order_value(valid_list):,.2f}")

    header(f"UNITS SOLD PER PRODUCT (Top {TOP_N})")
    units_by_product = units_sold_per_product(valid_list)
    for name, units in sorted(units_by_product.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]:
        print(f"{name[:40]:40s} {units}")

    header("SALES BY DAY OF WEEK")
    weekday_totals = sales_by_weekday(valid_list)
    for day in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
        print(f"{day:10s} {weekday_totals[day]:,.2f}")

    header("CANCELLATION AND RETURNS SUMMARY")
    raw_again = load_transactions(args.csv)
    summary = cancellation_summary(raw_again)
    for k in ["TotalCancellations", "CancellationRate", "CancelledNetAmount", "CancelledAbsAmount"]:
        val = summary[k]
        if k == "CancellationRate":
            print(f"{k+':':20s} {val:.2f}%")
        else:
            print(f"{k+':':20s} {val}")


if __name__ == "__main__":
    main()
