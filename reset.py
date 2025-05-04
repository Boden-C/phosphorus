"""
Used to fully reset the database, create initial users, and re-import data.
This will remove all previous data. FOR DEVELOPMENT ONLY.
"""

import os
import django
import sys
import csv
import traceback

# Setup Django environment
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# Import necessary models and functions AFTER django.setup()
from django.contrib.auth.models import User, Group
from django.db import connection, IntegrityError
from setup.logger import log
from backend.api import create_borrower, create_librarian

AUTHORS_PATH = "setup/output/authors.csv"
BOOK_PATH = "setup/output/book.csv"
BOOK_AUTHORS_PATH = "setup/output/book_authors.csv"
BORROWER_PATH = "setup/output/borrower.csv"

# --- Hardcoded Credentials (FOR DEVELOPMENT ONLY) ---
SUPERUSER_USERNAME = "admin"
SUPERUSER_PASSWORD = "adminpassword"

LIBRARIAN_USERNAME = "librarian1"
LIBRARIAN_PASSWORD = "librarian1password"

BORROWER_TEMP_PASSWORD = "borrowerpassword"
# --- ---


def main():
    # WARNING: This will clear the database, including users
    clear_database()

    # Create essential groups and initial users
    create_initial_groups_and_users()

    # Import the data into the database and create borrower users
    import_data()


def clear_database():
    """
    Clear the database by deleting all records from specified tables,
    including Django's auth tables.
    """
    log.info("Clearing database (including auth tables)...")
    try:
        with connection.cursor() as cursor:
            # Disable FK checks to truncate tables with dependencies
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

            # Truncate your application tables
            cursor.execute("TRUNCATE TABLE book_authors;")
            cursor.execute("TRUNCATE TABLE book_loans;")
            cursor.execute("TRUNCATE TABLE fines;")
            cursor.execute("TRUNCATE TABLE borrower;")
            cursor.execute("TRUNCATE TABLE authors;")
            cursor.execute("TRUNCATE TABLE book;")

            # Truncate Django auth tables
            cursor.execute("TRUNCATE TABLE auth_user_groups;")
            cursor.execute("TRUNCATE TABLE auth_user_user_permissions;")
            cursor.execute("TRUNCATE TABLE auth_group_permissions;")
            cursor.execute("TRUNCATE TABLE auth_permission;")
            cursor.execute("TRUNCATE TABLE auth_group;")
            cursor.execute("TRUNCATE TABLE auth_user;")

            # Truncate Django admin/session/contenttypes tables
            cursor.execute("TRUNCATE TABLE django_admin_log;")
            cursor.execute("TRUNCATE TABLE django_content_type;")
            cursor.execute("TRUNCATE TABLE django_migrations;")
            cursor.execute("TRUNCATE TABLE django_session;")

            # Re-enable FK checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        log.info("Database cleared successfully.")
    except Exception as e:
        log.error("Error clearing database: %s\n%s", str(e), traceback.format_exc())
        # Exit if clearing fails, as subsequent steps might behave unexpectedly
        sys.exit(1)


def create_initial_groups_and_users():
    """Creates necessary Groups and initial admin/librarian users."""
    log.info("Creating initial groups and users...")

    # 1. Create Librarians Group
    try:
        librarian_group, _ = Group.objects.get_or_create(name="Librarians")
        log.info("Group 'Librarians' ensured.")
    except Exception as e:
        log.error("Failed to create group: %s", e)
        return  # Stop if group can't be created

    # 2. Create Superuser
    if not User.objects.filter(username=SUPERUSER_USERNAME).exists():
        try:
            User.objects.create_superuser(username=SUPERUSER_USERNAME, password=SUPERUSER_PASSWORD)
            log.info(f"Superuser '{SUPERUSER_USERNAME}' created.")
        except Exception as e:
            log.error("Failed to create superuser '%s': %s", SUPERUSER_USERNAME, e)
    else:
        log.warning(f"Superuser '{SUPERUSER_USERNAME}' already exists. Skipping creation.")

    # 3. Create Librarian User using API
    if not User.objects.filter(username=LIBRARIAN_USERNAME).exists():
        try:
            staff_id, username = create_librarian(LIBRARIAN_USERNAME, LIBRARIAN_PASSWORD)
            log.info(f"Librarian user '{LIBRARIAN_USERNAME}' created with staff ID {staff_id}.")
        except Exception as e:
            log.error("Failed to create librarian user '%s': %s", LIBRARIAN_USERNAME, e)
    else:
        log.warning(f"Librarian user '{LIBRARIAN_USERNAME}' already exists. Skipping creation.")


def import_data():
    """Imports data from CSVs."""
    imports_succeeded = 0
    imports_failed = 0

    # --- Import Authors (No User creation needed) ---
    log.info("Importing authors...")
    try:
        # ... (keep existing author import logic using direct SQL INSERT) ...
        # Example using the previous direct SQL approach:
        with open(AUTHORS_PATH, newline="", encoding="utf-8") as f, connection.cursor() as cursor:
            reader = csv.DictReader(f)
            names = [row["Name"].strip() for row in reader]
            cursor.execute("SELECT MAX(CAST(Author_id AS UNSIGNED)) FROM AUTHORS")
            max_id = cursor.fetchone()[0] or 0
            data = [(str(max_id + i + 1), name) for i, name in enumerate(names)]
            cursor.executemany("INSERT INTO AUTHORS (Author_id, Name) VALUES (%s, %s)", data)
        imports_succeeded += 1
    except FileNotFoundError:
        log.error("CSV file not found: %s", AUTHORS_PATH)
        imports_failed += 1
    except Exception as e:
        log.error(f"Author import failed: {e}\n{traceback.format_exc()}")
        imports_failed += 1

    # --- Import Books (No User creation needed) ---
    log.info("Importing books...")
    try:
        # ... (keep existing book import logic using direct SQL INSERT) ...
        with open(BOOK_PATH, newline="", encoding="utf-8") as f, connection.cursor() as cursor:
            reader = csv.DictReader(f)
            entries = [(row["Isbn"].strip(), row["Title"].strip()) for row in reader]
            cursor.executemany("INSERT INTO BOOK (Isbn, Title) VALUES (%s, %s)", entries)
        imports_succeeded += 1
    except FileNotFoundError:
        log.error("CSV file not found: %s", BOOK_PATH)
        imports_failed += 1
    except Exception as e:
        log.error(f"Book import failed: {e}\n{traceback.format_exc()}")
        imports_failed += 1

    # --- Import Book Authors (No User creation needed) ---
    log.info("Importing book authors...")
    try:
        with open(BOOK_AUTHORS_PATH, newline="", encoding="utf-8") as f, connection.cursor() as cursor:
            reader = csv.DictReader(f)
            links = [(row["Author_id"].strip(), row["Isbn"].strip()) for row in reader]
            cursor.executemany("INSERT INTO BOOK_AUTHORS (Author_id, Isbn) VALUES (%s, %s)", links)
        imports_succeeded += 1
    except FileNotFoundError:
        log.error("CSV file not found: %s", BOOK_AUTHORS_PATH)
        imports_failed += 1
    except Exception as e:
        log.error(f"Book authors import failed: {e}\n{traceback.format_exc()}")
        imports_failed += 1

    log.info("Importing borrowers...")
    try:
        with open(BORROWER_PATH, newline="", encoding="utf-8") as f, connection.cursor() as cursor:
            reader = csv.DictReader(f)
            cursor.execute("SELECT MAX(CAST(card_id AS UNSIGNED)) FROM borrower")
            data = []
            for i, row in enumerate(reader):
                card_id = row["Card_id"].strip()
                ssn = row["Ssn"].strip()
                bname = row["Bname"].strip()
                address = row["Address"].strip()
                phone = row.get("Phone", "").strip()
                data.append((card_id, ssn, bname, address, phone))
            cursor.executemany(
                "INSERT INTO BORROWER (Card_id, Ssn, Bname, Address, Phone) VALUES (%s, %s, %s, %s, %s)", data
            )
        imports_succeeded += 1

    except FileNotFoundError:
        log.error("CSV file not found: %s", BORROWER_PATH)
        imports_failed += 1
    except Exception as e:
        log.error(f"{e}\n{traceback.format_exc()}")
        log.error("Skipping borrower import.")
        imports_failed += 1

    log.info(
        f"Import process finished. Table imports succeeded: {imports_succeeded}, Table imports failed/skipped: {imports_failed}"
    )


if __name__ == "__main__":
    main()
