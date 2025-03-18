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

    for _, row in books.iterrows():
        if pd.notna(row["Author"]):
            # Split multiple authors by comma
            authors: List[str] = [author.strip() for author in row["Author"].split(",")]

            for author in authors:
                # Normalize the author name
                normalized_author = normalize_author(author, useAllUppercase)

                # Add to author dictionary if not already present
                if normalized_author not in author_dict:
                    author_dict[normalized_author] = author_id
                    author_id += 1

                # Create book-author pair
                book_author_pairs.append({"Isbn": row["Isbn"], "Author_id": author_dict[normalized_author]})

    print("")
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


def normalize_author(author: str, uppercase: bool = False) -> str:
    """
    Normalize author names by:
    1. Removing all periods
    2. Removing spaces between single capital letters (J K -> JK, J. K. -> JK)

    Args:
        author: Author name string to normalize
        uppercase: Whether to convert the result to uppercase

    Returns:
        Normalized author name
    """
    original = author

    # Remove all periods
    author = author.replace(".", "")

    # Find patterns of single capital letters separated by spaces and join them
    pattern = r"\b((?:[A-Z]\s)+[A-Z])\b"
    matches = re.findall(pattern, author)
    for match in matches:
        no_spaces = match.replace(" ", "")
        author = author.replace(match, no_spaces)

    # Log if changes were made
    if original != author:
        print(f"; {original} -> {author}", end="")

    # Apply uppercase if required
    if uppercase:
        author = author.upper()

    return author.strip()


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
