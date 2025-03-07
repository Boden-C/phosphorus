import pandas as pd
import os, re
from pandas import DataFrame
from typing import Dict, List, Tuple, Union

# Constants
BOOKS_PATH = "./data/books.csv"
BORROWERS_PATH = "./data/borrowers.csv"


def normalize_books(books_path: str, borrowers_path: str) -> Tuple[DataFrame, DataFrame, DataFrame, DataFrame]:
    """
    Normalize books and borrowers data into 3NF according to the specified schema.

    Args:
        books_path: Path to the books CSV file.
        borrowers_path: Path to the borrowers CSV file.

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
        print(f"Error reading input files: {e}")
        raise

    # Print both the datasets
    print("Books DataFrame:")
    print(books.head())
    print("\nBorrowers DataFrame:")
    print(borrowers.head())

    # NORMALIZE BOOKS TABLE
    # Rename columns to match schema
    books = books.rename(columns={"ISBN10": "Isbn10", "ISBN13": "Isbn"})
    book_table = books[["Isbn", "Isbn10", "Title", "Cover", "Publisher", "Pages"]].copy()

    # NORMALIZE AUTHORS
    author_dict: Dict[str, int] = {}
    author_id = 1
    book_author_pairs: List[Dict[str, Union[str, int]]] = []

    # Process authors
    for _, row in books.iterrows():
        if pd.notna(row["Author"]):
            # Split authors by comma and handle potential whitespace
            authors: List[str] = [author.strip() for author in row["Author"].split(",")]
            for author in authors:
                # Add new author if not seen before
                if author not in author_dict:
                    author_dict[author] = author_id
                    author_id += 1
                # Add book-author relationship
                book_author_pairs.append({"Isbn": row["Isbn"], "Author_id": author_dict[author]})

    # Create authors table from collected data
    authors_table = DataFrame({"Author_id": list(author_dict.values()), "Name": list(author_dict.keys())})
    authors_table = authors_table[["Author_id", "Name"]]

    # Create book_authors junction table
    book_authors_table = DataFrame(book_author_pairs)
    book_authors_table = book_authors_table[["Author_id", "Isbn"]]

    # NORMALIZE BORROWERS TABLE
    # Rename columns to match schema
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

    # Combine first and last name for Bname
    borrowers["Bname"] = borrowers["First_name"] + " " + borrowers["Last_name"]

    # Ensure all schema columns exist
    required_borrower_columns = [
        "Card_id",
        "Ssn",
        "Bname",
        "First_name",
        "Last_name",
        "Email",
        "Address",
        "City",
        "State",
        "Phone",
    ]

    for col in required_borrower_columns:
        if col not in borrowers.columns:
            borrowers[col] = ""

    # Create borrowers table with schema columns
    borrowers_table = borrowers[required_borrower_columns].copy()

    return book_table, authors_table, book_authors_table, borrowers_table


def main():
    # Set to file location directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    books_path = re.sub(r"^./", re.escape(base_dir) + "/", BOOKS_PATH)
    borrowers_path = re.sub(r"^./", re.escape(base_dir) + "/", BORROWERS_PATH)

    try:
        book_table, authors_table, book_authors_table, borrowers_table = normalize_books(books_path, borrowers_path)
    except Exception as e:
        print(f"Normalization failed: {e}")
        return

    try:
        # Save normalized tables to CSV files
        book_table.to_csv("book.csv", index=False)
        authors_table.to_csv("authors.csv", index=False)
        book_authors_table.to_csv("book_authors.csv", index=False)
        borrowers_table.to_csv("borrower.csv", index=False)
        print("Successfully created normalized CSV files")
    except Exception as e:
        print(f"Error writing output files: {e}")


if __name__ == "__main__":
    main()
