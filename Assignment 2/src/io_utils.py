# src/io_utils.py
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from .models import Transaction

HEADER_MAP = {
    "invoice": "InvoiceNo",
    "invoiceno": "InvoiceNo",
    "stockcode": "StockCode",
    "description": "Description",
    "quantity": "Quantity",
    "invoicedate": "InvoiceDate",
    "price": "UnitPrice",
    "unitprice": "UnitPrice",
    "customer id": "CustomerID",
    "customerid": "CustomerID",
    "country": "Country",
}

DATE_FORMATS = [
    "%m/%d/%y %H:%M",
    "%m/%d/%Y %H:%M",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
]

def _parse_date(raw: str) -> Optional[datetime]:
    v = (raw or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None

def _norm_header(name: str) -> str:
    return HEADER_MAP.get(name.strip().lower(), name.strip())

def _opt_str(val: str | None) -> Optional[str]:
    if val is None:
        return None
    v = val.strip()
    return v or None

def load_transactions(csv_path: str | Path, encoding: str = "ISO-8859-1") -> Iterator[Transaction]:
    path = Path(csv_path)
    with path.open(newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [_norm_header(h) for h in (reader.fieldnames or [])]

        for row in reader:
            try:
                quantity = int(row["Quantity"])
                unit_price = float(row["UnitPrice"])
            except Exception:
                continue

            invoice_date = _parse_date(row.get("InvoiceDate", ""))
            if invoice_date is None:
                continue

            invoice_no = (row.get("InvoiceNo") or "").strip()
            stock_code = (row.get("StockCode") or "").strip()
            country = (row.get("Country") or "").strip()
            if not invoice_no or not stock_code or not country:
                continue

            yield Transaction(
                invoice_no=invoice_no,
                stock_code=stock_code,
                description=_opt_str(row.get("Description")),
                quantity=quantity,
                invoice_date=invoice_date,
                unit_price=unit_price,
                customer_id=_opt_str(row.get("CustomerID")),
                country=country,
            )
