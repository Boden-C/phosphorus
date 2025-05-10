"""
Query parser for structured search strings in the library management system.

This module provides a Query class that can parse search strings with keywords
for filtering and sorting library data like books, borrowers, loans, and fines.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional, Set, List, ClassVar, TypeVar, Generic


class OrderDirection(Enum):
    """Enum for sort order direction."""

    ASCENDING = auto()
    DESCENDING = auto()


class LoanStatus(Enum):
    """Enum for loan status filtering."""

    ACTIVE = auto()  # Books currently checked out
    RETURNED = auto()  # Books that have been returned


class FineStatus(Enum):
    """Enum for fine status filtering."""

    OWED = auto()  # Unpaid fines
    PAID = auto()  # Paid fines


class DueStatus(Enum):
    """Enum for due date filtering."""

    PAST = auto()  # Books with past due date
    FUTURE = auto()  # Books with future due date


T = TypeVar("T")


@dataclass
class Results(Generic[T]):
    """
    Generic container for paginated results.

    Attributes:
        items: List of result items
        total: Total number of items across all pages
        page_limit: Maximum items per page (None for unlimited)
        current_page: Current page number (1-indexed)
    """

    items: List[T]
    total: int
    page_limit: Optional[int]
    current_page: int


@dataclass
class Query:
    """
    Parses and represents structured search queries with keywords for library data.

    Keywords:
        borrower:, user: - Filter by borrower name
        card: - Filter by card ID
        phone: - Filter by phone number
        isbn: - Filter by book ISBN
        title: - Filter by book title
        author: - Filter by book author
        loan_id: - Filter by loan ID
        sort: - Sort results (isbn, borrower, card, title, author, etc.)
        order: - Sort direction (asc, ascending, desc, descending)
        loan_is: - Loan status (active, returned)
        fine_is: - Fine status (owed, paid)
        due: - Due date status (past, future)
        available: - Book availability (true, false)
        limit: - Maximum results to return
        page: - Page number for pagination

    Any text without a keyword is treated as a general search term.
    """

    # Original query string
    raw_query: str = ""

    # General search term (without keywords)
    any_term: str = ""

    # Specific field filters
    borrower: Optional[str] = None
    card: Optional[str] = None
    phone: Optional[str] = None
    isbn: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    loan_id: Optional[str] = None

    # Status filters
    loan_is: Optional[LoanStatus] = None
    fine_is: Optional[FineStatus] = None
    due: Optional[DueStatus] = None
    available: Optional[bool] = None

    # Sorting options
    sort: Optional[str] = None
    order: OrderDirection = OrderDirection.ASCENDING

    # Pagination parameters
    limit: Optional[int] = None
    page: int = 1

    # Keyword aliases for parsing (use exact field names as primary keys)
    KEYWORD_ALIASES: ClassVar[Dict[str, Set[str]]] = {
        "borrower": {"user"},
        "loan_is": {"loan_status", "loan"},
        "fine_is": {"fine_status", "fine"},
        "due": {"due_status"},
        "available": {"availability"},
        "sort": {"sort_by"},
        "order": {"order_by", "order_direction"},
        "limit": {"max", "count"},
        "page": {"page_num"},
    }

    # Value mapping for enum fields and booleans
    VALUE_MAPPINGS: ClassVar[Dict[str, Dict[str, any]]] = {
        "loan_is": {
            "active": LoanStatus.ACTIVE,
            "returned": LoanStatus.RETURNED,
            "in": LoanStatus.RETURNED,
        },
        "fine_is": {
            "owed": FineStatus.OWED,
            "paid": FineStatus.PAID,
        },
        "due": {
            "past": DueStatus.PAST,
            "future": DueStatus.FUTURE,
        },
        "available": {
            "true": True,
            "yes": True,
            "available": True,
            "false": False,
            "no": False,
            "unavailable": False,
            "checked_out": False,
        },
        "order": {
            "asc": OrderDirection.ASCENDING,
            "ascending": OrderDirection.ASCENDING,
            "desc": OrderDirection.DESCENDING,
            "descending": OrderDirection.DESCENDING,
        },
    }

    def __init__(
        self,
        raw_query: str = "",
        borrower: Optional[str] = None,
        card: Optional[str] = None,
        phone: Optional[str] = None,
        isbn: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        loan_id: Optional[str] = None,
        sort: Optional[str] = None,
        order: OrderDirection = OrderDirection.ASCENDING,
        loan_is: Optional[LoanStatus] = None,
        fine_is: Optional[FineStatus] = None,
        due: Optional[DueStatus] = None,
        available: Optional[bool] = None,
        limit: Optional[int] = None,
        page: int = 1,
        any_term: str = "",
    ):
        """
        Initialize a Query object with optional parameters.

        Args:
            raw_query: Original query string (if created from string)
            borrower: Filter by borrower name
            card: Filter by card ID
            phone: Filter by phone number
            isbn: Filter by book ISBN
            title: Filter by book title
            author: Filter by book author
            loan_id: Filter by loan ID
            sort: Field to sort results by
            order: Sort direction
            loan_is: Status of loans to filter
            fine_is: Status of fines to filter
            due: Status of due dates to filter
            available: Filter by book availability
            limit: Maximum results to return
            page: Page number for pagination
            any_term: General search term
        """
        self.raw_query = raw_query
        self.borrower = borrower
        self.card = card
        self.phone = phone
        self.isbn = isbn
        self.title = title
        self.author = author
        self.loan_id = loan_id
        self.sort = sort
        self.order = order
        self.loan_is = loan_is
        self.fine_is = fine_is
        self.due = due
        self.available = available
        self.limit = limit
        self.page = page
        self.any_term = any_term

        # If raw_query was provided, parse it
        if raw_query:
            self.parse()

    @classmethod
    def of(cls, query_string: str) -> "Query":
        """
        Alternative constructor that creates a Query from a string.

        Args:
            query_string: The search query string to parse

        Returns:
            A new Query object representing the parsed query
        """
        return cls(raw_query=query_string).parse()

    def parse(self) -> "Query":
        """
        Parse the raw query string into structured query components.

        Returns:
            Self, for method chaining
        """
        if not self.raw_query:
            return self

        parts = []
        current = ""
        in_quotes = False

        # First split the query respecting quoted sections
        for char in self.raw_query:
            if char == '"' and (not current or current[-1] != "\\"):
                in_quotes = not in_quotes
                current += char
            elif char.isspace() and not in_quotes:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char

        if current:
            parts.append(current)

        # Process the parts to extract keywords and values
        any_terms = []

        i = 0
        while i < len(parts):
            part = parts[i]

            # Check if this part contains a keyword
            if ":" in part:
                keyword, value = part.split(":", 1)
                keyword = keyword.lower()

                # Handle quoted values
                if value.startswith('"') and value.endswith('"') and len(value) > 1:
                    value = value[1:-1]

                self._set_keyword_value(keyword, value)
            else:
                # If no keyword, add to general search terms
                any_terms.append(part)

            i += 1

        # Join any remaining terms as the general search
        if any_terms:
            self.any_term = " ".join(any_terms)

        return self

    def _set_keyword_value(self, keyword: str, value: str) -> None:
        """
        Set the appropriate field based on the keyword.

        Args:
            keyword: The keyword to set
            value: The value to set for the keyword
        """
        # Find the canonical field name for the keyword
        field_name = None
        for field, aliases in self.KEYWORD_ALIASES.items():
            if keyword in aliases:
                field_name = field
                break

        # Use the keyword directly if no alias is found
        if field_name is None:
            field_name = keyword

        # Check if this is a valid field
        if not hasattr(self, field_name):
            return

        # Handle numeric fields
        if field_name == "page":
            try:
                self.page = int(value)
            except ValueError:
                # Ignore invalid page values
                pass
            return
        elif field_name == "limit":
            try:
                self.limit = int(value)
            except ValueError:
                # Ignore invalid limit values
                pass
            return

        # Handle enum fields and booleans
        if field_name in self.VALUE_MAPPINGS and value.lower() in self.VALUE_MAPPINGS[field_name]:
            setattr(self, field_name, self.VALUE_MAPPINGS[field_name][value.lower()])
        else:
            # Set the field value directly
            setattr(self, field_name, value)

    def has_filters(self) -> bool:
        """
        Check if any filters are applied in this query.

        Returns:
            True if any filter is set, False otherwise
        """
        filter_fields = [
            "borrower",
            "card",
            "phone",
            "isbn",
            "title",
            "author",
            "loan_id",
            "loan_is",
            "fine_is",
            "due",
            "available",
        ]

        return any(getattr(self, field) is not None for field in filter_fields) or bool(self.any_term)

    def __str__(self) -> str:
        """String representation of the query for debugging."""
        parts = []

        if self.any_term:
            parts.append(f"Any: '{self.any_term}'")

        fields = [
            ("Borrower", self.borrower),
            ("Card", self.card),
            ("Phone", self.phone),
            ("ISBN", self.isbn),
            ("Title", self.title),
            ("Author", self.author),
            ("Loan ID", self.loan_id),
            ("Loan Status", self.loan_is.name if self.loan_is else None),
            ("Fine Status", self.fine_is.name if self.fine_is else None),
            ("Due Status", self.due.name if self.due else None),
            ("Available", self.available),
            ("Sort By", self.sort),
            ("Order", self.order.name if self.order else None),
            ("Limit", self.limit),
            ("Page", self.page),
        ]

        parts.extend(f"{name}: '{value}'" for name, value in fields if value is not None)

        return f"Query({', '.join(parts)})"


if __name__ == "__main__":
    """Simple demo of the Query parser."""
    query_str = input("Enter query: ")
    query = Query.of(query_str)
    print(f"\nParsed query: {query}")
