import pandas as pd
import re
from typing import Dict
from log_config import logger


import pandas as pd
import re
from typing import Dict
from log_config import logger


def is_valid_isbn13(isbn: str) -> bool:
    if not isbn or not isinstance(isbn, str) or not re.match(r"^\d{13}$", isbn):
        return False

    digits = [int(d) for d in isbn]
    weighted_sum = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    return weighted_sum % 10 == 0


def validate_books(book_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the book table data."""
    issues = {"duplicate_isbn": 0, "isbn_invalid": 0}

    # Check for duplicate ISBNs
    duplicates = book_table.duplicated(subset=["Isbn"], keep=False)
    issues["duplicate_isbn"] = duplicates.sum()

    if issues["duplicate_isbn"] > 0 and issues["duplicate_isbn"] <= 5:
        logger.warning(
            f"Found {issues['duplicate_isbn']} duplicate ISBN entries: {book_table.loc[duplicates, 'Isbn'].tolist()}"
        )
    elif issues["duplicate_isbn"] > 0:
        logger.warning(f"Found {issues['duplicate_isbn']} duplicate ISBN entries.")

    # Check ISBN-13 format and checksum
    isbn13_invalid = book_table["Isbn"].apply(lambda x: not is_valid_isbn13(str(x)) if pd.notna(x) else False)
    issues["isbn_invalid"] = isbn13_invalid.sum()

    if issues["isbn_invalid"] > 0 and issues["isbn_invalid"] <= 5:
        logger.warning(
            f"Found {issues['isbn_invalid']} books with invalid ISBN-13 checksum: {book_table.loc[isbn13_invalid, 'Isbn'].tolist()}"
        )
    elif issues["isbn_invalid"] > 0:
        logger.warning(f"Found {issues['isbn_invalid']} books with invalid ISBN-13 checksum.")

    return issues


def validate_authors(authors_table: pd.DataFrame, book_authors_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the authors table data."""
    issues = {"duplicate_authors": 0, "invalid_author_ids": 0, "empty_author_names": 0}

    # Check for duplicate author names
    duplicates = authors_table.duplicated(subset=["Name"], keep=False)
    issues["duplicate_authors"] = duplicates.sum()

    if issues["duplicate_authors"] > 0 and issues["duplicate_authors"] <= 5:
        logger.warning(
            f"Found {issues['duplicate_authors']} duplicate author entries: {authors_table.loc[duplicates, 'Name'].tolist()}"
        )
    elif issues["duplicate_authors"] > 0:
        logger.warning(f"Found {issues['duplicate_authors']} duplicate author entries.")

    return issues


def validate_borrowers(borrowers_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the borrowers table data."""
    issues = {"duplicate_ssn": 0, "empty_fields": 0}

    # Check for duplicate SSNs
    duplicate_ssn = borrowers_table.duplicated(subset=["Ssn"], keep=False) & borrowers_table["Ssn"].notna()
    issues["duplicate_ssn"] = duplicate_ssn.sum()

    if issues["duplicate_ssn"] > 0:
        duplicate_rows = borrowers_table[duplicate_ssn].index.tolist()
        logger.warning(
            f"Found {issues['duplicate_ssn']} duplicate SSN entries. "
            f"Rows: {duplicate_rows[:5]}{' and more...' if issues['duplicate_ssn'] > 5 else ''}"
        )

    # Check for empty required fields
    required_fields = ["Card_id", "Bname", "Address", "Phone"]
    for field in required_fields:
        empty = borrowers_table[field].isna() | (borrowers_table[field] == "")
        empty_count = empty.sum()
        if empty_count > 0:
            issues["empty_fields"] += empty_count
            empty_rows = borrowers_table[empty].index.tolist()
            logger.warning(
                f"Found {empty_count} borrowers with empty {field}. "
                f"Rows: {empty_rows[:5]}{' and more...' if empty_count > 5 else ''}"
            )

    return issues


def validate_all_data(
    book_table: pd.DataFrame,
    authors_table: pd.DataFrame,
    book_authors_table: pd.DataFrame,
    borrowers_table: pd.DataFrame,
) -> Dict[str, Dict[str, int]]:
    """
    Validate all library data tables.

    Args:
        book_table: DataFrame containing book information
        authors_table: DataFrame containing author information
        book_authors_table: DataFrame containing book-author relationships
        borrowers_table: DataFrame containing borrower information

    Returns:
        Dictionary with validation results for each table
    """
    results = {}

    try:
        results["books"] = validate_books(book_table)
        results["authors"] = validate_authors(authors_table, book_authors_table)
        results["borrowers"] = validate_borrowers(borrowers_table)

        total_issues = sum(sum(table.values()) for table in results.values())
        if total_issues == 0:
            logger.info("Validation complete. No issues found.")
        else:
            logger.warning(f"Validation complete. Found {total_issues} potential issues.")

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

    return results


if __name__ == "__main__":
    # Example usage when script is run directly
    try:
        # Load data from files
        book_table = pd.read_csv("book.csv")
        authors_table = pd.read_csv("authors.csv")
        book_authors_table = pd.read_csv("book_authors.csv")
        borrowers_table = pd.read_csv("borrower.csv")

        results = validate_all_data(book_table, authors_table, book_authors_table, borrowers_table)
    except Exception as e:
        logger.error(f"Validation script failed: {str(e)}")
