from __future__ import annotations

"""
Retail Analytics Package

Public API for the retail analysis assignment.
"""

from .models import Transaction
from .analysis import (
    valid_transactions,
    returns_view,
    total_revenue,
    revenue_by_country,
    monthly_revenue,
    top_n_products_by_revenue,
    top_n_customers_by_revenue,
    sales_by_weekday,
    cancellation_summary,
    avg_order_value,
    units_sold_per_product,
    cancellation_rate,
)
from .io_utils import load_transactions

__all__ = [
    "Transaction",
    "valid_transactions",
    "returns_view",
    "total_revenue",
    "revenue_by_country",
    "monthly_revenue",
    "top_n_products_by_revenue",
    "top_n_customers_by_revenue",
    "sales_by_weekday",
    "cancellation_summary",
    "avg_order_value",
    "units_sold_per_product",
    "cancellation_rate",
    "load_transactions",
]
