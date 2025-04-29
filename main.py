"""
This is the entry point used only for testing purposes.
It has an example of how to use the API methods.
This does not call the HTTP endpoints directly, instead it imports the api methods from backend/api.py.

If you are looking for the implementation of the API methods, check the backend/api.py file.
If you are looking for the HTTP endpoints, check the backend/views.py file.
If you are looking for managing the database, check the manage.py file.
"""

from datetime import date, timedelta
import django, os, sys
from django.core.exceptions import ValidationError
from setup.logger import log
import traceback

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# The modules below contain the main logic
from backend.api import *
from reset import clear_database, import_data


def main():
    """
    Main testing playground for the API methods.
    By default, it contains examples of how to use the API methods.

    All available API methods:
     - search_books(query: str) -> List[Tuple]
     - checkout(card_id: str, isbn: str) -> str
     - search_loans(card_id: str, query: str) -> List[Tuple]
     - checkin(loan_id: str) -> str
     - get_user_fines(card_id: str, include_paid: bool = False) -> Decimal
     - get_fines(card_ids:list = [], include_paid: bool = False, sum: bool = False) -> List[Tuple]
     - get_fines_dict(card_ids:list = [], include_paid: bool = False) -> Dict[str, Decimal]
     - pay_loan_fine(loan_id: str) -> dict
     - pay_borrower_fines(card_id: str) -> dict
     - update_fines(current_date: date = date.today()) -> None
     - create_borrower(ssn: str, bname: str, address: str, phone: str = None) -> Tuple[str, str]
     - create_book(isbn: str, title: str) -> Tuple[str, str]
     - create_junction(author_id: str, isbn: str) -> Tuple[str, str]
     - create_author(author_name: str) -> Tuple[str, str]

    Setup:
     - clear_database()
     - import_data()
    """
    # Reset database
    clear_database()
    import_data()

    # Example of the create_borrower method
    card_id: str = None
    try:
        card_id, bname = create_borrower("123456789", "John Doe", "123 Main St", "555-5555")
        log.info(f"Borrower created: {card_id}, {bname}")
    except ValidationError as e:
        log.warning(f"Validation error: {e}")
        card_id = "10001000"  # Use a fallback ID for testing
    except Exception as e:
        log.error(f"Error creating borrower: {e}\n{traceback.format_exc()}")

    # Example of the search_books method
    isbn: str = None
    try:
        books = search_books("CLASSICAL")
        log.info(f"Books found: {len(books)} books total")
        if books:
            isbn, title, names = books[0]
            log.info(f"Selected book: {title} ({isbn})")
    except Exception as e:
        log.error(f"Error searching book: {e}\n{traceback.format_exc()}")
        return

    # Example of the checkout method
    loan_id: str = None
    try:
        loan_id = checkout(card_id, isbn)
        log.info(f"Book checked out: Loan {loan_id}")
    except ValidationError as e:
        log.warning(f"Checkout validation error: {e}")
    except Exception as e:
        log.error(f"Error checking out book: {e}\n{traceback.format_exc()}")
        return

    # Example of the search_loans method
    try:
        loans = search_loans(card_id, isbn)
        log.info(f"Loans found: {len(loans)} loans total")
        if loans:
            loan_details = loans[0]
            log.info(f"Loan details: {loan_details}")
    except Exception as e:
        log.error(f"Error searching loans: {e}\n{traceback.format_exc()}")

    # Example of the get_fines method with single card ID in list
    try:
        fines = get_fines(card_ids=[card_id])
        log.info(f"Fines found: {len(fines)} unpaid fines")

        # Example with include_paid
        all_fines = get_fines(card_ids=[card_id], include_paid=True)
        log.info(f"All fines (including paid): {len(all_fines)} fines")

        # Example with multiple card IDs
        multi_card_fines = get_fines(card_ids=["10001000", "10001001"])
        log.info(f"Multi-card fines found: {len(multi_card_fines)} unpaid fines")
    except Exception as e:
        log.error(f"Error getting fines: {e}\n{traceback.format_exc()}")

    # Example of get_user_fines method
    try:
        user_fine_total = get_user_fines(card_id)
        log.info(f"User fine total: ${user_fine_total:.2f}")
    except Exception as e:
        log.error(f"Error getting user fines: {e}\n{traceback.format_exc()}")

    # Example of get_fines_dict method
    try:
        fines_dict = get_fines_dict()
        log.info(f"Fines by user: {fines_dict}")

        # Example with specific card IDs
        specific_fines_dict = get_fines_dict(card_ids=["10001000", "10001001"])
        log.info(f"Specific fines by user: {specific_fines_dict}")
    except Exception as e:
        log.error(f"Error getting fines dictionary: {e}\n{traceback.format_exc()}")

    # Example of the update_fines method
    try:
        # For testing purposes, we set the date to the future
        update_fines(date.today() + timedelta(days=20))
        log.info(f"All fines updated")

        # Show updated fines
        updated_user_fine = get_user_fines(card_id)
        log.info(f"Updated user fine total: ${updated_user_fine:.2f}")
    except Exception as e:
        log.error(f"Error updating fines: {e}\n{traceback.format_exc()}")

    # Example of the checkin method
    try:
        checkin(loan_id)
        log.info(f"Book checked in: Loan {loan_id}")
    except ValidationError as e:
        log.warning(f"Checkin validation error: {e}")
    except Exception as e:
        log.error(f"Error checking in book: {e}\n{traceback.format_exc()}")

    # Example of the pay_borrower_fines method
    try:
        payment_result = pay_borrower_fines(card_id)
        log.info(f"Fines paid: {payment_result['message']}")

        # Verify fines are paid
        remaining_fines = get_user_fines(card_id)
        log.info(f"Remaining unpaid fines: ${remaining_fines:.2f}")
    except ValidationError as e:
        log.warning(f"Payment validation error: {e}")
    except Exception as e:
        log.error(f"Error paying borrower fines: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
