# src/io_utils.py
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from .models import Transaction

# Maps various messy CSV header variants to normalized canonical names.
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

# Set of date formats observed in the Online Retail datasets.
DATE_FORMATS = [
    "%m/%d/%y %H:%M",
    "%m/%d/%Y %H:%M",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
]


def _parse_date(raw: str) -> Optional[datetime]:
    """
    Attempt to parse a raw date string using known formats.

    Args:
        raw: Raw date field from CSV.

    Returns:
        Parsed datetime if successful, or None if no format matches.
    """
    v = (raw or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


def _norm_header(name: str) -> str:
    """
    Normalize a header name from the CSV to its canonical field name.

    Args:
        name: Raw CSV column header.

    Returns:
        Canonical header name if known, otherwise the cleaned original.
    """
    return HEADER_MAP.get(name.strip().lower(), name.strip())


def _opt_str(val: str | None) -> Optional[str]:
    """
    Clean optional string fields.

    Args:
        val: Raw value from the CSV which may be None or whitespace.

    Returns:
        Trimmed string or None if empty.
    """
    if val is None:
        return None
    v = val.strip()
    return v or None


def load_transactions(csv_path: str | Path, encoding: str = "ISO-8859-1") -> Iterator[Transaction]:
    """
    Stream transactions from a Retail CSV file.

    This function performs:
        - Header normalization.
        - Type conversion for quantity and unit price.
        - Flexible date parsing.
        - Required-field validation.
        - Optional field cleaning.

    Args:
        csv_path: Path to the CSV file.
        encoding: File encoding used when reading the CSV.

    Yields:
        Transaction objects constructed from valid rows.

    Notes:
        Rows with invalid numeric fields, missing required fields, or
        unparseable dates are skipped silently to keep streaming robust.
    """
    path = Path(csv_path)
    with path.open(newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)

        # Normalize CSV headers so downstream code always sees canonical names.
        reader.fieldnames = [_norm_header(h) for h in (reader.fieldnames or [])]

        for row in reader:
            # Parse basic numeric fields; skip row if invalid.
            try:
                quantity = int(row["Quantity"])
                unit_price = float(row["UnitPrice"])
            except Exception:
                continue

            # Parse date; skip row if unparseable.
            invoice_date = _parse_date(row.get("InvoiceDate", ""))
            if invoice_date is None:
                continue

            # Required fields: invoice_no, stock_code, country.
            invoice_no = (row.get("InvoiceNo") or "").strip()
            stock_code = (row.get("StockCode") or "").strip()
            country = (row.get("Country") or "").strip()
            if not invoice_no or not stock_code or not country:
                continue

            # Construct an immutable Transaction instance.
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
