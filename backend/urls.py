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
    pay_fine,
)

urlpatterns = [
    path("api/borrower/create", create_borrower),
    path("api/books/create", create_book),
    path("api/books/search", search_books),
    path("api/loans/search", search_loans),
    path("api/loans/checkout", checkout_loan),
    path("api/loans/checkin", checkin_loan),
    path("api/fines/search", search_fines),
    path("api/fines/pay", pay_fine),
]
