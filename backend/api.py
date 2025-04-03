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


def checkout(user_id: str, isbn: str) -> str:
    """ Attempt to check out a book for a borrower """
    with connection.cursor() as cursor:
        # Check if borrower has 3 active loans
        cursor.execute("""
            SELECT COUNT(*) FROM BOOK_LOANS
            WHERE card_id = %s AND date_in IS NULL;
            """), [user_id]
        active_loans = cursor.fetchone()[0]

        if active_loans >= 3:
            return 'Checkout failed: Borrower has already reached the maximum limit of 3 books.'

        # Check if borrower has unpaid fines
        cursor.execute("""
            SELECT COALESCE(SUM(fine_amt), 0) FROM FINES
            WHERE card_id = %s AND paid = FALSE;
            """), [user_id]
        fine_due = cursor.fetchone()[0]

        if fine_due > 0:
            return 'Checkout failed: Borrower has unpaid fines.'

        # Check if the book is available
        cursor.execute("""
            SELECT COUNT(*) FROM BOOK_LOANS
            WHERE isbn = %s AND date_in IS NULL;
            """), [isbn]
        book_available = cursor.fetchone()[0]

        if book_available > 0:
            return 'Checkout failed: Book is currently checked out.'

        # Insert new book loan
        cursor.execute("""
            INSERT INTO BOOK_LOANS (isbn, card_id, date_out, due_date)
            VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
            """), [isbn, user_id]

        return 'Checkout successful.'


def search_loans(user_id: str, query: str) -> List[Tuple]:
    """ Search book loans by user ID or book information"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT loan_id, isbn, card_no, date_out, due_date, date_in
            FROM BOOK_LOANS
            JOIN BORROWER ON BOOK_LOANS.card_id = BORROWER.card_id
            WHERE BOOK_LOANS.card_id = %s 
                AND (BOOK_LOANS.isbn LIKE %s
                    OR BORROWER.bname LIKE %s);
        """, [user_id, f'%{query}%', f'%{query}%'])
        return cursor.fetchall()


def checkin(loan_id: str) -> str:
    """ Check in a book by updating its return date."""
    with connection.cursor() as cursor:
        # Check if the loan exists and is still active
        cursor.execute("""
            SELECT COUNT(*) FROM BOOK_LOANS
            WHERE loan_id = %s AND date_in IS NULL;
        """, [loan_id])

        loan_exists = cursor.fetchone()[0]

        if loan_exists == 0:
            return 'Check-in failed: No active loan found for this loan ID'

        # Update the book loan record to mark as checked in
        cursor.execute("""
            UPDATE BOOK_LOANS
            SET date_in = CURDATE()
            WHERE loan_id = %s;
        """, [loan_id])

        return 'Check-in successful.'
