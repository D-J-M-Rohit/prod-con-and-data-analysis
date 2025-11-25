# src/analysis.py
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Iterator, List, Tuple

from .models import Transaction

__all__ = [
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
]

# -----------------------------
# Views (generators)
# -----------------------------

def valid_transactions(records: Iterable[Transaction]) -> Iterator[Transaction]:
    """
    Yield transactions considered valid sales.

    Criteria:
        - Not a cancellation.
        - quantity > 0
        - unit_price > 0

    Returns:
        Iterator of clean sale transactions.
    """
    for t in records:
        if (not t.is_cancellation) and t.quantity > 0 and t.unit_price > 0.0:
            yield t


def returns_view(records: Iterable[Transaction]) -> Iterator[Transaction]:
    """
    Yield transactions considered returns or cancellations.

    Criteria:
        - Invoice starts with "C", or
        - quantity <= 0 (dataset often encodes returns this way)
    """
    for t in records:
        if t.is_cancellation or t.quantity <= 0:
            yield t


# -----------------------------
# Aggregations
# -----------------------------

def total_revenue(records: Iterable[Transaction]) -> float:
    """
    Compute total revenue from valid sales.

    Returns:
        Sum of line totals for all valid transactions.
    """
    return sum(t.line_total for t in valid_transactions(records))


def revenue_by_country(records: Iterable[Transaction]) -> Dict[str, float]:
    """
    Revenue aggregated per country.

    Returns:
        Dict mapping country -> rounded revenue.
    """
    agg: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        agg[t.country] += t.line_total
    return {k: round(v, 2) for k, v in agg.items()}


def monthly_revenue(records: Iterable[Transaction]) -> Dict[str, float]:
    """
    Revenue aggregated per month.

    Key format:
        "YYYY-MM"
    """
    agg: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        key = f"{t.invoice_date.year:04d}-{t.invoice_date.month:02d}"
        agg[key] += t.line_total
    return {k: round(v, 2) for k, v in agg.items()}


def _product_key(t: Transaction) -> str:
    """
    Determine the display key for product grouping.

    Uses description when present, otherwise falls back to stock code.
    """
    return (t.description or t.stock_code).strip()


def top_n_products_by_revenue(records: Iterable[Transaction], n: int = 10) -> List[Tuple[str, float]]:
    """
    Top N products ranked by revenue.

    Args:
        n: Number of products to return.

    Returns:
        List of (product_name, revenue) sorted by revenue descending.
    """
    if n <= 0:
        return []
    agg: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        agg[_product_key(t)] += t.line_total
    ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return [(name, round(amount, 2)) for name, amount in ranked[:n]]


def top_n_customers_by_revenue(records: Iterable[Transaction], n: int = 10) -> List[Tuple[str, float]]:
    """
    Top N customers by revenue.

    Only customers with non-null IDs are counted.
    """
    if n <= 0:
        return []
    agg: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        if t.customer_id:
            agg[t.customer_id] += t.line_total
    ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return [(cust, round(amount, 2)) for cust, amount in ranked[:n]]


def sales_by_weekday(records: Iterable[Transaction]) -> Dict[str, float]:
    """
    Aggregate revenue by weekday.

    Returns:
        Dict mapping weekday -> revenue.
        Always includes all 7 days (Mon–Sun).
    """
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    agg: Dict[str, float] = {d: 0.0 for d in order}

    for t in valid_transactions(records):
        day = t.invoice_date.strftime("%A")
        agg.setdefault(day, 0.0)
        agg[day] += t.line_total

    return {k: round(v, 2) for k, v in agg.items()}


def cancellation_summary(records: Iterable[Transaction]) -> Dict[str, float | int]:
    """
    Produce summary metrics for cancellations and returns.

    Metrics:
        - TotalCancellations: number of cancelled or returned invoices.
        - CancellationRate: percentage of invoices cancelled.
        - CancelledNetAmount: signed sum of cancelled line totals.
        - CancelledAbsAmount: absolute value of cancellations.

    Notes:
        Uses invoice-level tracking to detect cancellation groups.
    """
    all_invoices = set()
    cancelled_invoices = set()
    net_amount = 0.0

    for t in records:
        all_invoices.add(t.invoice_no)
        if t.is_cancellation or t.quantity <= 0:
            cancelled_invoices.add(t.invoice_no)
            net_amount += t.line_total

    total_invoices = len(all_invoices)
    total_cancels = len(cancelled_invoices)
    rate = (total_cancels / total_invoices * 100.0) if total_invoices else 0.0

    return {
        "TotalCancellations": int(total_cancels),
        "CancellationRate": round(rate, 2),
        "CancelledNetAmount": round(net_amount, 2),
        "CancelledAbsAmount": round(abs(net_amount), 2),
    }


def avg_order_value(records: Iterable[Transaction]) -> float:
    """
    Compute average order value (AOV).

    Steps:
        - Aggregate revenue per invoice.
        - Compute mean revenue across invoices.
    """
    per_invoice: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        per_invoice[t.invoice_no] += t.line_total
    if not per_invoice:
        return 0.0
    return sum(per_invoice.values()) / len(per_invoice)


def units_sold_per_product(records: Iterable[Transaction]) -> Dict[str, int]:
    """
    Count total units sold per product.

    Uses description when available, stock code otherwise.
    """
    out: Dict[str, int] = defaultdict(int)
    for t in valid_transactions(records):
        name = (t.description or t.stock_code).strip()
        out[name] += t.quantity
    return dict(out)


def cancellation_rate(records: Iterable[Transaction]) -> float:
    """
    Compute percentage of cancelled value relative to total value.

    Definitions:
        - gross: sum of absolute line totals across all transactions.
        - cancelled: absolute line totals for cancellation/return rows.

    Returns:
        Percent of cancelled value, or 0 if no gross value exists.
    """
    gross = 0.0
    cancelled = 0.0

    for t in records:
        lt_abs = abs(t.line_total)
        gross += lt_abs
        if t.is_cancellation or t.quantity <= 0:
            cancelled += lt_abs

    return (cancelled / gross * 100.0) if gross else 0.0
