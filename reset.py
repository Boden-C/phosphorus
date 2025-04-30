"""
Used to fully reset the database and re-import data from the raw CSV files.
This will remove all previous data.
"""

import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.api import create_author, create_borrower, create_book, create_junction
from django.db import connection
import csv
from setup.logger import log
import traceback

AUTHORS_PATH = "setup/output/authors.csv"
BOOK_PATH = "setup/output/book.csv"
BOOK_AUTHORS_PATH = "setup/output/book_authors.csv"
BORROWER_PATH = "setup/output/borrower.csv"


def main():
    # Comment out a function call if you want to skip

    # WARNING: This will clear the database
    clear_database()

    # Import the data into the database
    import_data()


def clear_database():
    """
    Clear the database by deleting all records from the specified tables.
    """
    log.info("Clearing database...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("TRUNCATE TABLE book_authors;")
            cursor.execute("TRUNCATE TABLE borrower;")
            cursor.execute("TRUNCATE TABLE authors;")
            cursor.execute("TRUNCATE TABLE book;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    except Exception as e:
        log.error("Error clearing database: %s", str(e))


def import_data():
    imports_succeeded = 0
    imports_failed = 0

    log.info("Importing authors...")
    try:
        with open(AUTHORS_PATH, newline="", encoding="utf-8") as f, connection.cursor() as cursor:
            reader = csv.DictReader(f)
            names = [row["Name"].strip() for row in reader]
            cursor.execute("SELECT MAX(CAST(Author_id AS UNSIGNED)) FROM AUTHORS")
            max_id = cursor.fetchone()[0] or 0
            data = [(str(max_id + i + 1), name) for i, name in enumerate(names)]  # CHANGED
            cursor.executemany("INSERT INTO AUTHORS (Author_id, Name) VALUES (%s, %s)", data)  # CHANGED
        imports_succeeded += 1

    except FileNotFoundError:
        log.error("CSV file not found: %s", AUTHORS_PATH)
        imports_failed += 1
    except Exception as e:
        log.error(f"{e}\n{traceback.format_exc()}")
        log.error("Skipping author import.")
        imports_failed += 1

    log.info("Importing books...")
    try:
        with open(BOOK_PATH, newline="", encoding="utf-8") as f, connection.cursor() as cursor:
            reader = csv.DictReader(f)
            entries = [(row["Isbn"].strip(), row["Title"].strip()) for row in reader]
            cursor.executemany("INSERT INTO BOOK (Isbn, Title) VALUES (%s, %s)", entries)  # CHANGED
        imports_succeeded += 1
    except FileNotFoundError:
        log.error("CSV file not found: %s", BOOK_PATH)
        imports_failed += 1
    except Exception as e:
        log.error(f"{e}\n{traceback.format_exc()}")
        log.error("Skipping book import.")
        imports_failed += 1

    log.info("Importing book authors...")
    try:
        with open(BOOK_AUTHORS_PATH, newline="", encoding="utf-8") as f, connection.cursor() as cursor:
            reader = csv.DictReader(f)
            links = [(row["Author_id"].strip(), row["Isbn"].strip()) for row in reader]
            cursor.executemany("INSERT INTO BOOK_AUTHORS (Author_id, Isbn) VALUES (%s, %s)", links)  # CHANGED
        imports_succeeded += 1
    except FileNotFoundError:
        log.error("CSV file not found: %s", BOOK_AUTHORS_PATH)
        imports_failed += 1
    except Exception as e:
        log.error(f"{e}\n{traceback.format_exc()}")
        log.error("Skipping book authors import.")
        imports_failed += 1

    log.info("Importing borrowers...")
    try:
        with open(BORROWER_PATH, newline="", encoding="utf-8") as f, connection.cursor() as cursor:
            reader = csv.DictReader(f)
            cursor.execute("SELECT MAX(CAST(card_id AS UNSIGNED)) FROM borrower")
            max_id = cursor.fetchone()[0] or 10000000
            data = []
            for i, row in enumerate(reader):
                ssn = row["Ssn"].strip()
                bname = row["Bname"].strip()
                address = row["Address"].strip()
                phone = row.get("Phone", "").strip()
                card_id = str(max_id + i + 1)
                data.append((card_id, ssn, bname, address, phone))
            cursor.executemany("INSERT INTO BORROWER (Card_id, Ssn, Bname, Address, Phone) VALUES (%s, %s, %s, %s, %s)", data)  # CHANGED
        imports_succeeded += 1

    except FileNotFoundError:
        log.error("CSV file not found: %s", BORROWER_PATH)
        imports_failed += 1
    except Exception as e:
        log.error(f"{e}\n{traceback.format_exc()}")
        log.error("Skipping borrower import.")
        imports_failed += 1

    log.info(f"Done. Created: {imports_succeeded}, Skipped: {imports_failed}")


if __name__ == "__main__":
    main()