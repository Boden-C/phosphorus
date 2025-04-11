"""
This is the entry point used only for testing purposes.
It has an example of how to use the API methods.
This does not call the HTTP endpoints directly, instead it imports the api methods from backend/api.py.

If you are looking for the implementation of the API methods, check the backend/api.py file.
If you are looking for the HTTP endpoints, check the backend/views.py file.
If you are looking for managing the database, check the manage.py file.
"""

from datetime import timedelta
import django, os, sys
from django.forms import ValidationError
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
     - search_books(query:str)
     - checkout(card_id:str, isbn:str)
     - search_loans(card_id:str, query:str)
     - checkin(loan_id:str)
     - get_borrower_fines(card_id:str, show_paid:bool=False)
     - pay_loan_fine(loan_id:str)
     - pay_borrower_fines(card_id:str)
     - get_fine_summary(card_id:str=None)
     - update_fines(current_date:date=date.today())
     - create_borrower(ssn:str, bname:str, address:str, phone:str=None)
     - create_book(isbn:str, title:str)
     - create_junction(author_id:str, isbn:str)
     - create_author(author_name:str)

    Setup:
     - clear_database()
     - import_data()
    """
    # Comment this out if you want to skip: Clears the database
    clear_database()
    # Comment this out if you want to skip: Imports the data into the database
    import_data()

    # Example of the create_borrower method
    card_id: str = None
    try:
        card_id, bname = create_borrower("123456789", "John Doe", "123 Main St", "555-5555")
        log.info(f"Borrower created: {card_id}, {bname}")
    except ValidationError as e:
        log.warning("User already exists. Skipping.")
        card_id = "10001000"
    except Exception as e:
        log.error(f"Error creating borrower: {e}\n{traceback.format_exc()}")

    # Example of the search_book method
    isbn: str = None
    try:
        books = search_books("CLASSICAL")
        log.info(f"Books found: {len(books)} books total")
        isbn, title, names = books[0]
    except Exception as e:
        log.error(f"Error searching book: {e}\n{traceback.format_exc()}")
        return

    # Example of the checkout_book method
    loan_id: str = None
    try:
        loan_id = checkout(card_id, isbn)
        log.info(f"Book checked out: Loan {loan_id}")
    except Exception as e:
        log.error(f"Error checking out book: {e}\n{traceback.format_exc()}")
        return

    # Example of the search_loans method
    try:
        loans = search_loans(card_id, isbn)
        log.info(f"Loans found: {len(loans)} loans total")
    except Exception as e:
        log.error(f"Error searching loans: {e}\n{traceback.format_exc()}")

    # Example of the get_borrower_fines method
    try:
        fines = get_borrower_fines(card_id)
        log.info(f"Fines found: {len(fines)} fines")
    except Exception as e:
        log.error(f"Error getting borrower fines: {e}\n{traceback.format_exc()}")

    # Example of get_fine_summary method
    try:
        fine_summary = get_fine_summary()
        log.info(f"Fine summary: {fine_summary}")
    except Exception as e:
        log.error(f"Error getting fine summary: {e}\n{traceback.format_exc()}")

    # Example of the update_fines method
    try:
        # For testing purposes, we set the date to the future
        update_fines(date.today() + timedelta(days=20))
        log.info(f"All fines updated")
    except Exception as e:
        log.error(f"Error updating fines: {e}\n{traceback.format_exc()}")

    # Example of the get_fine_summary method
    try:
        fine_summary = get_fine_summary(card_id)
        log.info(f"Fine summary: {fine_summary}")
    except Exception as e:
        log.error(f"Error getting fine summary: {e}\n{traceback.format_exc()}")

    # Example of the checkin method
    try:
        checkin(loan_id)
        log.info(f"Book checked in: Loan {loan_id}")
    except Exception as e:
        log.error(f"Error checking in book: {e}\n{traceback.format_exc()}")

    # Example of the pay_borrower_fines method
    try:
        pay_borrower_fines(card_id)
        log.info(f"Fines paid for borrower {card_id}")
    except Exception as e:
        log.error(f"Error paying borrower fines: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
