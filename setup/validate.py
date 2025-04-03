import pandas as pd
import re
from typing import Dict
from logger import log


def is_valid_isbn13(isbn: str) -> bool:
    """Check if the ISBN-13 number is valid."""
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    total = sum((3 if i % 2 else 1) * int(num) for i, num in enumerate(isbn[:12]))
    check_digit = (10 - (total % 10)) % 10
    return check_digit == int(isbn[-1])


def validate_books(book_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the book table data."""
    issues = {"duplicate_isbn": 0, "isbn_invalid": 0, "non_upper_case_titles": 0}

    # Check for duplicate ISBNs
    duplicates = book_table.duplicated(subset=["Isbn"], keep=False)
    issues["duplicate_isbn"] = duplicates.sum()

    if issues["duplicate_isbn"] > 0:
        log.warning(f"Found {issues['duplicate_isbn']} duplicate ISBN entries.")

    # Check ISBN-13 format and checksum
    isbn13_invalid = book_table["Isbn"].apply(lambda x: not is_valid_isbn13(str(x)) if pd.notna(x) else False)
    issues["isbn_invalid"] = isbn13_invalid.sum()

    if issues["isbn_invalid"] > 0:
        log.warning(f"Found {issues['isbn_invalid']} books with invalid ISBN-13 checksum.")

    # Check if titles are in upper case
    if "Title" in book_table.columns:
        non_upper_case = book_table["Title"].apply(lambda x: x != x.upper() if pd.notna(x) else False)
        issues["non_upper_case_titles"] = non_upper_case.sum()

        if issues["non_upper_case_titles"] > 0:
            log.warning(f"Found {issues['non_upper_case_titles']} books with non-upper-case titles.")

    return issues


def validate_authors(authors_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the authors table data."""
    issues = {"duplicate_authors": 0, "empty_author_names": 0, "non_upper_case_authors": 0}

    # Check for duplicate author names
    duplicates = authors_table.duplicated(subset=["Name"], keep=False)
    issues["duplicate_authors"] = duplicates.sum()

    if issues["duplicate_authors"] > 0:
        log.warning(f"Found {issues['duplicate_authors']} duplicate author entries.")

    # Check for empty author names
    empty_names = authors_table["Name"].isna() | (authors_table["Name"] == "")
    issues["empty_author_names"] = empty_names.sum()

    if issues["empty_author_names"] > 0:
        log.warning(f"Found {issues['empty_author_names']} authors with empty names.")

    # Check if author names are in upper case
    non_upper_case = authors_table["Name"].apply(lambda x: x != x.upper() if pd.notna(x) else False)
    issues["non_upper_case_authors"] = non_upper_case.sum()

    if issues["non_upper_case_authors"] > 0:
        log.warning(f"Found {issues['non_upper_case_authors']} authors with non-upper-case names.")

    return issues


def validate_book_authors(book_authors_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the book-authors table data."""
    issues = {"duplicate_entries": 0, "missing_isbn": 0, "missing_author_id": 0}

    # Check for duplicate entries
    duplicates = book_authors_table.duplicated(subset=["Isbn", "Author_id"], keep=False)
    issues["duplicate_entries"] = duplicates.sum()

    if issues["duplicate_entries"] > 0:
        log.warning(f"Found {issues['duplicate_entries']} duplicate book-author entries.")

    # Check for missing ISBNs
    missing_isbn = book_authors_table["Isbn"].isna() | (book_authors_table["Isbn"] == "")
    issues["missing_isbn"] = missing_isbn.sum()

    if issues["missing_isbn"] > 0:
        log.warning(f"Found {issues['missing_isbn']} book-author entries with missing ISBN.")

    # Check for missing author IDs
    missing_author_id = book_authors_table["Author_id"].isna() | (book_authors_table["Author_id"] == "")
    issues["missing_author_id"] = missing_author_id.sum()

    if issues["missing_author_id"] > 0:
        log.warning(f"Found {issues['missing_author_id']} book-author entries with missing author ID.")

    return issues


def validate_borrowers(borrowers_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the borrowers table data."""
    issues = {"duplicate_ssn": 0, "empty_fields": 0, "non_upper_case_bnames": 0}

    # Check for duplicate SSNs
    duplicate_ssn = borrowers_table.duplicated(subset=["Ssn"], keep=False) & borrowers_table["Ssn"].notna()
    issues["duplicate_ssn"] = duplicate_ssn.sum()

    if issues["duplicate_ssn"] > 0:
        log.warning(f"Found {issues['duplicate_ssn']} duplicate SSN entries.")

    # Check for empty required fields
    required_fields = ["Card_id", "Bname", "Address", "Phone"]
    for field in required_fields:
        empty = borrowers_table[field].isna() | (borrowers_table[field] == "")
        empty_count = empty.sum()
        if empty_count > 0:
            issues["empty_fields"] += empty_count
            log.warning(f"Found {empty_count} borrowers with empty {field}.")

    # Check if borrower names are in upper case
    non_upper_case = borrowers_table["Bname"].apply(lambda x: x != x.upper() if pd.notna(x) else False)
    issues["non_upper_case_bnames"] = non_upper_case.sum()

    if issues["non_upper_case_bnames"] > 0:
        log.warning(f"Found {issues['non_upper_case_bnames']} borrowers with non-upper-case names.")

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
        results["authors"] = validate_authors(authors_table)
        results["book_authors"] = validate_book_authors(book_authors_table)
        results["borrowers"] = validate_borrowers(borrowers_table)

        total_issues = sum(sum(table.values()) for table in results.values())
        if total_issues == 0:
            log.info("Validation complete. No issues found.")
        else:
            log.warning(f"Validation complete. Found {total_issues} potential issues.")

    except Exception as e:
        log.error(f"Validation failed: {str(e)}")
        raise

    return results


if __name__ == "__main__":
    # Example usage when script is run directly
    try:
        # Load data from files
        book_table = pd.read_csv("setup/output/book.csv")
        authors_table = pd.read_csv("setup/output/authors.csv")
        book_authors_table = pd.read_csv("setup/output/book_authors.csv")
        borrowers_table = pd.read_csv("setup/output/borrower.csv")

        results = validate_all_data(book_table, authors_table, book_authors_table, borrowers_table)
    except Exception as e:
        log.error(f"Validation script failed: {str(e)}")
