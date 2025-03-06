import pandas as pd
import os
from pandas import DataFrame
from typing import Dict, List, Tuple, Union

# Constants
BOOKS_PATH = "./data/books.csv"
BORROWERS_PATH = "./data/borrowers.csv"


def normalize_books(books_path: str, borrowers_path: str) -> Tuple[DataFrame, DataFrame, DataFrame]:
    """
    Normalize books and borrowers data into 3NF.

    Args:
        books_path: Path to the books CSV file.
        borrowers_path: Path to the borrowers CSV file.

    Returns:
        A tuple of
    """
    # Import the datasets
    try:
        books = pd.read_csv(books_path, delimiter="\t", dtype=str)
        borrowers = pd.read_csv(borrowers_path, delimiter=",", dtype=str)
    except Exception as e:
        print(f"Error reading input files: {e}")
        raise

    # Show the datasets to understand
    print("Books DataFrame:")
    print(books.head())

    print("Borrowers DataFrame:")
    print(borrowers.head())

    # Rename columns to match schema
    books = books.rename(columns={"ISBN10": "Isbn10", "ISBN13": "Isbn"})
    borrowers = borrowers.rename(columns={"ID0000id": "Card_id", "ssn": "Ssn"})

    # Combine first and last name into a full name
    borrowers["Bname"] = borrowers["first_name"] + " " + borrowers["last_name"]

    # Combine Address
    borrowers["Address"] = borrowers["address"] + ", " + borrowers["city"] + ", " + borrowers["state"]

    columns_to_keep = ["Card_id", "Ssn", "Bname", "Address", "phone"]
    borrowers_table = borrowers[columns_to_keep]

    # Create book table with required columns
    book_table = books[["Isbn", "Isbn10", "Title", "Cover", "Publisher", "Pages"]].copy()

    # Extract and process authors
    author_dict: Dict[str, int] = {}
    author_id = 1
    book_author_pairs: List[Dict[str, Union[str, int]]] = []

    # Collect authors for book-author relationships
    for _, row in books.iterrows():
        if pd.notna(row["Author"]):
            # Split authors by comma
            authors: List[str] = [author.strip() for author in row["Author"].split(",")]
            for author in authors:
                # If new author, increment
                if author not in author_dict:
                    author_dict[author] = author_id
                    author_id += 1
                # Else add
                book_author_pairs.append({"Isbn": row["Isbn"], "Author_id": author_dict[author]})

    # Create DataFrames from the collected data
    authors_table = DataFrame({"Name": list(author_dict.keys()), "Author_id": list(author_dict.values())})[
        ["Author_id", "Name"]
    ]

    # Create the book_authors table
    book_authors_table = DataFrame(book_author_pairs)

    return book_table, authors_table, book_authors_table, borrowers_table


def main():

    # Set to file location directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    books_path = os.path.join(base_dir, "data", "books.csv")
    borrowers_path = os.path.join(base_dir, "data", "borrowers.csv")

    try:
        book_table, authors_table, book_authors_table, borrowers_table = normalize_books(books_path, borrowers_path)
    except Exception as e:
        print(f"Normalization failed: {e}")
        return

    try:
        book_table.to_csv("book.csv", index=False)
        authors_table.to_csv("authors.csv", index=False)
        book_authors_table.to_csv("book_authors.csv", index=False)
        borrowers_table.to_csv("borrowers.csv", index=False)
    except Exception as e:
        print(f"Error writing output files: {e}")


if __name__ == "__main__":
    main()
