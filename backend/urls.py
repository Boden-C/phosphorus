"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from backend.views import (
    create_borrower,
    create_book,
    search_books,
    search_loans,
    checkout_loan,
    checkin_loan,
    search_fines,
    borrower_fines,
    pay_fine,
)

urlpatterns = [
    # Create new borrower - POST
    # Params: ssn (required), bname (required), address (required), phone (optional)
    # Returns: card_id and name of created borrower
    # Errors: 400 if SSN already exists or database integrity error
    path("api/borrower/create", create_borrower),
    # Get borrower's total fines - GET
    # Params: card_id (required), include_paid (optional, default=false)
    # Returns: total fines for the specified borrower
    # Errors: 400 if card_id not provided or not found
    path("api/borrower/fines", borrower_fines),
    # Create new book - POST
    # Params: isbn (required), title (required), authors (optional, list of names)
    # Returns: isbn, title, and optional author_ids
    # Errors: 400 if required params missing or database integrity error
    path("api/books/create", create_book),
    # Search books - GET
    # Params: query (required, searches title, isbn, author)
    # Returns: list of matching books with authors
    # Errors: 500 for database errors
    path("api/books/search", search_books),
    # Search loans - GET
    # Params: card_id (required), query (optional, defaults to empty)
    # Returns: list of loans matching the query for the borrower
    # Errors: 400 if card_id not provided
    path("api/loans/search", search_loans),
    # Checkout book - POST
    # Params: card_id (required), isbn (required)
    # Returns: loan_id of created loan
    # Errors: 400 if borrower has 3 active loans, unpaid fines, or book unavailable
    path("api/loans/checkout", checkout_loan),
    # Check in book - POST
    # Params: loan_id (required)
    # Returns: confirmation with loan_id
    # Errors: 400 if loan not found or already checked in
    path("api/loans/checkin", checkin_loan),
    # Search fines - GET
    # Params: card_ids (optional, JSON array), card_id (optional),
    #         include_paid (optional, default=false), sum (optional, default=false)
    # Returns: fine records or summary by borrower
    # Errors: 400 if card_ids not valid JSON array or database errors
    path("api/fines/search", search_fines),
    # Pay fine - POST
    # Params: loan_id OR card_id (exactly one required)
    # Returns: payment confirmation with amount paid
    # Errors: 400 if both or neither param provided, if book not returned,
    #         or if no unpaid fines exist
    path("api/fines/pay", pay_fine),
]
