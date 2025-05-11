"""
Library management system API implementation.

This module provides all core functionality for the library management system, including:
 - search_books(query: Query) -> Results[Book]
 - search_books_with_loan(query: Query) -> Results[Tuple[Book, Optional[Loan]]]
 - get_book(isbn: str) -> Book
 - search_loans(query: Query) -> Results[Loan]
 - search_loans_with_book(query: Query) -> Results[Tuple[Loan, Book]]
 - search_borrowers(query: Query) -> Results[Borrower]
 - search_borrowers_with_fines(card_id: str, query: Query) -> Results[Tuple[Borrower, Decimal]]
 - checkout(card_id: str, isbn: str) -> Loan
 - checkin(loan_id: str) -> Loan
 - get_user_fines(card_id: str, include_paid: bool = False) -> Decimal
 - get_fines(card_ids:list = [], include_paid: bool = False, sum: bool = False) -> List[Loan]
 - get_fines_grouped(card_ids:list = [], include_paid: bool = False) -> Dict[str, Decimal]
 - pay_loan_fine(loan_id: str) -> Loan
 - pay_borrower_fines(card_id: str) -> List[Loan]
 - update_fines(current_date: date = date.today()) -> None
 - create_borrower(ssn: str, bname: str, address: str, phone: str = None, card_id: str = None) -> Borrower
 - create_librarian(username: str, password: str) -> User
 - create_user(username: str, password: str, group: str) -> User
 - create_book(isbn: str, title: str, authors: List[str] = []) -> Book
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from django.db import connection, transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.models import User, Group

from .query import Query, Results, OrderDirection, LoanStatus, DueStatus, FineStatus
from .utils import Book, Loan, Borrower, parse_date, parse_authors

MAX_ACTIVE_LOANS = 3
LOAN_DURATION_DAYS = 14


def search_books(query: Query) -> Results[Book]:
    """
    Search for books with filtering and pagination.

    Supported query keywords:
        isbn: Filter by book ISBN
        title: Filter by book title
        author: Filter by book author
        sort: Sort by (isbn, title, author)
        order: Sort direction (asc, desc)
        limit: Maximum results per page
        page: Page number
        any_term: Search across all text fields

    Args:
        query: Query object containing search parameters and filters

    Returns:
        Results[Book]: Paginated results of books

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Build the WHERE clause based on the query filters
        where_clauses = []
        params = []

        if query.isbn:
            where_clauses.append("B.isbn LIKE %s")
            params.append(f"%{query.isbn}%")

        if query.title:
            where_clauses.append("B.title LIKE %s")
            params.append(f"%{query.title}%")

        if query.author:
            where_clauses.append("A.name LIKE %s")
            params.append(f"%{query.author}%")

        if query.any_term:
            where_clauses.append("(B.title LIKE %s OR B.isbn LIKE %s OR A.name LIKE %s)")
            params.extend([f"%{query.any_term}%", f"%{query.any_term}%", f"%{query.any_term}%"])

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(DISTINCT B.isbn)
            FROM BOOK B
            LEFT JOIN BOOK_AUTHORS BA ON B.isbn = BA.isbn
            LEFT JOIN AUTHORS A ON BA.author_id = A.author_id
            WHERE {where_clause}
        """

        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Build main query with sorting and pagination
        main_query = f"""
            SELECT 
                B.isbn, 
                B.title, 
                GROUP_CONCAT(DISTINCT A.name SEPARATOR '\u001f') AS authors
            FROM BOOK B
            LEFT JOIN BOOK_AUTHORS BA ON B.isbn = BA.isbn
            LEFT JOIN AUTHORS A ON BA.author_id = A.author_id
            WHERE {where_clause}
            GROUP BY B.isbn, B.title
        """

        # Add sorting
        if query.sort:
            sort_field = query.sort.lower()
            direction = "DESC" if query.order == OrderDirection.DESCENDING else "ASC"

            if sort_field == "isbn":
                main_query += f" ORDER BY B.isbn {direction}"
            elif sort_field == "title":
                main_query += f" ORDER BY B.title {direction}"
            elif sort_field == "author":
                main_query += f" ORDER BY authors {direction}"
            else:
                # Default sort
                main_query += f" ORDER BY B.title {direction}"
        else:
            # Default sort
            main_query += " ORDER BY B.title ASC"

        # Add pagination
        if query.limit is not None:
            offset = (query.page - 1) * query.limit
            main_query += " LIMIT %s OFFSET %s"
            params.extend([query.limit, offset])

        cursor.execute(main_query, params)

        books = []
        for row in cursor.fetchall():
            isbn, title, author_str = row
            authors = parse_authors(author_str)
            books.append(Book(isbn=isbn, title=title, authors=authors))

        return Results(items=books, total=total_count, page_limit=query.limit, current_page=query.page)


def search_books_with_loan(query: Query) -> Results[Tuple[Book, Optional[Loan]]]:
    """
    Search for books with their current loan status.

    Supported query keywords:
        isbn: Filter by book ISBN
        title: Filter by book title
        author: Filter by book author
        borrower: Filter by borrower name
        card: Filter by card ID
        available: Filter by availability (true/false)
        loan_is: Filter by loan status (active/returned)
        fine_is: Filter by fine status (owed/paid)
        due: Filter by due date (past/future)
        sort: Sort by (isbn, title, author)
        order: Sort direction (asc, desc)
        limit: Maximum results per page
        page: Page number
        any_term: Search across all text fields

    Args:
        query: Query object containing search parameters and filters

    Returns:
        Results[Tuple[Book, Optional[Loan]]]: Paginated results with books and their loan status

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        where_clauses = []
        params = []

        # Apply filters from query
        if query.isbn:
            where_clauses.append("B.isbn LIKE %s")
            params.append(f"%{query.isbn}%")

        if query.title:
            where_clauses.append("B.title LIKE %s")
            params.append(f"%{query.title}%")

        if query.author:
            where_clauses.append("A.name LIKE %s")
            params.append(f"%{query.author}%")

        if query.any_term:
            where_clauses.append("(B.title LIKE %s OR B.isbn LIKE %s OR A.name LIKE %s)")
            params.extend([f"%{query.any_term}%", f"%{query.any_term}%", f"%{query.any_term}%"])

        # Filter by availability if specified
        if query.available is not None:
            if query.available:
                where_clauses.append("(BL.loan_id IS NULL OR BL.date_in IS NOT NULL)")
            else:
                where_clauses.append("(BL.loan_id IS NOT NULL AND BL.date_in IS NULL)")

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(DISTINCT B.isbn)
            FROM BOOK B
            LEFT JOIN BOOK_AUTHORS BA ON B.isbn = BA.isbn
            LEFT JOIN AUTHORS A ON BA.author_id = A.author_id
            LEFT JOIN (
                SELECT * FROM BOOK_LOANS
                WHERE date_in IS NULL
            ) AS BL ON B.isbn = BL.isbn
            WHERE {where_clause}
        """

        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Build main query with sorting and pagination
        main_query = f"""
            SELECT 
                B.isbn, 
                B.title, 
                GROUP_CONCAT(DISTINCT A.name SEPARATOR '\u001f') AS authors,
                BL.loan_id,
                BL.card_id,
                BL.date_out,
                BL.due_date,
                BL.date_in,
                COALESCE(F.fine_amt, 0) as fine_amt,
                COALESCE(F.paid, FALSE) as paid
            FROM BOOK B
            LEFT JOIN BOOK_AUTHORS BA ON B.isbn = BA.isbn
            LEFT JOIN AUTHORS A ON BA.author_id = A.author_id
            LEFT JOIN (
                SELECT * FROM BOOK_LOANS
                WHERE date_in IS NULL
            ) AS BL ON B.isbn = BL.isbn
            LEFT JOIN FINES F ON BL.loan_id = F.loan_id
            WHERE {where_clause}
            GROUP BY B.isbn, B.title, BL.loan_id, BL.card_id, BL.date_out, 
                     BL.due_date, BL.date_in, fine_amt, paid
        """

        # Add sorting
        if query.sort:
            sort_field = query.sort.lower()
            direction = "DESC" if query.order == OrderDirection.DESCENDING else "ASC"

            if sort_field == "isbn":
                main_query += f" ORDER BY B.isbn {direction}"
            elif sort_field == "title":
                main_query += f" ORDER BY B.title {direction}"
            elif sort_field == "author":
                main_query += f" ORDER BY authors {direction}"
            else:
                # Default sort
                main_query += f" ORDER BY B.title {direction}"
        else:
            # Default sort
            main_query += " ORDER BY B.title ASC"

        # Add pagination
        if query.limit is not None:
            offset = (query.page - 1) * query.limit
            main_query += " LIMIT %s OFFSET %s"
            params.extend([query.limit, offset])

        cursor.execute(main_query, params)

        results = []
        for row in cursor.fetchall():
            isbn, title, author_str, loan_id, card_id, date_out, due_date, date_in, fine_amt, paid = row
            authors = parse_authors(author_str)
            book = Book(isbn=isbn, title=title, authors=authors)

            # Parse loan if exists
            loan = None
            if loan_id is not None:
                loan = Loan(
                    loan_id=str(loan_id),
                    isbn=isbn,
                    card_id=str(card_id),
                    date_out=parse_date(date_out),
                    due_date=parse_date(due_date),
                    date_in=parse_date(date_in),
                    fine_amt=Decimal(fine_amt),
                    paid=bool(paid),
                )

            results.append((book, loan))

        return Results(items=results, total=total_count, page_limit=query.limit, current_page=query.page)


def search_loans(query: Query) -> Results[Loan]:
    """
    Search book loans with filtering and pagination.

    Supported query keywords:
        loan_id: Filter by loan ID
        isbn: Filter by book ISBN
        card: Filter by borrower card ID
        borrower: Filter by borrower name
        loan_is: Filter by loan status (active, returned)
        due: Filter by due date status (past, future)
        fine_is: Filter by fine status (owed, paid)
        sort: Sort by (loan_id, isbn, card_id, date_out, due_date, date_in, fine_amt)
        order: Sort direction (asc, desc)
        limit: Maximum results per page
        page: Page number
        any_term: Search across all text fields

    Args:
        query: Query object containing search parameters and filters

    Returns:
        Results[Loan]: Paginated results of loans

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        where_clauses = []
        params = []

        # Apply filters from query
        if query.loan_id:
            where_clauses.append("BL.loan_id = %s")
            params.append(query.loan_id)

        if query.isbn:
            where_clauses.append("BL.isbn LIKE %s")
            params.append(f"%{query.isbn}%")

        if query.card:
            where_clauses.append("BL.card_id LIKE %s")
            params.append(f"%{query.card}%")

        if query.borrower:
            where_clauses.append("BR.bname LIKE %s")
            params.append(f"%{query.borrower}%")

        if query.loan_is:
            if query.loan_is == LoanStatus.ACTIVE:
                where_clauses.append("BL.date_in IS NULL")
            elif query.loan_is == LoanStatus.RETURNED:
                where_clauses.append("BL.date_in IS NOT NULL")

        if query.due:
            if query.due == DueStatus.PAST:
                where_clauses.append("BL.due_date < CURDATE() AND BL.date_in IS NULL")
            elif query.due == DueStatus.FUTURE:
                where_clauses.append("BL.due_date >= CURDATE()")

        if query.fine_is:
            if query.fine_is == FineStatus.OWED:
                where_clauses.append("(F.fine_amt > 0 AND F.paid = FALSE)")
            elif query.fine_is == FineStatus.PAID:
                where_clauses.append("F.paid = TRUE")

        if query.any_term:
            where_clauses.append(
                """
                (
                    BL.loan_id LIKE %s OR 
                    BL.isbn LIKE %s OR 
                    BL.card_id LIKE %s OR 
                    BR.bname LIKE %s
                )
            """
            )
            params.extend([f"%{query.any_term}%", f"%{query.any_term}%", f"%{query.any_term}%", f"%{query.any_term}%"])

        # Build the WHERE clause
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(BL.loan_id)
            FROM BOOK_LOANS BL
            LEFT JOIN BORROWER BR ON BL.card_id = BR.card_id
            LEFT JOIN FINES F ON BL.loan_id = F.loan_id
            WHERE {where_clause}
        """

        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Build main query with sorting and pagination
        main_query = f"""
            SELECT
                BL.loan_id,
                BL.isbn,
                BL.card_id,
                BL.date_out,
                BL.due_date,
                BL.date_in,
                COALESCE(F.fine_amt, 0) as fine_amt,
                COALESCE(F.paid, FALSE) as paid
            FROM BOOK_LOANS BL
            LEFT JOIN BORROWER BR ON BL.card_id = BR.card_id
            LEFT JOIN FINES F ON BL.loan_id = F.loan_id
            WHERE {where_clause}
        """

        # Add sorting
        if query.sort:
            sort_field = query.sort.lower()
            direction = "DESC" if query.order == OrderDirection.DESCENDING else "ASC"

            if sort_field == "loan_id":
                main_query += f" ORDER BY BL.loan_id {direction}"
            elif sort_field == "isbn":
                main_query += f" ORDER BY BL.isbn {direction}"
            elif sort_field == "card_id" or sort_field == "card":
                main_query += f" ORDER BY BL.card_id {direction}"
            elif sort_field == "borrower":
                main_query += f" ORDER BY BR.bname {direction}"
            elif sort_field == "date_out":
                main_query += f" ORDER BY BL.date_out {direction}"
            elif sort_field == "due_date":
                main_query += f" ORDER BY BL.due_date {direction}"
            elif sort_field == "date_in":
                main_query += f" ORDER BY BL.date_in {direction}"
            elif sort_field == "fine_amt":
                main_query += f" ORDER BY fine_amt {direction}"
            else:
                # Default sort
                main_query += f" ORDER BY BL.loan_id {direction}"
        else:
            # Default sort
            main_query += " ORDER BY BL.loan_id DESC"

        # Add pagination
        if query.limit is not None:
            offset = (query.page - 1) * query.limit
            main_query += " LIMIT %s OFFSET %s"
            params.extend([query.limit, offset])

        cursor.execute(main_query, params)

        loans = []
        for row in cursor.fetchall():
            loan_id, isbn, card_id, date_out, due_date, date_in, fine_amt, paid = row
            loans.append(
                Loan(
                    loan_id=str(loan_id),
                    isbn=isbn,
                    card_id=card_id,
                    date_out=parse_date(date_out),
                    due_date=parse_date(due_date),
                    date_in=parse_date(date_in),
                    fine_amt=Decimal(fine_amt),
                    paid=bool(paid),
                )
            )

        return Results(items=loans, total=total_count, page_limit=query.limit, current_page=query.page)


def search_loans_with_book(query: Query) -> Results[Tuple[Loan, Book]]:
    """
    Search for loans and include the associated book details.

    Supported query keywords:
        loan_id: Filter by loan ID
        isbn: Filter by book ISBN
        title: Filter by book title
        author: Filter by book author
        borrower: Filter by borrower name
        card: Filter by card ID
        loan_is: Filter by loan status (active, returned)
        due: Filter by due date status (past, future)
        fine_is: Filter by fine status (owed, paid)
        sort: Sort by (loan_id, isbn, title, card_id, borrower, date_out, due_date, date_in, fine_amt)
        order: Sort direction (asc, desc)
        limit: Maximum results per page
        page: Page number
        any_term: Search across all text fields

    Args:
        query: Query object containing search parameters and filters

    Returns:
        Results[Tuple[Loan, Book]]: Paginated results of loans with book information

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        where_clauses = []
        params = []

        # Apply filters from query
        if query.loan_id:
            where_clauses.append("BL.loan_id = %s")
            params.append(query.loan_id)

        if query.isbn:
            where_clauses.append("BL.isbn LIKE %s")
            params.append(f"%{query.isbn}%")

        if query.card:
            where_clauses.append("BL.card_id LIKE %s")
            params.append(f"%{query.card}%")

        if query.borrower:
            where_clauses.append("BR.bname LIKE %s")
            params.append(f"%{query.borrower}%")

        if query.title:
            where_clauses.append("B.title LIKE %s")
            params.append(f"%{query.title}%")

        if query.author:
            where_clauses.append("A.name LIKE %s")
            params.append(f"%{query.author}%")

        if query.loan_is:
            if query.loan_is == LoanStatus.ACTIVE:
                where_clauses.append("BL.date_in IS NULL")
            elif query.loan_is == LoanStatus.RETURNED:
                where_clauses.append("BL.date_in IS NOT NULL")

        if query.due:
            if query.due == DueStatus.PAST:
                where_clauses.append("BL.due_date < CURDATE() AND BL.date_in IS NULL")
            elif query.due == DueStatus.FUTURE:
                where_clauses.append("BL.due_date >= CURDATE()")

        if query.fine_is:
            if query.fine_is == FineStatus.OWED:
                where_clauses.append("(F.fine_amt > 0 AND F.paid = FALSE)")
            elif query.fine_is == FineStatus.PAID:
                where_clauses.append("F.paid = TRUE")

        if query.any_term:
            where_clauses.append(
                """
                (
                    BL.loan_id LIKE %s OR 
                    BL.isbn LIKE %s OR 
                    BL.card_id LIKE %s OR 
                    BR.bname LIKE %s OR
                    B.title LIKE %s
                )
            """
            )
            params.extend(
                [
                    f"%{query.any_term}%",
                    f"%{query.any_term}%",
                    f"%{query.any_term}%",
                    f"%{query.any_term}%",
                    f"%{query.any_term}%",
                ]
            )

        # Build the WHERE clause
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(BL.loan_id)
            FROM BOOK_LOANS BL
            JOIN BOOK B ON BL.isbn = B.isbn
            LEFT JOIN BOOK_AUTHORS BA ON B.isbn = BA.isbn
            LEFT JOIN AUTHORS A ON BA.author_id = A.author_id
            LEFT JOIN BORROWER BR ON BL.card_id = BR.card_id
            LEFT JOIN FINES F ON BL.loan_id = F.loan_id
            WHERE {where_clause}
        """

        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Main query with sorting and pagination
        main_query = f"""
            SELECT
                BL.loan_id,
                BL.isbn,
                BL.card_id,
                BL.date_out,
                BL.due_date,
                BL.date_in,
                COALESCE(F.fine_amt, 0) as fine_amt,
                COALESCE(F.paid, FALSE) as paid,
                B.title,
                GROUP_CONCAT(DISTINCT A.name SEPARATOR '\u001f') AS authors
            FROM BOOK_LOANS BL
            JOIN BOOK B ON BL.isbn = B.isbn
            LEFT JOIN BOOK_AUTHORS BA ON B.isbn = BA.isbn
            LEFT JOIN AUTHORS A ON BA.author_id = A.author_id
            LEFT JOIN BORROWER BR ON BL.card_id = BR.card_id
            LEFT JOIN FINES F ON BL.loan_id = F.loan_id
            WHERE {where_clause}
            GROUP BY BL.loan_id, BL.isbn, BL.card_id, BL.date_out, BL.due_date, 
                     BL.date_in, fine_amt, paid, B.title
        """

        # Add sorting
        if query.sort:
            sort_field = query.sort.lower()
            direction = "DESC" if query.order == OrderDirection.DESCENDING else "ASC"

            if sort_field == "loan_id":
                main_query += f" ORDER BY BL.loan_id {direction}"
            elif sort_field == "isbn":
                main_query += f" ORDER BY BL.isbn {direction}"
            elif sort_field == "title":
                main_query += f" ORDER BY B.title {direction}"
            elif sort_field == "card_id" or sort_field == "card":
                main_query += f" ORDER BY BL.card_id {direction}"
            elif sort_field == "borrower":
                main_query += f" ORDER BY BR.bname {direction}"
            elif sort_field == "date_out":
                main_query += f" ORDER BY BL.date_out {direction}"
            elif sort_field == "due_date":
                main_query += f" ORDER BY BL.due_date {direction}"
            elif sort_field == "date_in":
                main_query += f" ORDER BY BL.date_in {direction}"
            elif sort_field == "fine_amt":
                main_query += f" ORDER BY fine_amt {direction}"
            else:
                # Default sort
                main_query += f" ORDER BY BL.loan_id {direction}"
        else:
            # Default sort
            main_query += " ORDER BY BL.loan_id DESC"

        # Add pagination
        if query.limit is not None:
            offset = (query.page - 1) * query.limit
            main_query += " LIMIT %s OFFSET %s"
            params.extend([query.limit, offset])

        cursor.execute(main_query, params)

        results = []
        for row in cursor.fetchall():
            loan_id, isbn, card_id, date_out, due_date, date_in, fine_amt, paid, title, author_str = row
            loan = Loan(
                loan_id=str(loan_id),
                isbn=isbn,
                card_id=card_id,
                date_out=parse_date(date_out),
                due_date=parse_date(due_date),
                date_in=parse_date(date_in),
                fine_amt=Decimal(fine_amt),
                paid=bool(paid),
            )
            authors = parse_authors(author_str)
            book = Book(isbn=isbn, title=title, authors=authors)

            results.append((loan, book))

        return Results(items=results, total=total_count, page_limit=query.limit, current_page=query.page)


def search_borrowers(query: Query) -> Results[Borrower]:
    """
    Search for borrowers with filtering and pagination.

    Supported query keywords:
        borrower: Filter by borrower name
        card: Filter by card ID
        phone: Filter by phone number
        sort: Sort by (card_id, name, phone, address)
        order: Sort direction (asc, desc)
        limit: Maximum results per page
        page: Page number
        any_term: Search across all text fields (including SSN and address)

    Args:
        query: Query object containing search parameters and filters

    Returns:
        Results[Borrower]: Paginated results of borrowers

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        where_clauses = []
        params = []

        # Apply filters from query
        if query.card:
            where_clauses.append("B.card_id LIKE %s")
            params.append(f"%{query.card}%")

        if query.borrower:
            where_clauses.append("B.bname LIKE %s")
            params.append(f"%{query.borrower}%")

        if query.phone:
            where_clauses.append("B.phone LIKE %s")
            params.append(f"%{query.phone}%")

        if query.any_term:
            where_clauses.append(
                """
                (
                    B.card_id LIKE %s OR 
                    B.bname LIKE %s OR 
                    B.address LIKE %s OR 
                    B.phone LIKE %s OR
                    B.ssn LIKE %s
                )
            """
            )
            params.extend(
                [
                    f"%{query.any_term}%",
                    f"%{query.any_term}%",
                    f"%{query.any_term}%",
                    f"%{query.any_term}%",
                    f"%{query.any_term}%",
                ]
            )

        # Build the WHERE clause
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(B.card_id)
            FROM BORROWER B
            WHERE {where_clause}
        """

        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Main query with sorting and pagination
        main_query = f"""
            SELECT
                B.card_id,
                B.ssn,
                B.bname,
                B.address,
                B.phone
            FROM BORROWER B
            WHERE {where_clause}
        """

        # Add sorting
        if query.sort:
            sort_field = query.sort.lower()
            direction = "DESC" if query.order == OrderDirection.DESCENDING else "ASC"

            if sort_field == "card_id" or sort_field == "card":
                main_query += f" ORDER BY B.card_id {direction}"
            elif sort_field == "borrower" or sort_field == "name":
                main_query += f" ORDER BY B.bname {direction}"
            elif sort_field == "phone":
                main_query += f" ORDER BY B.phone {direction}"
            elif sort_field == "address":
                main_query += f" ORDER BY B.address {direction}"
            else:
                # Default sort
                main_query += f" ORDER BY B.card_id {direction}"
        else:
            # Default sort
            main_query += " ORDER BY B.card_id ASC"

        # Add pagination
        if query.limit is not None:
            offset = (query.page - 1) * query.limit
            main_query += " LIMIT %s OFFSET %s"
            params.extend([query.limit, offset])

        cursor.execute(main_query, params)

        borrowers = []
        for row in cursor.fetchall():
            card_id, ssn, bname, address, phone = row
            borrowers.append(
                Borrower(
                    card_id=card_id,
                    ssn=ssn,
                    bname=bname,
                    address=address,
                    phone=phone if phone else "",
                )
            )

        return Results(items=borrowers, total=total_count, page_limit=query.limit, current_page=query.page)


def search_borrowers_with_fines(card_id: str, query: Query) -> Results[Tuple[Borrower, Decimal]]:
    """
    Search for borrowers with their total outstanding fines.

    Supported query keywords:
        borrower: Filter by borrower name
        card: Filter by card ID
        phone: Filter by phone number
        fine_is: Filter by fine status (owed, paid)
        sort: Sort by (card_id, name, phone, address, fine_amt)
        order: Sort direction (asc, desc)
        limit: Maximum results per page
        page: Page number
        any_term: Search across all text fields

    Args:
        card_id (str): Card ID to filter by (can be empty string)
        query (Query): Query object containing search parameters and filters

    Returns:
        Results[Tuple[Borrower, Decimal]]: Paginated results of borrowers with their fine amounts

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        where_clauses = []
        params = []

        # Filter by card_id if provided
        if card_id:
            where_clauses.append("B.card_id = %s")
            params.append(card_id)

        # Apply filters from query
        if query.card and not card_id:
            where_clauses.append("B.card_id LIKE %s")
            params.append(f"%{query.card}%")

        if query.borrower:
            where_clauses.append("B.bname LIKE %s")
            params.append(f"%{query.borrower}%")

        if query.phone:
            where_clauses.append("B.phone LIKE %s")
            params.append(f"%{query.phone}%")

        if query.fine_is:
            if query.fine_is == FineStatus.OWED:
                where_clauses.append("F.paid = FALSE AND F.fine_amt > 0")
            elif query.fine_is == FineStatus.PAID:
                where_clauses.append("F.paid = TRUE")

        if query.any_term:
            where_clauses.append(
                """
                (
                    B.card_id LIKE %s OR 
                    B.bname LIKE %s OR 
                    B.address LIKE %s OR 
                    B.phone LIKE %s
                )
            """
            )
            params.extend([f"%{query.any_term}%", f"%{query.any_term}%", f"%{query.any_term}%", f"%{query.any_term}%"])

        # Build the WHERE clause
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(DISTINCT B.card_id)
            FROM BORROWER B
            LEFT JOIN BOOK_LOANS BL ON B.card_id = BL.card_id
            LEFT JOIN FINES F ON BL.loan_id = F.loan_id
            WHERE {where_clause}
        """

        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Main query with sorting and pagination
        main_query = f"""
            SELECT
                B.card_id,
                B.ssn,
                B.bname,
                B.address,
                B.phone,
                COALESCE(SUM(CASE WHEN F.paid = FALSE THEN F.fine_amt ELSE 0 END), 0) as total_fines
            FROM BORROWER B
            LEFT JOIN BOOK_LOANS BL ON B.card_id = BL.card_id
            LEFT JOIN FINES F ON BL.loan_id = F.loan_id
            WHERE {where_clause}
            GROUP BY B.card_id, B.ssn, B.bname, B.address, B.phone
        """

        # Add sorting
        if query.sort:
            sort_field = query.sort.lower()
            direction = "DESC" if query.order == OrderDirection.DESCENDING else "ASC"

            if sort_field == "card_id" or sort_field == "card":
                main_query += f" ORDER BY B.card_id {direction}"
            elif sort_field == "borrower" or sort_field == "name":
                main_query += f" ORDER BY B.bname {direction}"
            elif sort_field == "phone":
                main_query += f" ORDER BY B.phone {direction}"
            elif sort_field == "address":
                main_query += f" ORDER BY B.address {direction}"
            elif sort_field == "fine_amt" or sort_field == "fines":
                main_query += f" ORDER BY total_fines {direction}"
            else:
                # Default sort
                main_query += f" ORDER BY B.card_id {direction}"
        else:
            # Default sort
            main_query += " ORDER BY B.card_id ASC"

        # Add pagination
        if query.limit is not None:
            offset = (query.page - 1) * query.limit
            main_query += " LIMIT %s OFFSET %s"
            params.extend([query.limit, offset])

        cursor.execute(main_query, params)

        results = []
        for row in cursor.fetchall():
            card_id, ssn, bname, address, phone, total_fines = row
            borrower = Borrower(
                card_id=card_id,
                ssn=ssn,
                bname=bname,
                address=address,
                phone=phone if phone else "",
            )
            results.append((borrower, Decimal(total_fines)))

        return Results(items=results, total=total_count, page_limit=query.limit, current_page=query.page)


def checkout(card_id: str, isbn: str) -> Loan:
    """
    Checkout a book for a borrower.

    Checks:
        - Borrower exists
        - Book exists
        - Book is available (not currently on loan)
        - Borrower has no unpaid fines
        - Borrower does not exceed the maximum number of active loans (3)

    Args:
        card_id (str): The borrower's card ID.
        isbn (str): The ISBN of the book to checkout.

    Returns:
        Loan: The newly created loan object.

    Raises:
        ObjectDoesNotExist: If the borrower or book does not exist.
        ValidationError: If the borrower has unpaid fines, too many loans, or the book is unavailable.
        Exception: If a database error occurs.
    """
    with connection.cursor() as cursor:
        # 1. Check if borrower exists
        cursor.execute("SELECT COUNT(*) FROM BORROWER WHERE card_id = %s", [card_id])
        if cursor.fetchone()[0] == 0:
            raise ObjectDoesNotExist(f"Borrower with card ID {card_id} does not exist.")

        # 2. Check if book exists
        cursor.execute("SELECT COUNT(*) FROM BOOK WHERE isbn = %s", [isbn])
        if cursor.fetchone()[0] == 0:
            raise ObjectDoesNotExist(f"Book with ISBN {isbn} does not exist.")

        # 3. Check if book is available
        cursor.execute(
            "SELECT COUNT(*) FROM BOOK_LOANS WHERE isbn = %s AND date_in IS NULL",
            [isbn],
        )
        if cursor.fetchone()[0] > 0:
            raise ValidationError(f"Book with ISBN {isbn} is currently on loan.")

        # 4. Check if borrower has unpaid fines
        cursor.execute(
            """
            SELECT COALESCE(SUM(F.fine_amt), 0)
            FROM FINES F
            JOIN BOOK_LOANS BL ON F.loan_id = BL.loan_id
            WHERE BL.card_id = %s AND F.paid = FALSE
            """,
            [card_id],
        )
        unpaid_fines = cursor.fetchone()[0]
        if Decimal(unpaid_fines) > Decimal("0.00"):
            raise ValidationError(f"Borrower with card ID {card_id} has unpaid fines.")

        # 5. Check if borrower exceeds max active loans
        cursor.execute(
            "SELECT COUNT(*) FROM BOOK_LOANS WHERE card_id = %s AND date_in IS NULL",
            [card_id],
        )
        active_loans_count = cursor.fetchone()[0]
        if active_loans_count >= MAX_ACTIVE_LOANS:
            raise ValidationError(
                "Borrower with card ID {card_id} has reached the maximum of " f"{MAX_ACTIVE_LOANS} active loans."
            )

        # All checks passed, proceed with checkout
        current_date = date.today()
        due_date = current_date + timedelta(days=LOAN_DURATION_DAYS)

        with transaction.atomic():
            # Insert the new loan record
            cursor.execute(
                """
                INSERT INTO BOOK_LOANS (isbn, card_id, date_out, due_date)
                VALUES (%s, %s, %s, %s)
            """,
                [isbn, card_id, current_date, due_date],
            )

            # Get the last inserted loan_id
            cursor.execute("SELECT LAST_INSERT_ID()")
            new_loan_id = cursor.fetchone()[0]

            # Fetch the newly created loan record
            cursor.execute(
                """
                SELECT loan_id, isbn, card_id, date_out, due_date, date_in
                FROM BOOK_LOANS
                WHERE loan_id = %s
            """,
                [new_loan_id],
            )
            row = cursor.fetchone()

            if row:
                (
                    loan_id_val,
                    isbn_val,
                    card_id_val,
                    date_out_val,
                    due_date_val,
                    date_in_val,
                ) = row
                # New loans have no fines initially
                return Loan(
                    loan_id=str(loan_id_val),
                    isbn=isbn_val,
                    card_id=card_id_val,
                    date_out=parse_date(date_out_val),
                    due_date=parse_date(due_date_val),
                    date_in=parse_date(date_in_val),
                    fine_amt=Decimal("0.00"),
                    paid=False,
                )
            else:
                raise Exception("Failed to retrieve new loan record after insert.")


def checkin(loan_id: str) -> Loan:
    """
    Checkin a book by marking the loan as returned.

    Updates the date_in for the loan and recalculates fines for all overdue
    loans, including the one just returned if it was overdue.

    Args:
        loan_id (str): The ID of the loan to checkin.

    Returns:
        Loan: The updated loan object, including any calculated fine.

    Raises:
        ObjectDoesNotExist: If the loan does not exist.
        ValidationError: If the loan is already returned.
        Exception: If a database error occurs.
    """
    with connection.cursor() as cursor:
        # 1. Check if loan exists and get current date_in
        cursor.execute(
            "SELECT date_in FROM BOOK_LOANS WHERE loan_id = %s",
            [loan_id],
        )
        loan_row = cursor.fetchone()

        if loan_row is None:
            raise ObjectDoesNotExist(f"Loan with ID {loan_id} does not exist.")

        date_in = loan_row[0]

        # 2. Check if loan is already returned
        if date_in is not None:
            raise ValidationError(f"Loan with ID {loan_id} has already been returned.")

        # Proceed with checkin
        current_date = date.today()

        with transaction.atomic():
            # Update the date_in for the loan
            cursor.execute(
                """
                UPDATE BOOK_LOANS
                SET date_in = %s
                WHERE loan_id = %s
            """,
                [current_date, loan_id],
            )

            # Fetch the updated loan record including fine information
            cursor.execute(
                """
                SELECT
                    BL.loan_id,
                    BL.isbn,
                    BL.card_id,
                    BL.date_out,
                    BL.due_date,
                    BL.date_in,
                    COALESCE(F.fine_amt, 0) as fine_amt,
                    COALESCE(F.paid, FALSE) as paid
                FROM BOOK_LOANS BL
                LEFT JOIN FINES F ON BL.loan_id = F.loan_id
                WHERE BL.loan_id = %s
            """,
                [loan_id],
            )

            row = cursor.fetchone()
            if row:
                (
                    loan_id_val,
                    isbn_val,
                    card_id_val,
                    date_out_val,
                    due_date_val,
                    date_in_val,
                    fine_amt_val,
                    paid_val,
                ) = row
                return Loan(
                    loan_id=str(loan_id_val),
                    isbn=isbn_val,
                    card_id=card_id_val,
                    date_out=parse_date(date_out_val),
                    due_date=parse_date(due_date_val),
                    date_in=parse_date(date_in_val),
                    fine_amt=Decimal(fine_amt_val),
                    paid=bool(paid_val),
                )
            else:
                # This case should ideally not be reached if the UPDATE and fine update succeeded
                raise Exception("Failed to retrieve updated loan record after checkin.")


def get_user_fines(card_id: str, include_paid: bool = False) -> Decimal:
    """
    Get the total fine amount for a borrower's card.

    Args:
        card_id (str): The borrower's card ID
        include_paid (bool): Whether to include paid fines (defaults to False)

    Returns:
        Decimal: Total fine amount

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        where_clause = "BL.card_id = %s"
        params = [card_id]

        if not include_paid:
            where_clause += " AND F.paid = FALSE"

        query = f"""
            SELECT COALESCE(SUM(F.fine_amt), 0) AS total_fine
            FROM FINES F
            JOIN BOOK_LOANS BL ON F.loan_id = BL.loan_id
            WHERE {where_clause}
        """

        cursor.execute(query, params)
        total_fine = cursor.fetchone()[0]

        return Decimal(total_fine)


def get_fines(card_ids: list = [], include_paid: bool = False, sum: bool = False) -> List[Loan]:
    """
    Get loans with fines for given card IDs or all cards.

    Args:
        card_ids (list): List of card IDs to filter by (empty list means all cards)
        include_paid (bool): Whether to include paid fines (defaults to False)
        sum (bool): Whether to sum fines by card (defaults to False)

    Returns:
        List[Loan]: List of loans with fines

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        where_clauses = ["F.fine_amt > 0"]
        params = []

        # Filter by card IDs if provided
        if card_ids:
            placeholders = ", ".join(["%s"] * len(card_ids))
            where_clauses.append(f"BL.card_id IN ({placeholders})")
            params.extend(card_ids)

        # Filter by payment status if requested
        if not include_paid:
            where_clauses.append("F.paid = FALSE")

        where_clause = " AND ".join(where_clauses)

        query = f"""
            SELECT
                BL.loan_id,
                BL.isbn,
                BL.card_id,
                BL.date_out,
                BL.due_date,
                BL.date_in,
                F.fine_amt,
                F.paid
            FROM FINES F
            JOIN BOOK_LOANS BL ON F.loan_id = BL.loan_id
            WHERE {where_clause}
            ORDER BY BL.card_id, F.fine_amt DESC
        """

        cursor.execute(query, params)

        loans = []
        for row in cursor.fetchall():
            loan_id, isbn, card_id, date_out, due_date, date_in, fine_amt, paid = row
            loans.append(
                Loan(
                    loan_id=str(loan_id),
                    isbn=isbn,
                    card_id=card_id,
                    date_out=parse_date(date_out),
                    due_date=parse_date(due_date),
                    date_in=parse_date(date_in),
                    fine_amt=Decimal(fine_amt),
                    paid=bool(paid),
                )
            )

        return loans


def get_fines_grouped(card_ids: list = [], include_paid: bool = False) -> Dict[str, Decimal]:
    """
    Get total fine amounts grouped by borrower card ID.

    Args:
        card_ids (list): List of card IDs to filter by (empty list means all cards)
        include_paid (bool): Whether to include paid fines (defaults to False)

    Returns:
        Dict[str, Decimal]: Dictionary mapping card IDs to their total fine amounts

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        where_clauses = ["F.fine_amt > 0"]
        params = []

        # Filter by card IDs if provided
        if card_ids:
            placeholders = ", ".join(["%s"] * len(card_ids))
            where_clauses.append(f"BL.card_id IN ({placeholders})")
            params.extend(card_ids)

        # Filter by payment status if requested
        if not include_paid:
            where_clauses.append("F.paid = FALSE")

        where_clause = " AND ".join(where_clauses)

        query = f"""
            SELECT
                BL.card_id,
                SUM(F.fine_amt) as total_fine_amt
            FROM FINES F
            JOIN BOOK_LOANS BL ON F.loan_id = BL.loan_id
            WHERE {where_clause}
            GROUP BY BL.card_id
        """

        cursor.execute(query, params)

        result = {}
        for row in cursor.fetchall():
            card_id, total_fine_amt = row
            result[card_id] = Decimal(total_fine_amt)

        return result


def pay_loan_fine(loan_id: str) -> Loan:
    """
    Mark a loan's fine as paid.

    Args:
        loan_id (str): The ID of the loan to mark as paid

    Returns:
        Loan: The updated loan with paid status

    Raises:
        ObjectDoesNotExist: If the loan does not exist
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Check if the loan exists
        cursor.execute("SELECT COUNT(*) FROM BOOK_LOANS WHERE loan_id = %s", [loan_id])
        if cursor.fetchone()[0] == 0:
            raise ObjectDoesNotExist(f"Loan with ID {loan_id} does not exist")

        # Update the fine to paid status
        with transaction.atomic():
            cursor.execute(
                """
                UPDATE FINES
                SET paid = TRUE
                WHERE loan_id = %s
            """,
                [loan_id],
            )

            # Get the updated loan details
            cursor.execute(
                """
                SELECT
                    BL.loan_id,
                    BL.isbn,
                    BL.card_id,
                    BL.date_out,
                    BL.due_date,
                    BL.date_in,
                    COALESCE(F.fine_amt, 0) as fine_amt,
                    COALESCE(F.paid, FALSE) as paid
                FROM BOOK_LOANS BL
                LEFT JOIN FINES F ON BL.loan_id = F.loan_id
                WHERE BL.loan_id = %s
            """,
                [loan_id],
            )

            row = cursor.fetchone()
            if row:
                loan_id, isbn, card_id, date_out, due_date, date_in, fine_amt, paid = row
                return Loan(
                    loan_id=str(loan_id),
                    isbn=isbn,
                    card_id=card_id,
                    date_out=parse_date(date_out),
                    due_date=parse_date(due_date),
                    date_in=parse_date(date_in),
                    fine_amt=Decimal(fine_amt),
                    paid=bool(paid),
                )

            raise ObjectDoesNotExist(f"Loan with ID {loan_id} not found after payment")


def pay_borrower_fines(card_id: str) -> List[Loan]:
    """
    Mark all fines for a borrower as paid.

    Args:
        card_id (str): The borrower's card ID

    Returns:
        List[Loan]: List of updated loans with paid status

    Raises:
        ObjectDoesNotExist: If the borrower does not exist
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Check if the borrower exists
        cursor.execute("SELECT COUNT(*) FROM BORROWER WHERE card_id = %s", [card_id])
        if cursor.fetchone()[0] == 0:
            raise ObjectDoesNotExist(f"Borrower with card ID {card_id} does not exist")

        # Get loan IDs with unpaid fines
        cursor.execute(
            """
            SELECT BL.loan_id
            FROM BOOK_LOANS BL
            JOIN FINES F ON BL.loan_id = F.loan_id
            WHERE BL.card_id = %s AND F.paid = FALSE AND F.fine_amt > 0
        """,
            [card_id],
        )

        loan_ids = [row[0] for row in cursor.fetchall()]
        if not loan_ids:
            return []  # No fines to pay

        # Update the fines to paid status
        with transaction.atomic():
            placeholder = ", ".join(["%s"] * len(loan_ids))
            cursor.execute(
                f"""
                UPDATE FINES
                SET paid = TRUE
                WHERE loan_id IN ({placeholder})
            """,
                loan_ids,
            )

            # Get the updated loan details
            cursor.execute(
                f"""
                SELECT
                    BL.loan_id,
                    BL.isbn,
                    BL.card_id,
                    BL.date_out,
                    BL.due_date,
                    BL.date_in,
                    F.fine_amt,
                    F.paid
                FROM BOOK_LOANS BL
                JOIN FINES F ON BL.loan_id = F.loan_id
                WHERE BL.loan_id IN ({placeholder})
            """,
                loan_ids,
            )

            updated_loans = []
            for row in cursor.fetchall():
                loan_id, isbn, card_id, date_out, due_date, date_in, fine_amt, paid = row
                updated_loans.append(
                    Loan(
                        loan_id=str(loan_id),
                        isbn=isbn,
                        card_id=card_id,
                        date_out=parse_date(date_out),
                        due_date=parse_date(due_date),
                        date_in=parse_date(date_in),
                        fine_amt=Decimal(fine_amt),
                        paid=bool(paid),
                    )
                )

            return updated_loans


def update_fines(current_date: date = date.today()) -> None:
    """
    Calculate and update fines for all overdue books.

    Args:
        current_date (date): The date to use for fine calculations (defaults to today)

    Raises:
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Get all overdue books that have not been returned
        query = """
            SELECT loan_id, due_date, date_in
            FROM BOOK_LOANS
            WHERE due_date < %s AND (date_in IS NULL OR date_in > due_date)
        """
        cursor.execute(query, [current_date])

        # Process each overdue book
        with transaction.atomic():
            for loan_id, due_date, date_in in cursor.fetchall():
                # Calculate days overdue
                end_date = date_in if date_in else current_date
                days_late = (end_date - due_date).days

                # Standard fine rate is $0.25 per day
                fine_amt = Decimal(str(days_late * 0.25))

                # Check if fine record exists
                cursor.execute("SELECT loan_id FROM FINES WHERE loan_id = %s", [loan_id])
                fine_exists = cursor.fetchone() is not None

                if fine_exists:
                    # Update existing fine
                    cursor.execute(
                        """
                        UPDATE FINES
                        SET fine_amt = %s
                        WHERE loan_id = %s AND paid = FALSE
                    """,
                        [fine_amt, loan_id],
                    )
                else:
                    # Create new fine record
                    cursor.execute(
                        """
                        INSERT INTO FINES (loan_id, fine_amt, paid)
                        VALUES (%s, %s, FALSE)
                    """,
                        [loan_id, fine_amt],
                    )


def create_borrower(ssn: str, bname: str, address: str, phone: str = None, card_id: str = None) -> Borrower:
    """
    Create a new borrower in the system.

    Args:
        ssn (str): Social security number of the borrower
        bname (str): Borrower's name
        address (str): Borrower's address
        phone (str, optional): Borrower's phone number
        card_id (str, optional): Card ID to assign (generated if not provided)

    Returns:
        Borrower: The newly created borrower object

    Raises:
        ValidationError: If validation fails (e.g., duplicate SSN)
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Check for duplicate SSN
        cursor.execute("SELECT COUNT(*) FROM BORROWER WHERE ssn = %s", [ssn])
        if cursor.fetchone()[0] > 0:
            raise ValidationError(f"Borrower with SSN {ssn} already exists")

        # Generate card_id if not provided
        if not card_id:
            cursor.execute("SELECT card_id FROM BORROWER WHERE card_id LIKE 'ID%' ORDER BY card_id DESC LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                # Extract the numeric part from the latest card_id
                last_id = int(result[0][2:])
                next_id = last_id + 1
            else:
                # No existing cards, start with 1
                next_id = 1
                
            card_id = f"ID{next_id:06d}"  # Format as ID000001, ID000002, etc.

        # Create the borrower record
        with transaction.atomic():
            cursor.execute(
                """
                INSERT INTO BORROWER (card_id, ssn, bname, address, phone)
                VALUES (%s, %s, %s, %s, %s)
            """,
                [card_id, ssn, bname, address, phone],
            )

            return Borrower(card_id=card_id, ssn=ssn, bname=bname, address=address, phone=phone if phone else "")


def create_librarian(username: str, password: str) -> User:
    """
    Create a new librarian user account.

    Args:
        username (str): Username for the new librarian
        password (str): Password for the new librarian

    Returns:
        User: The newly created user object

    Raises:
        ValidationError: If validation fails (e.g., duplicate username)
        Exception: If a database error occurs
    """
    return create_user(username, password, "librarian")


def create_user(username: str, password: str, group: str) -> User:
    """
    Create a new user account with specified group.

    Args:
        username (str): Username for the new user
        password (str): Password for the new user
        group (str): User group/role (e.g., 'librarian', 'admin')

    Returns:
        User: The newly created user object

    Raises:
        ValidationError: If validation fails (e.g., duplicate username)
        Exception: If a database error occurs
    """
    # Check if username exists
    if User.objects.filter(username=username).exists():
        raise ValidationError(f"Username '{username}' already exists")

    # Check if group exists, create if it doesn't
    try:
        group_obj = Group.objects.get(name=group)
    except Group.DoesNotExist:
        group_obj = Group.objects.create(name=group)

    # Create the user
    with transaction.atomic():
        user = User.objects.create_user(username=username, password=password)
        user.groups.add(group_obj)
        user.save()

        return user


def create_book(isbn: str, title: str, authors: List[str] = []) -> Book:
    """
    Add a new book to the library.

    Args:
        isbn (str): ISBN number for the book
        title (str): Title of the book
        authors (List[str]): List of author names

    Returns:
        Book: The newly created book object

    Raises:
        ValidationError: If validation fails (e.g., duplicate ISBN)
        Exception: If a database error occurs
    """
    with connection.cursor() as cursor:
        # Check if ISBN exists
        cursor.execute("SELECT COUNT(*) FROM BOOK WHERE isbn = %s", [isbn])
        if cursor.fetchone()[0] > 0:
            raise ValidationError(f"Book with ISBN {isbn} already exists")

        # Create the book record
        with transaction.atomic():
            # Insert into BOOK table
            cursor.execute(
                """
                INSERT INTO BOOK (isbn, title)
                VALUES (%s, %s)
            """,
                [isbn, title],
            )

            # Process authors
            for author_name in authors:
                # Check if author exists
                cursor.execute("SELECT author_id FROM AUTHORS WHERE name = %s", [author_name])
                author_row = cursor.fetchone()

                if author_row:
                    author_id = author_row[0]
                else:
                    # Create new author
                    cursor.execute(
                        """
                        INSERT INTO AUTHORS (name)
                        VALUES (%s)
                    """,
                        [author_name],
                    )
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    author_id = cursor.fetchone()[0]

                # Link author to book
                cursor.execute(
                    """
                    INSERT INTO BOOK_AUTHORS (isbn, author_id)
                    VALUES (%s, %s)
                """,
                    [isbn, author_id],
                )

            return Book(isbn=isbn, title=title, authors=authors)
