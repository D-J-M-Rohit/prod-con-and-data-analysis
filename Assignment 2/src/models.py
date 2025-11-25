# src/models.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class Transaction:
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
        return self.quantity * self.unit_price

    @property
    def is_cancellation(self) -> bool:
        return self.invoice_no.upper().startswith("C")
