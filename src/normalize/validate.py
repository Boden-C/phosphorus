import pandas as pd
import re
from typing import Dict
from log_config import logger


def validate_books(book_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the book table data."""
    issues = {"isbn_invalid": 0, "isbn10_invalid": 0, "isbn_mismatch": 0, "duplicate_isbn": 0, "pages_invalid": 0}

    # Check ISBN-13 format and checksum
    def is_valid_isbn13(isbn: str) -> bool:
        if not isbn or not isinstance(isbn, str) or not re.match(r"^\d{13}$", isbn):
            return False

        # ISBN-13 checksum
        digits = [int(d) for d in isbn]
        weighted_sum = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
        return weighted_sum % 10 == 0

    # Check ISBN-10 format and checksum
    def is_valid_isbn10(isbn: str) -> bool:
        if not isbn or not isinstance(isbn, str) or not re.match(r"^[\dX]{10}$", isbn):
            return False

        # ISBN-10 checksum
        digits = [10 if c == "X" else int(c) for c in isbn]
        weighted_sum = sum((10 - i) * d for i, d in enumerate(digits))
        return weighted_sum % 11 == 0

    # Convert ISBN-10 to ISBN-13
    def isbn10_to_isbn13(isbn10: str) -> str:
        if not isbn10 or len(isbn10) != 10:
            return None

        # Remove check digit, prefix with '978', calculate new check digit
        base = "978" + isbn10[:-1]
        digits = [int(d) for d in base]

        # Calculate check digit
        weighted_sum = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
        check_digit = (10 - (weighted_sum % 10)) % 10

        return base + str(check_digit)

    # Vectorized operations
    isbn13_invalid = book_table["Isbn"].apply(lambda x: not is_valid_isbn13(str(x)) if pd.notna(x) else False)
    issues["isbn_invalid"] = isbn13_invalid.sum()

    if issues["isbn_invalid"] > 0 and issues["isbn_invalid"] <= 5:
        logger.warning(
            f"Found {issues['isbn_invalid']} books with invalid ISBN-13 checksum: {book_table.loc[isbn13_invalid, 'Isbn'].tolist()}"
        )
    elif issues["isbn_invalid"] > 0:
        logger.warning(f"Found {issues['isbn_invalid']} books with invalid ISBN-13 checksum.")

    isbn10_invalid = book_table["Isbn10"].apply(lambda x: not is_valid_isbn10(str(x)) if pd.notna(x) else False)
    issues["isbn10_invalid"] = isbn10_invalid.sum()

    if issues["isbn10_invalid"] > 0 and issues["isbn10_invalid"] <= 5:
        logger.warning(
            f"Found {issues['isbn10_invalid']} books with invalid ISBN-10 checksum: {book_table.loc[isbn10_invalid, 'Isbn10'].tolist()}"
        )
    elif issues["isbn10_invalid"] > 0:
        logger.warning(f"Found {issues['isbn10_invalid']} books with invalid ISBN-10 checksum.")

    # Check for ISBN-13 and ISBN-10 correspondence
    valid_both = book_table["Isbn"].notna() & book_table["Isbn10"].notna() & ~isbn13_invalid & ~isbn10_invalid
    if valid_both.sum() > 0:
        calculated_isbn13 = book_table.loc[valid_both, "Isbn10"].apply(isbn10_to_isbn13)
        mismatch = calculated_isbn13 != book_table.loc[valid_both, "Isbn"]
        issues["isbn_mismatch"] = mismatch.sum()

        if issues["isbn_mismatch"] > 0 and issues["isbn_mismatch"] <= 5:
            mismatched_records = book_table.loc[valid_both][mismatch]
            logger.warning(
                f"Found {issues['isbn_mismatch']} books where ISBN-13 and ISBN-10 don't correspond: {list(zip(mismatched_records['Isbn'], mismatched_records['Isbn10']))}"
            )
        elif issues["isbn_mismatch"] > 0:
            logger.warning(f"Found {issues['isbn_mismatch']} books where ISBN-13 and ISBN-10 don't correspond.")

    # Check for duplicate ISBNs
    duplicates = book_table.duplicated(subset=["Isbn"], keep=False)
    issues["duplicate_isbn"] = duplicates.sum()

    if issues["duplicate_isbn"] > 0 and issues["duplicate_isbn"] <= 5:
        logger.warning(
            f"Found {issues['duplicate_isbn']} duplicate ISBN entries: {book_table.loc[duplicates, 'Isbn'].tolist()}"
        )
    elif issues["duplicate_isbn"] > 0:
        logger.warning(f"Found {issues['duplicate_isbn']} duplicate ISBN entries.")

    # Check for valid page count
    invalid_pages = (book_table["Pages"] <= 0) & book_table["Pages"].notna()
    issues["pages_invalid"] = invalid_pages.sum()

    if issues["pages_invalid"] > 0:
        logger.warning(f"Found {issues['pages_invalid']} books with invalid page counts (0 or negative).")

    # Check for missing values in important fields
    for column in ["Isbn", "Title", "Publisher"]:
        missing = book_table[column].isna()
        missing_count = missing.sum()
        if missing_count > 0:
            # Log the row indices with missing values
            missing_rows = book_table[missing].index.tolist()
            titles_sample = []
            if column != "Title" and "Title" in book_table.columns:
                for idx in missing_rows[:5]:  # Limit to 5
                    title = book_table.at[idx, "Title"] if pd.notna(book_table.at[idx, "Title"]) else "Unknown Title"
                    titles_sample.append(f"Row {idx}: {title}")

                logger.warning(
                    f"Column '{column}' has {missing_count} missing values in book_table:\n    "
                    f"{'\n    '.join(titles_sample)}"
                    f"{'and more...' if missing_count > 5 else ''}"
                )
            else:
                logger.warning(
                    f"Column '{column}' has {missing_count} missing values in book_table: {missing_rows[:5]} and more..."
                )

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

    # Check for author IDs in book_authors that don't exist in authors_table
    invalid_ids = ~book_authors_table["Author_id"].isin(authors_table["Author_id"])
    issues["invalid_author_ids"] = invalid_ids.sum()

    if issues["invalid_author_ids"] > 0 and issues["invalid_author_ids"] <= 5:
        logger.warning(
            f"Found {issues['invalid_author_ids']} book-author relationships with invalid author IDs: {book_authors_table.loc[invalid_ids, 'Author_id'].tolist()}"
        )
    elif issues["invalid_author_ids"] > 0:
        logger.warning(f"Found {issues['invalid_author_ids']} book-author relationships with invalid author IDs.")

    # Check for empty author names
    empty_names = authors_table["Name"].isna() | (authors_table["Name"] == "")
    issues["empty_author_names"] = empty_names.sum()

    if issues["empty_author_names"] > 0:
        # Log the row indices with empty names
        empty_rows = authors_table[empty_names].index.tolist()
        author_ids = authors_table.loc[empty_names, "Author_id"].tolist()
        logger.warning(
            f"Found {issues['empty_author_names']} authors with empty names. "
            f"Rows: {empty_rows[:5]}{' and more...' if issues['empty_author_names'] > 5 else ''}, "
            f"Author IDs: {author_ids[:5]}{' and more...' if issues['empty_author_names'] > 5 else ''}"
        )

    return issues


def validate_borrowers(borrowers_table: pd.DataFrame) -> Dict[str, int]:
    """Validate the borrowers table data."""
    issues = {"invalid_ssn": 0, "duplicate_ssn": 0, "invalid_email": 0, "invalid_phone": 0, "empty_fields": 0}

    # Check SSN format
    ssn_mask = borrowers_table["Ssn"].astype(str).str.match(r"^\d{3}-\d{2}-\d{4}$")
    invalid_ssn = ~ssn_mask & borrowers_table["Ssn"].notna()
    issues["invalid_ssn"] = invalid_ssn.sum()

    if issues["invalid_ssn"] > 0:
        invalid_rows = borrowers_table[invalid_ssn].index.tolist()
        logger.warning(
            f"Found {issues['invalid_ssn']} borrowers with invalid SSN format. "
            f"Rows: {invalid_rows[:5]}{' and more...' if issues['invalid_ssn'] > 5 else ''}"
        )

    # Check for duplicate SSNs
    duplicate_ssn = borrowers_table.duplicated(subset=["Ssn"], keep=False) & borrowers_table["Ssn"].notna()
    issues["duplicate_ssn"] = duplicate_ssn.sum()

    if issues["duplicate_ssn"] > 0:
        duplicate_rows = borrowers_table[duplicate_ssn].index.tolist()
        logger.warning(
            f"Found {issues['duplicate_ssn']} duplicate SSN entries. "
            f"Rows: {duplicate_rows[:5]}{' and more...' if issues['duplicate_ssn'] > 5 else ''}"
        )

    # Check email format
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    email_mask = borrowers_table["Email"].astype(str).str.match(email_pattern)
    invalid_email = ~email_mask & borrowers_table["Email"].notna()
    issues["invalid_email"] = invalid_email.sum()

    if issues["invalid_email"] > 0:
        invalid_rows = borrowers_table[invalid_email].index.tolist()
        invalid_emails = borrowers_table.loc[invalid_email, "Email"].tolist()
        logger.warning(
            f"Found {issues['invalid_email']} borrowers with invalid email format. "
            f"Rows: {invalid_rows[:5]}{' and more...' if issues['invalid_email'] > 5 else ''}, "
            f"Examples: {invalid_emails[:5]}{' and more...' if issues['invalid_email'] > 5 else ''}"
        )

    # Check phone format (XXX) XXX-XXXX
    phone_pattern = r"^\(\d{3}\) \d{3}-\d{4}$"
    phone_mask = borrowers_table["Phone"].astype(str).str.match(phone_pattern)
    invalid_phone = ~phone_mask & borrowers_table["Phone"].notna()
    issues["invalid_phone"] = invalid_phone.sum()

    if issues["invalid_phone"] > 0:
        invalid_rows = borrowers_table[invalid_phone].index.tolist()
        invalid_phones = borrowers_table.loc[invalid_phone, "Phone"].tolist()
        logger.warning(
            f"Found {issues['invalid_phone']} borrowers with invalid phone format. "
            f"Rows: {invalid_rows[:5]}{' and more...' if issues['invalid_phone'] > 5 else ''}, "
            f"Examples: {invalid_phones[:5]}{' and more...' if issues['invalid_phone'] > 5 else ''}"
        )

    # Check for empty required fields
    required_fields = ["Card_id", "Bname", "First_name", "Last_name"]
    for field in required_fields:
        empty = borrowers_table[field].isna() | (borrowers_table[field] == "")
        empty_count = empty.sum()
        if empty_count > 0:
            issues["empty_fields"] += empty_count
            empty_rows = borrowers_table[empty].index.tolist()
            # Try to include borrower names for better identification (if not checking Bname field)
            if field != "Bname" and "Bname" in borrowers_table.columns:
                names_sample = []
                for idx in empty_rows[:5]:  # Limit to first 5 for brevity
                    name = borrowers_table.at[idx, "Bname"] if pd.notna(borrowers_table.at[idx, "Bname"]) else "Unknown"
                    names_sample.append(f"Row {idx}: {name}")

                logger.warning(
                    f"Found {empty_count} borrowers with empty {field}. "
                    f"Affected borrowers (sample): {', '.join(names_sample)}"
                    f"{' and more...' if empty_count > 5 else ''}"
                )
            else:
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

        # Count total issues
        total_issues = sum(sum(table.values()) for table in results.values())
        if total_issues == 0:
            logger.info("Validation complete. No issues found.")
        else:
            logger.warning(f"Validation complete. Found {total_issues} total issues.")

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
