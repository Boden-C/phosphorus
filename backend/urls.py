"""
URL configuration for backend project.
This file defines all HTTP endpoints for the backend.

The views are in views.py, and the actual logic is in api.py.
"""

from django.urls import path
from django.contrib.auth.decorators import user_passes_test
from django.contrib import admin
from backend.views import (
    create_borrower,
    create_librarian,
    create_book,
    search_books,
    search_loans,
    checkout_loan,
    checkin_loan,
    search_fines,
    borrower_fines,
    pay_fine,
)
from backend.auth_views import login_view, logout_view, unauthorized_view


# Staff permission check
def is_staff(user):
    return user.is_staff


urlpatterns = [
    # Admin interface
    # Accessible at /admin/ with admin credentials.
    path("admin/", admin.site.urls),
    # POST /api/auth/login
    # Authenticate user and start session.
    # Params: username (str, required), password (str, required)
    # Returns: user info, session token
    # Errors: 401 if credentials invalid
    path("api/auth/login", login_view, name="login"),
    # POST /api/auth/logout
    # Log out current user and end session.
    # Params: none
    # Returns: confirmation
    # Errors: 401 if not authenticated
    path("api/auth/logout", logout_view, name="logout"),
    # GET /api/auth/unauthorized
    # Always returns 401 unauthorized.
    # Params: none
    # Returns: error message
    # Errors: always 401
    path("api/auth/unauthorized", unauthorized_view, name="unauthorized"),
    # GET /api/books/search
    # Search books by title, ISBN, or author.
    # Params: query (str, required)
    # Returns: list of books with authors
    # Errors: 500 for database errors
    path("api/books/search", search_books),
    # POST /api/borrower/create
    # Create new borrower (staff only).
    # Params: ssn (str, required), bname (str, required), address (str, required),
    #         phone (str, optional), username (str, optional), password (str, optional)
    # Returns: card_id, name, username if created
    # Errors: 400 if SSN exists or integrity error
    path("api/borrower/create", user_passes_test(is_staff)(create_borrower)),
    # POST /api/librarian/create
    # Create new librarian (staff only).
    # Params: username (str, required), password (str, required)
    # Returns: staff_id, username
    # Errors: 400 if username exists or integrity error
    path("api/librarian/create", user_passes_test(is_staff)(create_librarian)),
    # GET /api/borrower/fines
    # Get total fines for borrower (staff only).
    # Params: card_id (str, required), include_paid (bool, optional)
    # Returns: total fines
    # Errors: 400 if card_id missing or not found
    path("api/borrower/fines", user_passes_test(is_staff)(borrower_fines)),
    # POST /api/books/create
    # Create new book (staff only).
    # Params: isbn (str, required), title (str, required), authors (list[str], optional)
    # Returns: isbn, title, author_ids if provided
    # Errors: 400 if required params missing or integrity error
    path("api/books/create", user_passes_test(is_staff)(create_book)),
    # GET /api/loans/search
    # Search loans by borrower (staff only).
    # Params: card_id (str, required), query (str, optional)
    # Returns: list of loans
    # Errors: 400 if card_id missing
    path("api/loans/search", user_passes_test(is_staff)(search_loans)),
    # POST /api/loans/checkout
    # Check out book for borrower (staff only).
    # Params: card_id (str, required), isbn (str, required)
    # Returns: loan_id
    # Errors: 400 if 3 active loans, unpaid fines, or book unavailable
    path("api/loans/checkout", user_passes_test(is_staff)(checkout_loan)),
    # POST /api/loans/checkin
    # Check in book (staff only).
    # Params: loan_id (str, required)
    # Returns: confirmation with loan_id
    # Errors: 400 if loan not found or already checked in
    path("api/loans/checkin", user_passes_test(is_staff)(checkin_loan)),
    # GET /api/fines/search
    # Search fines (staff only).
    # Params: card_ids (JSON array, optional), card_id (str, optional),
    #         include_paid (bool, optional), sum (bool, optional)
    # Returns: fine records or summary
    # Errors: 400 if card_ids invalid or db errors
    path("api/fines/search", user_passes_test(is_staff)(search_fines)),
    # POST /api/fines/pay
    # Pay fines for loan or borrower (staff only).
    # Params: loan_id (str) OR card_id (str), exactly one required
    # Returns: payment confirmation, amount paid
    # Errors: 400 if both/neither param, book not returned, or no unpaid fines
    path("api/fines/pay", user_passes_test(is_staff)(pay_fine)),
]
