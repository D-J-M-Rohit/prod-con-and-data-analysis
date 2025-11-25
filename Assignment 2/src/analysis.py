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
    for t in records:
        if (not t.is_cancellation) and t.quantity > 0 and t.unit_price > 0.0:
            yield t

def returns_view(records: Iterable[Transaction]) -> Iterator[Transaction]:
    for t in records:
        if t.is_cancellation or t.quantity <= 0:
            yield t

# -----------------------------
# Aggregations
# -----------------------------
def total_revenue(records: Iterable[Transaction]) -> float:
    return sum(t.line_total for t in valid_transactions(records))

def revenue_by_country(records: Iterable[Transaction]) -> Dict[str, float]:
    agg: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        agg[t.country] += t.line_total
    return {k: round(v, 2) for k, v in agg.items()}

def monthly_revenue(records: Iterable[Transaction]) -> Dict[str, float]:
    agg: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        key = f"{t.invoice_date.year:04d}-{t.invoice_date.month:02d}"
        agg[key] += t.line_total
    return {k: round(v, 2) for k, v in agg.items()}

def _product_key(t: Transaction) -> str:
    return (t.description or t.stock_code).strip()

def top_n_products_by_revenue(records: Iterable[Transaction], n: int = 10) -> List[Tuple[str, float]]:
    if n <= 0:
        return []
    agg: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        agg[_product_key(t)] += t.line_total
    ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return [(name, round(amount, 2)) for name, amount in ranked[:n]]

def top_n_customers_by_revenue(records: Iterable[Transaction], n: int = 10) -> List[Tuple[str, float]]:
    if n <= 0:
        return []
    agg: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        if t.customer_id:
            agg[t.customer_id] += t.line_total
    ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return [(cust, round(amount, 2)) for cust, amount in ranked[:n]]

def sales_by_weekday(records: Iterable[Transaction]) -> Dict[str, float]:
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    agg: Dict[str, float] = {d: 0.0 for d in order}
    for t in valid_transactions(records):
        day = t.invoice_date.strftime("%A")
        agg.setdefault(day, 0.0)
        agg[day] += t.line_total
    return {k: round(v, 2) for k, v in agg.items()}

def cancellation_summary(records: Iterable[Transaction]) -> Dict[str, float | int]:
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
    Average order value across the sales view.
    Computes per-invoice totals first, then averages them.
    """
    per_invoice: Dict[str, float] = defaultdict(float)
    for t in valid_transactions(records):
        per_invoice[t.invoice_no] += t.line_total
    if not per_invoice:
        return 0.0
    return sum(per_invoice.values()) / len(per_invoice)


def units_sold_per_product(records: Iterable[Transaction]) -> Dict[str, int]:
    """
    Units sold per product across the sales view.
    Uses Description when available, otherwise falls back to StockCode.
    """
    out: Dict[str, int] = defaultdict(int)
    for t in valid_transactions(records):
        name = (t.description or t.stock_code).strip()
        out[name] += t.quantity
    return dict(out)

def cancellation_rate(records: Iterable[Transaction]) -> float:
    """
    Percentage of cancelled value over gross value.
    Gross is sum of absolute line totals across all rows.
    Cancelled value uses rows where invoice is cancelled or quantity is non-positive.
    """
    gross = 0.0
    cancelled = 0.0
    for t in records:
        lt_abs = abs(t.line_total)
        gross += lt_abs
        if t.is_cancellation or t.quantity <= 0:
            cancelled += lt_abs
    return (cancelled / gross * 100.0) if gross else 0.0