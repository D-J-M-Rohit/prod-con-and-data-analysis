# src/models.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    """
    Immutable data model representing a single retail transaction record.

    Fields:
        invoice_no: Unique invoice identifier. Cancellation invoices typically start with "C".
        stock_code: Product identifier.
        description: Optional human-readable product description.
        quantity: Number of units purchased (negative for returns in some datasets).
        invoice_date: Timestamp of the transaction.
        unit_price: Price per individual unit.
        customer_id: Optional identifier; some transactions may lack this.
        country: Country of the customer or transaction origin.

    Notes:
        - Instances are frozen to maintain immutability once created.
        - Provides convenience properties for computing totals and detecting cancellations.
    """

    invoice_no: str
    stock_code: str
    description: Optional[str]
    quantity: int
    invoice_date: datetime
    unit_price: float
    customer_id: Optional[str]
    country: str

    @property
    def line_total(self) -> float:
        """
        Compute the monetary total for this line item.

        Returns:
            float: quantity × unit_price.
        """
        return self.quantity * self.unit_price

    @property
    def is_cancellation(self) -> bool:
        """
        Determine whether this invoice represents a cancellation.

        Returns:
            bool: True if the invoice number begins with "C" (case-insensitive).
        """
        return self.invoice_no.upper().startswith("C")
