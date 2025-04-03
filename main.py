"""
This is the entry point used only for testing purposes.
It has an example of how to use the API methods.
This does not call the HTTP endpoints directly, instead it imports the api methods from backend/api.py.

If you are looking for the implementation of the API methods, check the backend/api.py file.
If you are looking for the HTTP endpoints, check the backend/views.py file.
If you are looking for managing the database, check the manage.py file.
"""

import django, os, sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# The modules below contain the main logic
from backend.api import create_borrower
from reset import clear_database, import_data
from setup.logger import log


def main():
    # Comment this out if you want to skip: Clears the database
    clear_database()
    # Comment this out if you want to skip: Imports the data into the database
    import_data()

    # Example of the create_borrower method
    try:
        card_id, bname = create_borrower("123456789", "John Doe", "123 Main St", "555-5555")
        log.info(f"Borrower created: {card_id}, {bname}")
    except Exception as e:
        log.error(f"Error creating borrower: {e}")


if __name__ == "__main__":
    main()
