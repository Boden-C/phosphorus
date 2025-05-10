"""
This is the entry point used only for testing purposes.
It has an example of how to use the API methods.
This does not call the HTTP endpoints directly, instead it imports the api methods from backend/api.py.

If you are looking for the implementation of the API methods, check the backend/api.py file.
If you are looking for the HTTP endpoints, check the backend/views.py file.
"""

from datetime import date, timedelta
import django, os, sys
from django.core.exceptions import ValidationError
from setup.logger import log
import traceback
import pathlib

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# The modules below contain the main logic
from backend.api import *
from reset import clear_database, create_initial_groups_and_users, import_data


def main():
    """
    Main testing playground for the API methods.
    By default, it contains examples of how to use the API methods.
    """
    # Reset database if allowed by .env.local
    if should_reset_database():
        log.info("Resetting database...")
        clear_database()
        create_initial_groups_and_users()
        import_data()
        update_env_var("RESET", "false")
        log.info("Database reset complete. RESET flag set to false.")
    else:
        log.info("Skipping database reset due to .env.local RESET=false")

    # Create librarian user
    try:
        user = create_librarian("librarian_test", "librarian123")
        log.info(f"Librarian created: username={user.username}, id={user.id}")
    except ValidationError as e:
        log.warning(f"Librarian creation validation error: {e}")
    except Exception as e:
        log.error(f"Error creating librarian: {e}\n{traceback.format_exc()}")

    # Create borrower
    card_id = "ID001001"
    try:
        borrower = create_borrower(
            ssn="123456789", bname="John Doe", address="123 Main St", phone="555-5555", card_id=card_id
        )
        log.info(
            f"Borrower created: card_id={borrower.card_id}, name={borrower.bname}, address={borrower.address}, phone={borrower.phone}"
        )
    except ValidationError as e:
        log.warning(f"Validation error: {e}")
    except Exception as e:
        log.error(f"Error creating borrower: {e}\n{traceback.format_exc()}")

    # Search books
    isbn: str = None
    try:
        # Use Query object for search_books
        books_result = search_books(Query.of("CLASSICAL"))
        log.info(f"Books found: {books_result.total} books total")
        if books_result.items:
            book = books_result.items[0]
            isbn = book.isbn
            log.info(f"Selected book: {book.title} ({book.isbn}) by {', '.join(book.authors)}")
    except Exception as e:
        log.error(f"Error searching book: {e}\n{traceback.format_exc()}")
        return

    # Checkout book
    loan_id: str = None
    try:
        loan = checkout(card_id, isbn)
        log.info(f"Book checked out: Loan {loan.loan_id}")
        loan_id = loan.loan_id
    except ValidationError as e:
        log.warning(f"Checkout validation error: {e}")
    except Exception as e:
        log.error(f"Error checking out book: {e}\n{traceback.format_exc()}")
        return

    # Search loans
    try:
        loans_result = search_loans(Query(card=card_id))
        log.info(f"Loans found: {loans_result.total} loans total")
    except Exception as e:
        log.error(f"Error searching loans: {e}\n{traceback.format_exc()}")

    # Get fines for borrower
    try:
        fines = get_fines(card_ids=[card_id])
        log.info(f"Fines found: {len(fines)} unpaid fines")
        for f in fines:
            log.info(f"Fine: loan_id={f.loan_id}, fine_amt={f.fine_amt}, paid={f.paid}")
        all_fines = get_fines(card_ids=[card_id], include_paid=True)
        log.info(f"All fines (including paid): {len(all_fines)} fines")
        multi_card_fines = get_fines(card_ids=["ID001001", "10001001"])
        log.info(f"Multi-card fines found: {len(multi_card_fines)} unpaid fines")
    except Exception as e:
        log.error(f"Error getting fines: {e}\n{traceback.format_exc()}")

    # Get user fine total
    try:
        user_fine_total = get_user_fines(card_id)
        log.info(f"User fine total: ${user_fine_total:.2f}")
    except Exception as e:
        log.error(f"Error getting user fines: {e}\n{traceback.format_exc()}")

    # Get fines dict
    try:
        fines_dict = get_fines_grouped()
        log.info(f"Fines by user: {fines_dict}")
        specific_fines_dict = get_fines_grouped(card_ids=["ID001001", "10001001"])
        log.info(f"Specific fines by user: {specific_fines_dict}")
    except Exception as e:
        log.error(f"Error getting fines dictionary: {e}\n{traceback.format_exc()}")

    # Update fines
    try:
        update_fines(date.today() + timedelta(days=20))
        log.info(f"All fines updated")
        updated_user_fine = get_user_fines(card_id)
        log.info(f"Updated user fine total: ${updated_user_fine:.2f}")
    except Exception as e:
        log.error(f"Error updating fines: {e}\n{traceback.format_exc()}")

    # Checkin book
    try:
        checkin(loan_id)
        log.info(f"Book checked in: Loan {loan_id}")
    except ValidationError as e:
        log.warning(f"Checkin validation error: {e}")
    except Exception as e:
        log.error(f"Error checking in book: {e}\n{traceback.format_exc()}")

    # Pay all fines for borrower
    try:
        paid_loans = pay_borrower_fines(card_id)
        if paid_loans:
            log.info(f"Fines paid for {len(paid_loans)} loans:")
            for l in paid_loans:
                log.info(f"Paid: loan_id={l.loan_id}, fine_amt={l.fine_amt}, paid={l.paid}")
        else:
            log.info("No fines to pay.")
        remaining_fines = get_user_fines(card_id)
        log.info(f"Remaining unpaid fines: ${remaining_fines:.2f}")
    except ValidationError as e:
        log.warning(f"Payment validation error: {e}")
    except Exception as e:
        log.error(f"Error paying borrower fines: {e}\n{traceback.format_exc()}")


def update_env_var(key: str, value: str) -> bool:
    """
    Updates or adds an environment variable in the .env.local file.

    Args:
        key: Environment variable name
        value: Environment variable value

    Returns:
        bool: True if update was successful, False otherwise
    """
    env_path = pathlib.Path(__file__).parent / ".env.local"

    # Read existing content or initialize empty if file doesn't exist
    content = {}
    if env_path.exists():
        try:
            with env_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        content[k.strip()] = v.strip()
        except Exception as e:
            log.warning(f"Error reading .env.local: {e}")
            return False

    # Update the specified key
    content[key] = value

    # Write back to file
    try:
        with env_path.open("w", encoding="utf-8") as f:
            for k, v in content.items():
                f.write(f"{k}={v}\n")
        return True
    except Exception as e:
        log.warning(f"Error writing to .env.local: {e}")
        return False


def should_reset_database() -> bool:
    """
    Determines whether to reset the database based on .env.local and RESET variable.
    Returns True if reset should occur, False otherwise.
    """
    env_path = pathlib.Path(__file__).parent / ".env.local"
    if not env_path.exists():
        return True
    try:
        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() == "RESET":
                    if value.strip().lower() == "false":
                        return False
    except Exception as e:
        log.warning(f"Could not read .env.local: {e}")
    return True


if __name__ == "__main__":
    main()
