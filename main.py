"""
This is the entry point used only for testing purposes.
It has an example of how to use the API methods.
This does not call the HTTP endpoints directly, instead it imports the api methods from backend/api.py.

If you are looking for the implementation of the API methods, check the backend/api.py file.
If you are looking for the HTTP endpoints, check the backend/views.py file.
If you are looking for managing the database, check the manage.py file.
"""

import django, os, sys
from django.forms import ValidationError
from setup.logger import log
import traceback

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# The modules below contain the main logic
from backend.api import checkin, checkout, create_borrower, search_loans
from reset import clear_database, import_data


def main():
    # Comment this out if you want to skip: Clears the database
    # clear_database()
    # Comment this out if you want to skip: Imports the data into the database
    # import_data()

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

    # Example of the checkout_book method
    try:
        loan_id = checkout(card_id, "9780195153445")
        log.info(f"Book checked out: Loan {loan_id}")
    except Exception as e:
        log.error(f"Error checking out book: {e}\n{traceback.format_exc()}")
        return

    loan_id: str = None
    try:
        # Example of the search_loans method
        loans = search_loans(card_id, "9780195153445")
        log.info(f"Loans found: {len(loans)} loans")
        if loans:
            # First loan that does not have a date_in
            for loan in loans:
                if loan[5] is None:
                    loan_id = loan[0]
                    break
    except Exception as e:
        log.error(f"Error searching loans: {e}\n{traceback.format_exc()}")
        return

    try:
        # Example of the checkin method
        checkin(loan_id)
        log.info(f"Book checked in: Loan {loan_id}")
    except Exception as e:
        log.error(f"Error checking in book: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
