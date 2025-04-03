"""
The logic for handling requests and responses in the backend of the application.
This contains all the methods that interacts with the database and can be imported for usage in other files.

Contains:
 - search_books(query:str)
 - checkout(user_id:str, isbn:str)
 - search_loans(user_id:str, query:str)
 - checkin(loan_id:str)
 - create_borrower(...)
 - update_fines()
"""

from typing import Optional, Tuple
from django.db import connection


def create_borrower(ssn: str, bname: str, address: str, phone: str = None, email: str = None) -> Optional[Tuple]:
    """
    Create a new borrower in the database.

    Args:
        ssn (str): The social security number of the borrower.
        bname (str): The name of the borrower.
        address (str): The address of the borrower.
        phone (str, optional): The phone number of the borrower. Defaults to None.
        email (str, optional): The email address of the borrower. Defaults to None.

    Returns:
        Optional[Tuple]: A tuple containing the borrower if created successfully.

    Raises:
        Exception: If there is an error while creating the borrower.
    """
