"""
The logic for handling requests and responses in the backend of the application.
This contains all the methods that interacts with the database and can be imported for usage in other files.

Contains:
 - search_books(query:str)
 - checkout(user_id:str, isbn:str)
 - search_loans(user_id:str, query:str)
 - checkin(loan_id:str)
 - update_fines()
 - create_borrower(...)
 - create_book(...)
 - create_junction(...)
 - create_author(...)
"""

from typing import List, Tuple
from django.db import connection
from django.core.exceptions import ValidationError


def checkout(user_id: str, isbn: str) -> str:
    """Attempt to check out a book for a borrower"""
    with connection.cursor() as cursor:
        # Check if borrower has 3 active loans
        cursor.execute(
            """
            SELECT COUNT(*) FROM BOOK_LOANS
            WHERE card_id = %s AND date_in IS NULL;
            """,
            [user_id],
        )
        active_loans = cursor.fetchone()[0]

        if active_loans >= 3:
            return "Checkout failed: Borrower has already reached the maximum limit of 3 books."

        # Check if borrower has unpaid fines
        cursor.execute(
            """
            SELECT COALESCE(SUM(fine_amt), 0) FROM FINES
            WHERE loan_id = %s AND paid = FALSE;
            """,
            [user_id],
        )
        fine_due = cursor.fetchone()[0]

        if fine_due > 0:
            return "Checkout failed: Borrower has unpaid fines."

        # Check if the book is available
        cursor.execute(
            """
            SELECT COUNT(*) FROM BOOK_LOANS
            WHERE isbn = %s AND date_in IS NULL;
            """,
            [user_id],
        )
        book_available = cursor.fetchone()[0]

        if book_available > 0:
            return "Checkout failed: Book is currently checked out."

        # Insert new book loan
        cursor.execute(
            """
            INSERT INTO BOOK_LOANS (isbn, card_id, date_out, due_date)
            VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
            """,
            [isbn, user_id],
        )

        return "Checkout successful."


def search_loans(user_id: str, query: str) -> List[Tuple]:
    """Search book loans by user ID or book information"""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT loan_id, isbn, card_no, date_out, due_date, date_in
            FROM BOOK_LOANS
            JOIN BORROWER ON BOOK_LOANS.card_id = BORROWER.card_id
            WHERE BOOK_LOANS.card_id = %s 
                AND (BOOK_LOANS.isbn LIKE %s
                    OR BORROWER.bname LIKE %s);
        """,
            [user_id, f"%{query}%", f"%{query}%"],
        )
        return cursor.fetchall()


def checkin(loan_id: str) -> str:
    """Check in a book by updating its return date."""
    with connection.cursor() as cursor:
        # Check if the loan exists and is still active
        cursor.execute(
            """
            SELECT COUNT(*) FROM BOOK_LOANS
            WHERE loan_id = %s AND date_in IS NULL;
        """,
            [loan_id],
        )

        loan_exists = cursor.fetchone()[0]

        if loan_exists == 0:
            return "Check-in failed: No active loan found for this loan ID"

        # Update the book loan record to mark as checked in
        cursor.execute(
            """
            UPDATE BOOK_LOANS
            SET date_in = CURDATE()
            WHERE loan_id = %s;
        """,
            [loan_id],
        )

        return "Check-in successful."


def create_borrower(ssn: str, bname: str, address: str, phone: str = None) -> Tuple[str, str]:
    """
    Create a new borrower record.

    Args:
        ssn: Social security number
        bname: Borrower name
        address: Borrower address
        phone: Optional phone number

    Returns:
        Tuple containing (card_id, bname)

    Raises:
        ValidationError: If borrower with SSN already exists
        DatabaseError: If database operation fails
    """
    with connection.cursor() as cursor:
        # Check for duplicate SSN
        cursor.execute(
            "SELECT card_id FROM borrower WHERE ssn = %s",
            [ssn],
        )
        if cursor.fetchone():
            raise ValidationError(f"Borrower with SSN {ssn} already exists")

        # Generate new card_id
        cursor.execute("SELECT MAX(CAST(card_id AS UNSIGNED)) FROM borrower")
        result = cursor.fetchone()
        next_card_id = (int(result[0]) + 1) if result[0] else 10000000
        card_id_str = str(next_card_id).zfill(8)

        # Insert new borrower
        cursor.execute(
            """
            INSERT INTO borrower (card_id, ssn, bname, address, phone)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [card_id_str, ssn, bname, address, phone],
        )
        return (card_id_str, bname)


def create_book(isbn: str, title: str) -> Tuple[str, str]:
    """
    Create a new book record.

    Args:
        isbn: International Standard Book Number
        title: Book title

    Returns:
        Tuple containing (isbn, title)

    Raises:
        DatabaseError: If database operation fails
    """
    with connection.cursor() as cursor:
        # Insert new book
        cursor.execute(
            "INSERT INTO BOOK (Isbn, Title) VALUES (%s, %s)",
            [isbn, title],
        )
        return (isbn, title)


def create_author(author_name: str) -> Tuple[str, str]:
    """
    Create a new author record.

    Args:
        author_name: Author's name

    Returns:
        Tuple containing (author_id, author_name)

    Raises:
        ValidationError: If author with same name already exists
        DatabaseError: If database operation fails
    """
    with connection.cursor() as cursor:
        # Generate new author_id
        cursor.execute("SELECT MAX(CAST(Author_id AS UNSIGNED)) FROM AUTHORS")
        result = cursor.fetchone()
        next_author_id = str((int(result[0]) + 1) if result[0] else 1)

        # Insert new author
        cursor.execute(
            "INSERT INTO AUTHORS (Author_id, Name) VALUES (%s, %s)",
            [next_author_id, author_name],
        )
        return (next_author_id, author_name)


def create_junction(author_id: str, isbn: str) -> Tuple[str, str]:
    """
    Create a new book-author junction record.

    Args:
        author_id: Author's ID
        isbn: Book's ISBN

    Returns:
        Tuple containing (author_id, isbn)

    Raises:
        ValidationError: If junction entry already exists
        DatabaseError: If database operation fails
    """
    with connection.cursor() as cursor:
        # Insert new junction entry
        cursor.execute(
            "INSERT INTO BOOK_AUTHORS (Author_id, Isbn) VALUES (%s, %s)",
            [author_id, isbn],
        )
        return (author_id, isbn)
