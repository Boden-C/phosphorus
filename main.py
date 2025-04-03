"""
This is the entry point used only for testing purposes.
It has an example of how to use the API methods.
This does not call the HTTP endpoints directly, instead it imports the api methods from backend/api.py.

If you are looking for the implementation of the API methods, check the backend/api.py file.
If you are looking for the HTTP endpoints, check the backend/views.py file.
If you are looking for managing the database, check the manage.py file.
"""

from backend.api import create_borrower

def main():
    # Example data for creating a borrower
    ssn = "123-45-6789"
    bname = "John Doe"
    address = "123 Main St, Springfield, IL"
    phone = "555-1234"
    email = "johndole@gmail.com"
    
    try:
        # Call the create_borrower method from the API
        borrower = create_borrower(ssn, bname, address, phone, email)
        print("Borrower created successfully:", borrower)
    except Exception as e:
        print("Error creating borrower:", str(e))