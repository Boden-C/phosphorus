"""
The logic for handling requests and responses in the backend of the application.
This contains all the methods that interact with the database and can be imported for usage in other files.

Contains:
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
 - create_borrower(card_id: str, ssn: str, bname: str, address: str, phone: str = None) -> Tuple[str, str]
 - create_librarian(username: str, password: str) -> Tuple[str, str]
 - create_user(id: str, username: str, password: str, group: str) -> Tuple[str, str]
 - create_book(isbn: str, title: str) -> Tuple[str, str]
 - create_junction(author_id: str, isbn: str) -> Tuple[str, str]
 - create_author(author_name: str) -> Tuple[str, str]
"""

from datetime import date
import decimal
from typing import List, Tuple, Dict, Optional
from django.db import connection, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group


def search_books(query: str) -> List[Tuple]:
    """
    Search for books by title, ISBN, or author name.

    Args:
        query (str): The search string to look for in books or authors

    Returns:
        List[Tuple]: A list of tuples (isbn, title, author_names) if results are found

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT B.isbn, B.title, GROUP_CONCAT(A.name SEPARATOR ', ') AS authors
            FROM BOOK B
            LEFT JOIN BOOK_AUTHORS BA ON B.isbn = BA.isbn
            LEFT JOIN AUTHORS A ON BA.author_id = A.author_id
            WHERE B.title LIKE %s OR B.isbn LIKE %s OR A.name LIKE %s
            GROUP BY B.isbn, B.title
            """,
            [f"%{query}%", f"%{query}%", f"%{query}%"],
        )
        return cursor.fetchall()


def checkout(card_id: str, isbn: str) -> str:
    """
    Attempt to check out a book for a borrower.

    Args:
        card_id (str): The card ID of the borrower
        isbn (str): The ISBN of the book to check out

    Returns:
        str: loan_id if successful

    Raises:
        ValidationError: If borrower has 3 active loans, unpaid fines, or book not available
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Check if borrower has 3 active loans
        cursor.execute(
            """
            SELECT COUNT(*) FROM BOOK_LOANS
            WHERE card_id = %s AND date_in IS NULL;
            """,
            [card_id],
        )
        active_loans = cursor.fetchone()[0]

        if active_loans >= 3:
            raise ValidationError("Checkout failed: Borrower has 3 active loans.")

        # Check if borrower has unpaid fines
        cursor.execute(
            """
            SELECT COALESCE(SUM(F.fine_amt), 0)
            FROM FINES F
            JOIN BOOK_LOANS BL ON F.Loan_id = BL.Loan_id
            WHERE BL.Card_id = %s
            AND F.Paid = FALSE;
            """,
            [card_id],
        )
        fine_due = cursor.fetchone()[0]

        if fine_due > 0:
            raise ValidationError("Checkout failed: Borrower has unpaid fines.")

        # Check if the book is available by comparing number of copies to number of checked out copies
        cursor.execute(
            """
            SELECT 
                (SELECT COUNT(*) FROM BOOK WHERE isbn = %s) AS total_copies,
                (SELECT COUNT(*) FROM BOOK_LOANS WHERE isbn = %s AND date_in IS NULL) AS checked_out_copies
            """,
            [isbn, isbn],
        )
        result = cursor.fetchone()
        total_copies = result[0]
        checked_out_copies = result[1]

        if total_copies == 0:
            raise ValidationError("Checkout failed: Book not found.")

        if checked_out_copies >= total_copies:
            raise ValidationError("Checkout failed: No copies available.")

        # Insert new book loan
        cursor.execute(
            """
            INSERT INTO BOOK_LOANS (isbn, card_id, date_out, due_date)
            VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
            """,
            [isbn, card_id],
        )

        # Get the loan_id of the newly created loan
        cursor.execute(
            """
            SELECT loan_id FROM BOOK_LOANS
            ORDER BY loan_id DESC LIMIT 1;
            """
        )

        return cursor.fetchone()[0]


def search_loans(card_id: str, query: str) -> List[Tuple]:
    """
    Search book loans by user ID or book information.

    Args:
        card_id (str): The card ID of the borrower
        query (str): Search string to match against ISBN or borrower name

    Returns:
        List[Tuple]: A list of tuples (loan_id, isbn, card_id, date_out, due_date, date_in) if results

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT loan_id, isbn, BORROWER.card_id, date_out, due_date, date_in
            FROM BOOK_LOANS
            JOIN BORROWER ON BOOK_LOANS.card_id = BORROWER.card_id
            WHERE BOOK_LOANS.card_id = %s 
                AND (BOOK_LOANS.isbn LIKE %s
                    OR BORROWER.bname LIKE %s);
        """,
            [card_id, f"%{query}%", f"%{query}%"],
        )
        return cursor.fetchall()


def checkin(loan_id: str) -> str:
    """
    Check in a book by updating its return date.

    Args:
        loan_id (str): The ID of the loan to check in

    Returns:
        str: loan_id if successful

    Raises:
        ValidationError: If no active loan is found
        Exception: If a database error occurs
    """
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
            raise ValidationError("Check-in failed: Loan ID not found or already checked in.")

        # Update the book loan record to mark as checked in
        cursor.execute(
            """
            UPDATE BOOK_LOANS
            SET date_in = CURDATE()
            WHERE loan_id = %s;
            """,
            [loan_id],
        )

        return loan_id


def get_fines(card_ids: list = [], include_paid: bool = False, sum: bool = False) -> List[Tuple]:
    """
    Get list of fines, optionally filtered by borrowers.

    Args:
        card_ids (list): List of card IDs to filter by (empty list for all borrowers)
        include_paid (bool): Whether to include paid fines (default: False)
        sum (bool): Whether to sum fines by borrower (default: False)

    Returns:
        List[Tuple]: A list of fine records or sum by borrower

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        if sum:
            query = """
                SELECT bl.card_id, COALESCE(SUM(f.fine_amt), 0) AS total_fine
                FROM FINES f
                JOIN BOOK_LOANS bl ON f.loan_id = bl.loan_id
                WHERE 1=1
            """
            params = []

            if not include_paid:
                query += " AND f.paid = FALSE"

            if card_ids:
                placeholders = ", ".join(["%s"] * len(card_ids))
                query += f" AND bl.card_id IN ({placeholders})"
                params.extend(card_ids)

            query += " GROUP BY bl.card_id ORDER BY bl.card_id"

            cursor.execute(query, params)
        else:
            query = """
                SELECT 
                    f.loan_id, 
                    bl.card_id,
                    f.fine_amt, 
                    f.paid,
                    b.title,
                    bl.due_date,
                    bl.date_in
                FROM FINES f
                JOIN BOOK_LOANS bl ON f.loan_id = bl.loan_id
                JOIN BOOK b ON bl.isbn = b.isbn
                WHERE 1=1
            """
            params = []

            if not include_paid:
                query += " AND f.paid = FALSE"

            if card_ids:
                placeholders = ", ".join(["%s"] * len(card_ids))
                query += f" AND bl.card_id IN ({placeholders})"
                params.extend(card_ids)

            query += " ORDER BY bl.card_id, f.paid, bl.due_date"

            cursor.execute(query, params)

        return cursor.fetchall()


def get_user_fines(card_id: str, include_paid: bool = False) -> decimal.Decimal:
    """
    Get the total sum of fines for a specific borrower.

    Args:
        card_id (str): The card ID of the borrower
        include_paid (bool): Whether to include paid fines (default: False)

    Returns:
        decimal.Decimal: The sum of fines for the specified borrower

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        query = """
            SELECT COALESCE(SUM(f.fine_amt), 0) AS total_fine
            FROM FINES f
            JOIN BOOK_LOANS bl ON f.loan_id = bl.loan_id
            WHERE bl.card_id = %s
        """
        params = [card_id]

        if not include_paid:
            query += " AND f.paid = FALSE"

        cursor.execute(query, params)
        result = cursor.fetchone()
        return decimal.Decimal(result[0]) if result else decimal.Decimal("0.00")


def get_fines_dict(card_ids: list = [], include_paid: bool = False) -> Dict[str, decimal.Decimal]:
    """
    Get dictionary of fines summed by borrower.

    Args:
        card_ids (list): List of card IDs to filter by (empty list for all borrowers)
        include_paid (bool): Whether to include paid fines (default: False)

    Returns:
        Dict[str, decimal.Decimal]: Dictionary mapping card_id to total fine amount

    Raises:
        Exception: If a database error occurs
    """
    fines_result = get_fines(card_ids=card_ids, include_paid=include_paid, sum=True)
    return {card_id: decimal.Decimal(amount) for card_id, amount in fines_result}


def pay_loan_fine(loan_id: str) -> dict:
    """
    Process payment for a single loan's fine.

    Args:
        loan_id (str): The ID of the loan to pay

    Returns:
        dict: Dictionary with payment confirmation

    Raises:
        ValidationError: If book isn't returned or fine already paid
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Verify book was returned
        cursor.execute(
            """
            SELECT date_in FROM BOOK_LOANS
            WHERE loan_id = %s
            """,
            [loan_id],
        )
        result = cursor.fetchone()

        if not result or result[0] is None:
            raise ValidationError("Cannot pay fine - book not yet returned")

        # Verify fine exists and isn't paid
        cursor.execute(
            """
            SELECT fine_amt FROM FINES
            WHERE loan_id = %s AND paid = FALSE
            """,
            [loan_id],
        )
        fine = cursor.fetchone()

        if not fine:
            raise ValidationError("No unpaid fine found for this loan")

        # Mark fine as paid
        cursor.execute(
            """
            UPDATE FINES
            SET paid = TRUE
            WHERE loan_id = %s
            """,
            [loan_id],
        )

        return {"loan_id": loan_id, "amount_paid": float(fine[0]), "message": f"Paid ${fine[0]:.2f} for loan {loan_id}"}


def pay_borrower_fines(card_id: str) -> dict:
    """
    Process payment for all unpaid fines of a borrower.

    Args:
        card_id (str): Borrower's card ID

    Returns:
        dict: Dictionary with payment summary

    Raises:
        ValidationError: If borrower has unreturned books or no fines
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Check for unreturned books
        cursor.execute(
            """
            SELECT f.loan_id, f.fine_amt
            FROM FINES f
            JOIN BOOK_LOANS bl ON f.loan_id = bl.loan_id
            WHERE bl.card_id = %s
              AND bl.date_in IS NOT NULL
              AND f.paid = FALSE
            """,
            [card_id],
        )
        fines = cursor.fetchall()

        if not fines:
            raise ValidationError("No payable fines found")

        # Pay each fine individually
        total = decimal.Decimal("0.00")
        for loan_id, amount in fines:
            cursor.execute(
                """
                UPDATE FINES
                SET paid = TRUE
                WHERE loan_id = %s
                """,
                [loan_id],
            )
            total += amount

        return {
            "card_id": card_id,
            "total_paid": float(total),
            "fines_paid": len(fines),
            "message": f"Paid ${total:.2f} for {len(fines)} loans",
        }


def update_fines(current_date: date = date.today()) -> None:
    """
    Update the FINES table for late books based on the current date.

    - Fines are $0.25 per day.
    - Inserts new fines for late loans without records.
    - Updates existing unpaid fines if the amount differs.
    - Ignores paid fines.

    Args:
        current_date (date): The date used to calculate fines for unreturned books.

    Raises:
        Exception: If a database error occurs
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Fetch all late loans with their fine status
            sql = """
            SELECT bl.Loan_id, bl.Due_date, bl.Date_in, f.Fine_amt, f.Paid
            FROM BOOK_LOANS bl
            LEFT JOIN 
                FINES f ON bl.Loan_id = f.Loan_id
            WHERE 
                (bl.Date_in IS NOT NULL AND bl.Date_in > bl.Due_date) 
                OR (bl.Date_in IS NULL AND bl.Due_date < %s)
            """
            cursor.execute(sql, [current_date])
            loans = cursor.fetchall()

            # Process loans in Python and prepare bulk operations
            final_inserts: List[Tuple[int, float, bool]] = []  # (Loan_id, Fine_amt, Paid)
            final_updates: List[Tuple[float, int]] = []  # (Fine_amt, Loan_id)

            for loan in loans:
                loan_id, due_date, date_in, existing_fine, paid = loan
                paid = paid if paid is not None else False

                # Calculate the fine
                days_late = (date_in - due_date).days if date_in else (current_date - due_date).days
                calculated_fine = max(days_late, 0) * 0.25

                # If no fine, then insert a new fine
                if existing_fine is None:
                    final_inserts.append((loan_id, calculated_fine, False))

                # If fine exists and the calculated fine is different, update it
                elif not paid and existing_fine != calculated_fine:
                    final_updates.append((calculated_fine, loan_id))

            # Execute the inserts and updates
            if final_inserts:
                insert_sql = """
                INSERT INTO FINES (Loan_id, Fine_amt, Paid)
                VALUES (%s, %s, %s)
                """
                cursor.executemany(insert_sql, final_inserts)
            if final_updates:
                update_sql = """
                UPDATE FINES
                SET Fine_amt = %s
                WHERE Loan_id = %s
                """
                cursor.executemany(update_sql, final_updates)


def create_user(id: str, username: str, password: str, group: str) -> Tuple[str, str]:
    """
    Create a new Django user and assign it to a group. If the username exists, append a number to make it unique.

    Args:
        id (str): Unique identifier for the user (card_id for borrowers, staff_id for librarians)
        username (str): Username for login
        password (str): Password for login
        group (str): Group name to assign the user to ("Borrowers" or "Librarians")

    Returns:
        Tuple[str, str]: Tuple containing (id, username)

    Raises:
        ValidationError: If user creation fails
    """
    base_username = username
    suffix = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{suffix}"
        suffix += 1
    try:
        is_staff = group == "Librarians"
        user = User.objects.create_user(username=username, password=password, is_staff=is_staff)
        try:
            group_obj = Group.objects.get(name=group)
            user.groups.add(group_obj)
        except Group.DoesNotExist:
            group_obj = Group.objects.create(name=group)
            user.groups.add(group_obj)
        return (id, username)
    except Exception as e:
        User.objects.filter(username=username).delete()
        raise ValidationError(f"Failed to create user: {str(e)}")


def create_librarian(username: str, password: str) -> Tuple[str, str]:
    """
    Create a new librarian user.

    Args:
        username (str): Username for login
        password (str): Password for login

    Returns:
        Tuple[str, str]: Tuple containing (staff_id, username)

    Raises:
        ValidationError: If username already exists
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Generate new staff_id
        cursor.execute(
            "SELECT MAX(CAST(SUBSTRING(username, 5) AS UNSIGNED)) FROM auth_user WHERE username LIKE 'lib_%'"
        )
        result = cursor.fetchone()
        next_id = (int(result[0]) + 1) if result[0] else 10000
        staff_id = str(next_id)

        # Create user with librarian privileges
        return create_user(staff_id, username, password, "Librarians")


def create_borrower(card_id: str, ssn: str, bname: str, address: str, phone: str = None) -> Tuple[str, str]:
    """
    Create a new borrower record.

    Args:
        card_id (str): Card ID for the borrower
        ssn (str): Social Security Number or other identifier
        bname (str): Borrower name
        address (str): Borrower address
        phone (str, optional): Borrower phone number

    Returns:
        Tuple[str, str]: A tuple containing (card_id, borrower_name)

    Raises:
        ValidationError: If borrower with SSN already exists or the card_id is already in use
    """
    with connection.cursor() as cursor:
        # Check if borrower with SSN already exists
        cursor.execute(
            "SELECT card_id FROM borrower WHERE ssn = %s",
            [ssn],
        )
        if cursor.fetchone():
            raise ValidationError(f"Borrower with SSN {ssn} already exists")

        # Check if card_id is already in use
        cursor.execute(
            "SELECT card_id FROM borrower WHERE card_id = %s",
            [card_id],
        )
        if cursor.fetchone():
            raise ValidationError(f"Card ID {card_id} is already in use")

        # Insert new borrower with provided card_id
        cursor.execute(
            """
            INSERT INTO borrower (card_id, ssn, bname, address, phone)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [card_id, ssn, bname, address, phone or ""],
        )

        return card_id, bname


def create_book(isbn: str, title: str) -> Tuple[str, str]:
    """
    Create a new book record.

    Args:
        isbn (str): International Standard Book Number
        title (str): Book title

    Returns:
        Tuple[str, str]: Tuple containing (isbn, title)

    Raises:
        Exception: If a database error occurs
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
        author_name (str): Author's name

    Returns:
        Tuple[str, str]: Tuple containing (author_id, author_name)

    Raises:
        Exception: If a database error occurs
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
        author_id (str): Author's ID
        isbn (str): Book's ISBN

    Returns:
        Tuple[str, str]: Tuple containing (author_id, isbn)

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Insert new junction entry
        cursor.execute(
            "INSERT INTO BOOK_AUTHORS (Author_id, Isbn) VALUES (%s, %s)",
            [author_id, isbn],
        )
        return (author_id, isbn)
