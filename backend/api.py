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


def create_borrower(ssn: str, bname: str, address: str, phone: str = None) -> Optional[Tuple]:
    """
    Create a new borrower using raw SQL.

    Returns:
        Tuple: (card_no, bname) if created successfully
        None: if duplicate SSN or error
    """
    try:
        with connection.cursor() as cursor:
            # Check for duplicate SSN
            cursor.execute("SELECT card_id FROM borrower WHERE ssn = %s", [ssn])
            if cursor.fetchone():
                print(f"Borrower with SSN {ssn} already exists.")
                return None

            # Generate new card_id
            cursor.execute("SELECT MAX(CAST(card_id AS UNSIGNED)) FROM borrower")
            result = cursor.fetchone()
            next_card_id = (int(result[0]) + 1) if result[0] else 10000000
            card_id_str = str(next_card_id).zfill(8)

            # Insert new borrower
            cursor.execute("""
                INSERT INTO borrower (card_id, ssn, bname, address, phone)
                VALUES (%s, %s, %s, %s, %s)
            """, [card_id_str, ssn, bname, address, phone])

            return (card_id_str, bname)

    except Exception as e:
        print(f"Error creating borrower: {e}")
        return None
