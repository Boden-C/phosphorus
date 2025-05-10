from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    isbn: str
    title: str
    authors: List[str]


@dataclass(frozen=True)
class Loan:
    loan_id: str
    isbn: str
    card_id: str
    date_out: Optional[date]
    due_date: Optional[date]
    date_in: Optional[date]
    fine_amt: Decimal = Decimal("0.00")
    paid: bool = False


@dataclass(frozen=True)
class Borrower:
    card_id: str
    ssn: str
    bname: str
    address: str
    phone: str


def parse_date(val) -> Optional[date]:
    """Parse a value into a date object or None."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    return datetime.strptime(str(val), "%Y-%m-%d").date()


def parse_authors(author_str: str) -> List[str]:
    """Parse a delimited author string into a list of author names."""
    if author_str and author_str != "None":
        return author_str.split("\u001f")
    return []
