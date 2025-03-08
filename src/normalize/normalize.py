import pandas as pd
import sys, os, re
from pandas import DataFrame
from typing import Dict, List, Tuple, Union
from log_config import logger
from validate import validate_all_data

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_PATH = os.path.join(BASE_DIR, "data", "books.csv")
BORROWERS_PATH = os.path.join(BASE_DIR, "data", "borrowers.csv")


def normalize_books(
    books_path: str, borrowers_path: str, useAllUppercase: bool = True
) -> Tuple[DataFrame, DataFrame, DataFrame, DataFrame]:
    """
    Normalize books and borrowers data into 3NF according to the specified schema.

    Args:
        books_path: Path to the books CSV file.
        borrowers_path: Path to the borrowers CSV file.
        useAllUppercase: If True, converts specific fields to title case.

    Returns:
        A tuple of DataFrames (book_table, authors_table, book_authors_table, borrowers_table)
    """
    # Import both datasets
    try:
        books = pd.read_csv(books_path, delimiter="\t")
        # Convert Pages to int
        books["Pages"] = pd.to_numeric(books["Pages"], errors="coerce").fillna(0).astype(int)
        borrowers = pd.read_csv(borrowers_path, delimiter=",", dtype=str)
    except Exception as e:
        logger.error(f"Error reading input files: {e}")
        raise

    # Log the dataset
    logger.info(f"Books dataset imported: {books.shape}")
    logger.info(f"Borrowers dataset imported: {borrowers.shape}")

    # Normalize books table
    books = books.rename(columns={"ISBN10": "Isbn10", "ISBN13": "Isbn"})
    if useAllUppercase:
        books["Title"] = books["Title"].str.upper()
        logger.info("Converting names to uppercase.")
    book_table = books[["Isbn", "Title"]].copy()

    # Normalize authors
    author_dict: Dict[str, int] = {}
    author_id = 1
    book_author_pairs: List[Dict[str, Union[str, int]]] = []

    pattern1 = r"(^|\s)([A-Z])\.([A-Z])\.(?!\s*[A-Z]\.)(\s|$)"
    pattern2 = r"(^|\s)([A-Z])\.\s([A-Z])\.(?!\s*[A-Z]\.)(\s|$)"
    pattern3 = r"(^|\s)([A-Z])\s([A-Z])(?!\s[A-Z](?:\s|$))(\s|$)"

    for _, row in books.iterrows():
        if pd.notna(row["Author"]):
            authors: List[str] = [author.strip() for author in row["Author"].split(",")]
            for author in authors:

                # Case 1: "J.K." -> "JK"
                if re.search(pattern1, author):
                    new_author = re.sub(pattern1, r"\1\2\3\4", author)
                    logger.info(f"Changing author format from '{author}' to '{new_author}'")
                    author = new_author

                # Case 2: "J. K." -> "JK"
                elif re.search(pattern2, author):
                    new_author = re.sub(pattern2, r"\1\2\3\4", author)
                    logger.info(f"Changing author format from '{author}' to '{new_author}'")
                    author = new_author

                # Case 3: "J K" -> "JK"
                elif re.search(pattern3, author):
                    new_author = re.sub(pattern3, r"\1\2\3\4", author)
                    logger.info(f"Changing author format from '{author}' to '{new_author}'")
                    author = new_author

                author = author.upper().strip() if useAllUppercase else author.strip()
                if author not in author_dict:
                    author_dict[author] = author_id
                    author_id += 1
                book_author_pairs.append({"Isbn": row["Isbn"], "Author_id": author_dict[author]})

    authors_table = DataFrame({"Author_id": list(author_dict.values()), "Name": list(author_dict.keys())})
    authors_table = authors_table[["Author_id", "Name"]]

    book_authors_table = DataFrame(book_author_pairs)
    book_authors_table = book_authors_table[["Author_id", "Isbn"]]

    # Normalize borrowers table
    borrowers = borrowers.rename(
        columns={
            "ID0000id": "Card_id",
            "ssn": "Ssn",
            "first_name": "First_name",
            "last_name": "Last_name",
            "email": "Email",
            "address": "Address",
            "city": "City",
            "state": "State",
            "phone": "Phone",
        }
    )

    borrowers["Bname"] = borrowers["First_name"] + " " + borrowers["Last_name"]
    if useAllUppercase:
        borrowers["Bname"] = borrowers["Bname"].str.upper()

    required_borrower_columns = ["Card_id", "Ssn", "Bname", "Address", "Phone"]
    for col in required_borrower_columns:
        if col not in borrowers.columns:
            borrowers[col] = ""

    borrowers_table = borrowers[required_borrower_columns].copy()

    return book_table, authors_table, book_authors_table, borrowers_table


def main():
    try:
        book_table, authors_table, book_authors_table, borrowers_table = normalize_books(BOOKS_PATH, BORROWERS_PATH)
    except Exception as e:
        logger.error(f"Error normalizing data: {e}")
        return

    logger.info("Data normalization completed. Starting validation...")
    validate_all_data(book_table, authors_table, book_authors_table, borrowers_table)

    try:
        # Save normalized tables to CSV files
        book_table.to_csv("book.csv", index=False)
        authors_table.to_csv("authors.csv", index=False)
        book_authors_table.to_csv("book_authors.csv", index=False)
        borrowers_table.to_csv("borrower.csv", index=False)
        logger.info("Exported normalized data.")
    except Exception as e:
        logger.error(f"Error saving normalized data: {e}")
        return


if __name__ == "__main__":
    main()
