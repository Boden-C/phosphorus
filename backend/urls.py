"""
URL configuration for backend project.
This file defines all HTTP endpoints for the backend.

The views are in views.py, and the actual logic is in api.py.
"""

from django.urls import path
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import admin
from backend.views import (
    create_borrower,
    create_librarian,
    create_book,
    search_books,
    search_books_with_loan,
    get_book,
    search_borrowers,
    search_borrowers_with_info,
    borrower_fines,
    search_loans,
    search_loans_with_book,
    checkout_loan,
    checkin_loan,
)
from backend.auth_views import login_view, logout_view, unauthorized_view, current_user_view

staff_required = login_required(
    user_passes_test(lambda u: u.is_staff, login_url="/api/auth/unauthorized"), login_url="/api/auth/unauthorized"
)


# Staff permission check
def is_staff(user):
    return user.is_staff


urlpatterns = [
    # Admin interface
    # /admin/ [GET]
    #   - Django admin interface for staff users.
    #   - Requires authentication (session/cookie).
    #   - Response: HTML admin dashboard.
    path("admin/", admin.site.urls, name="admin"),
    # Authentication endpoints
    # /api/auth/login [POST]
    #   - Headers: Content-Type: application/json
    #   - Body: {"username": str, "password": str}
    #   - Response: {"message": str, "username": str, "id": int} on success; {"error": str} on error.
    path("api/auth/login", login_view, name="login"),
    # /api/auth/logout [POST]
    #   - Logs out the current user session.
    #   - Response: {"message": str}
    path("api/auth/logout", logout_view, name="logout"),
    # /api/auth/me [GET]
    #   - Returns current user data if authenticated
    #   - Response: {"success": bool, "user": {"username": str, "is_staff": bool, "is_superuser": bool}}
    path("api/auth/me", current_user_view, name="current_user"),
    # /api/auth/unauthorized [GET]
    #   - Always returns 401 Unauthorized.
    #   - Response: {"error": "Unauthorized"}
    path("api/auth/unauthorized", unauthorized_view, name="unauthorized"),
    # Book endpoints
    # /api/books/search [GET]
    #   - Query: ?query=... (structured search string)
    #   - Response: {"books": [{"isbn": str, "title": str, "authors": [str]}], "total": int, "page": int}
    path("api/books/search", search_books, name="search_books"),
    # /api/books/search_with_loan [GET]
    #   - Query: ?query=... (structured search string)
    #   - Response: {"results": [[{"isbn": str, "title": str, "authors": [str]}, {loan or null}]], "total": int, "page": int}
    path("api/books/search_with_loan", login_required(search_books_with_loan), name="search_books_with_loan"),
    # /api/books/get [GET]
    #   - Query: ?isbn=... (book ISBN)
    #   - Response: {"isbn": str, "title": str, "authors": [str]} or {"error": str}
    path("api/books/get", login_required(get_book), name="get_book"),
    # /api/books/create [POST]
    #   - Headers: Content-Type: application/json
    #   - Body: {"isbn": str, "title": str, "authors": [str]}
    #   - Response: {"message": str, "isbn": str, "title": str, "authors": [str]} or {"error": str}
    path("api/books/create", login_required(create_book), name="create_book"),
    # Borrower endpoints
    # /api/borrower/create [POST]
    #   - Headers: Content-Type: application/json
    #   - Body: {"ssn": str, "bname": str, "address": str, "phone"?: str, "card_id"?: str}
    #   - Response: {"message": str, "card_id": str, "name": str} or {"error": str}
    path("api/borrower/create", login_required(user_passes_test(is_staff)(create_borrower)), name="create_borrower"),
    # /api/borrower/search [GET]
    #   - Query: ?query=... (structured search string)
    #   - Response: {"borrowers": [{"card_id": str, "ssn": str, "bname": str, "address": str, "phone": str}], "total": int, "page": int}
    path("api/borrower/search", login_required(user_passes_test(is_staff)(search_borrowers)), name="search_borrowers"),
    # /api/borrower/search_with_info [GET]
    #   - Query: ?query=... (structured search string)
    #   - Response: {"results": [[borrower, active_loans, fine_owed]], "total": int, "page": int}
    path(
        "api/borrower/search_with_info",
        login_required(user_passes_test(is_staff)(search_borrowers_with_info)),
        name="search_borrowers_with_info",
    ),
    # /api/borrower/fines [GET]
    #   - Query: ?card_id=...&include_paid=true|false
    #   - Response: {"card_id": str, "total_fines": float} or {"error": str}
    path("api/borrower/fines", login_required(user_passes_test(is_staff)(borrower_fines)), name="borrower_fines"),
    # Librarian endpoint
    # /api/librarian/create [POST]
    #   - Headers: Content-Type: application/json
    #   - Body: {"username": str, "password": str}
    #   - Response: {"message": str, "username": str, "id": int} or {"error": str}
    path("api/librarian/create", login_required(user_passes_test(is_staff)(create_librarian)), name="create_librarian"),
    # Loan endpoints
    # /api/loans/search [GET]
    #   - Query: ?query=... (structured search string)
    #   - Response: {"loans": [{"loan_id": str, "isbn": str, "card_id": str, "date_out": str, "due_date": str, "date_in": str, "fine_amt": float, "paid": bool}], "total": int, "page": int}
    path("api/loans/search", login_required(user_passes_test(is_staff)(search_loans)), name="search_loans"),
    # /api/loans/search_with_book [GET]
    #   - Query: ?query=... (structured search string)
    #   - Response: {"results": [[loan, book]], "total": int, "page": int}
    path(
        "api/loans/search_with_book",
        login_required(user_passes_test(is_staff)(search_loans_with_book)),
        name="search_loans_with_book",
    ),
    # /api/loans/checkout [POST]
    #   - Headers: Content-Type: application/json
    #   - Body: {"card_id": str, "isbn": str}
    #   - Response: {"message": str, "loan_id": str} or {"error": str}
    path("api/loans/checkout", login_required(user_passes_test(is_staff)(checkout_loan)), name="checkout_loan"),
    # /api/loans/checkin [POST]
    #   - Headers: Content-Type: application/json
    #   - Body: {"loan_id": str}
    #   - Response: {"message": str, "loan_id": str} or {"error": str}
    path("api/loans/checkin", login_required(user_passes_test(is_staff)(checkin_loan)), name="checkin_loan"),
]
