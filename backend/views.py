"""
HTTP endpoints for the backend of the application.
This module contains the views that handle HTTP requests and responses.

The logic is located in the api.py file, which these call.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import json
from backend import api
from backend.query import Query
from setup.logger import log
import traceback
from django.views.decorators.http import require_POST
from datetime import date


@csrf_exempt
def create_borrower(request):
    """Create a new borrower. POST body: {ssn, bname, address, phone?, card_id?}."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ssn = data.get("ssn")
            bname = data.get("bname")
            address = data.get("address")
            phone = data.get("phone")
            card_id = data.get("card_id")
            borrower = api.create_borrower(ssn=ssn, bname=bname, address=address, phone=phone, card_id=card_id)
            return JsonResponse({"message": "Borrower created", "card_id": borrower.card_id, "name": borrower.bname})
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            log(f"Exception in create_borrower: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": "Failed to create borrower"}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def create_librarian(request):
    """Create a new librarian. POST body: {username, password}."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
            if not username or not password:
                return JsonResponse({"error": "Username and password are required"}, status=400)
            user = api.create_librarian(username, password)
            return JsonResponse({"message": "Librarian created", "username": user.username, "id": user.id})
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            log(f"Exception in create_librarian: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def create_book(request):
    """Create a new book. POST body: {isbn, title, authors: [str]}."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            isbn = data.get("isbn")
            title = data.get("title")
            authors = data.get("authors", [])
            if not isbn or not title:
                return JsonResponse({"error": "isbn and title are required"}, status=400)
            book = api.create_book(isbn, title, authors)
            return JsonResponse(
                {"message": "Book created", "isbn": book.isbn, "title": book.title, "authors": book.authors}
            )
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            log(f"Exception in create_book: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def search_books(request):
    """Search for books. GET param: query (structured search string)."""
    if request.method == "GET":
        try:
            query_str = request.GET.get("query", "")
            page = int(request.GET.get("page", "1"))
            limit = int(request.GET.get("limit", "10"))
            query = Query.of(query_str)
            query.page = page
            query.limit = limit
            results = api.search_books(query)
            books = [{"isbn": b.isbn, "title": b.title, "authors": b.authors} for b in results.items]
            return JsonResponse({"books": books, "total": results.total, "page": results.current_page})
        except Exception as e:
            log(f"Exception in search_books: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def search_books_with_loan(request):
    """Search for books with loan status. GET param: query."""
    if request.method == "GET":
        try:
            query_str = request.GET.get("query", "")
            page = int(request.GET.get("page", "1"))
            limit = int(request.GET.get("limit", "10"))
            query = Query.of(query_str)
            query.page = page
            query.limit = limit
            results = api.search_books_with_loan(query)
            out = []
            for book, loan in results.items:
                book_dict = {"isbn": book.isbn, "title": book.title, "authors": book.authors}
                loan_dict = None
                if loan:
                    loan_dict = {
                        "loan_id": loan.loan_id,
                        "card_id": loan.card_id,
                        "date_out": loan.date_out.isoformat() if loan.date_out else None,
                        "due_date": loan.due_date.isoformat() if loan.due_date else None,
                        "date_in": loan.date_in.isoformat() if loan.date_in else None,
                        "fine_amt": float(loan.fine_amt),
                        "paid": loan.paid,
                    }
                out.append([book_dict, loan_dict])
            return JsonResponse({"results": out, "total": results.total, "page": results.current_page})
        except Exception as e:
            log(f"Exception in search_books_with_loan: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def get_book(request):
    """Get a single book by ISBN. GET param: isbn."""
    if request.method == "GET":
        try:
            isbn = request.GET.get("isbn")
            if not isbn:
                return JsonResponse({"error": "ISBN is required"}, status=400)
            book = api.search_books(Query(isbn=isbn)).items
            if not book:
                return JsonResponse({"error": "Book not found"}, status=404)
            b = book[0]
            return JsonResponse({"isbn": b.isbn, "title": b.title, "authors": b.authors})
        except Exception as e:
            log(f"Exception in get_book: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def search_borrowers(request):
    """Search for borrowers. GET param: query."""
    if request.method == "GET":
        try:
            query_str = request.GET.get("query", "")
            page = int(request.GET.get("page", "1"))
            limit = int(request.GET.get("limit", "10"))
            query = Query.of(query_str)
            query.page = page
            query.limit = limit
            results = api.search_borrowers(query)
            borrowers = [
                {"card_id": b.card_id, "ssn": b.ssn, "bname": b.bname, "address": b.address, "phone": b.phone}
                for b in results.items
            ]
            return JsonResponse({"borrowers": borrowers, "total": results.total, "page": results.current_page})
        except Exception as e:
            log(f"Exception in search_borrowers: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def search_borrowers_with_info(request):
    """Search for borrowers with active loans, total loans, and fines. GET param: query."""
    if request.method == "GET":
        try:
            query_str = request.GET.get("query", "")
            page = int(request.GET.get("page", "1"))
            limit = int(request.GET.get("limit", "10"))
            query = Query.of(query_str)
            query.page = page
            query.limit = limit
            results = api.search_borrowers_with_info("", query)
            out = []
            for borrower, active_loans, total_loans, fine in results.items:
                out.append(
                    [
                        {
                            "card_id": borrower.card_id,
                            "ssn": borrower.ssn,
                            "bname": borrower.bname,
                            "address": borrower.address,
                            "phone": borrower.phone,
                        },
                        active_loans,
                        total_loans,
                        float(fine),
                    ]
                )
            return JsonResponse({"results": out, "total": results.total, "page": results.current_page})
        except Exception as e:
            log(f"Exception in search_borrowers_with_fine: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def borrower_fines(request):
    """Get total fines for a borrower. GET param: card_id, include_paid?"""
    if request.method == "GET":
        try:
            card_id = request.GET.get("card_id")
            if not card_id:
                return JsonResponse({"error": "Card ID is required"}, status=400)
            include_paid = request.GET.get("include_paid", "false").lower() == "true"
            total = api.get_user_fines(card_id, include_paid)
            return JsonResponse({"card_id": card_id, "total_fines": float(total)})
        except Exception as e:
            log(f"Exception in borrower_fines: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def search_loans(request):
    """Search for loans. GET param: query."""
    if request.method == "GET":
        try:
            query_str = request.GET.get("query", "")
            page = int(request.GET.get("page", "1"))
            limit = int(request.GET.get("limit", "10"))
            query = Query.of(query_str)
            query.page = page
            query.limit = limit
            results = api.search_loans(query)
            loans = []
            for l in results.items:
                loans.append(
                    {
                        "loan_id": l.loan_id,
                        "isbn": l.isbn,
                        "card_id": l.card_id,
                        "date_out": l.date_out.isoformat() if l.date_out else None,
                        "due_date": l.due_date.isoformat() if l.due_date else None,
                        "date_in": l.date_in.isoformat() if l.date_in else None,
                        "fine_amt": float(l.fine_amt),
                        "paid": l.paid,
                    }
                )
            return JsonResponse({"loans": loans, "total": results.total, "page": results.current_page})
        except Exception as e:
            log(f"Exception in search_loans: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def search_loans_with_book(request):
    """Search for loans with book details. GET param: query."""
    if request.method == "GET":
        try:
            query_str = request.GET.get("query", "")
            page = int(request.GET.get("page", "1"))
            limit = int(request.GET.get("limit", "10"))
            query = Query.of(query_str)
            query.page = page
            query.limit = limit
            results = api.search_loans_with_book(query)
            out = []
            for loan, book in results.items:
                loan_dict = {
                    "loan_id": loan.loan_id,
                    "isbn": loan.isbn,
                    "card_id": loan.card_id,
                    "date_out": loan.date_out.isoformat() if loan.date_out else None,
                    "due_date": loan.due_date.isoformat() if loan.due_date else None,
                    "date_in": loan.date_in.isoformat() if loan.date_in else None,
                    "fine_amt": float(loan.fine_amt),
                    "paid": loan.paid,
                }
                book_dict = {"isbn": book.isbn, "title": book.title, "authors": book.authors}
                out.append([loan_dict, book_dict])
            return JsonResponse({"results": out, "total": results.total, "page": results.current_page})
        except Exception as e:
            log(f"Exception in search_loans_with_book: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def checkout_loan(request):
    """Checkout a book. POST body: {card_id, isbn}."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_id = data.get("card_id")
            isbn = data.get("isbn")
            if not card_id or not isbn:
                return JsonResponse({"error": "card_id and isbn are required"}, status=400)
            loan = api.checkout(card_id, isbn)
            return JsonResponse({"message": "Book checked out", "loan_id": loan.loan_id})
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            log(f"Exception in checkout_loan: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def checkin_loan(request):
    """Checkin a book. POST body: {loan_id}."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            loan_id = data.get("loan_id")
            if not loan_id:
                return JsonResponse({"error": "loan_id is required"}, status=400)
            loan = api.checkin(loan_id)
            return JsonResponse({"message": "Book checked in", "loan_id": loan.loan_id})
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            log(f"Exception in checkin_loan: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
@require_POST
def trigger_update_fines(request):
    """Trigger fine updates for all overdue loans"""
    try:
        api.update_fines(current_date=date.today())
        return JsonResponse({"message": "Fines updated successfully"})
    except Exception as e:
        log(f"Exception in trigger_update_fines: {e}\n{traceback.format_exc()}")
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
@require_POST
def pay_loan_fine_view(request, loan_id: str):
    try:
        print(f"[DEBUG] pay_loan_fine_view called with loan_id={loan_id}")
        loan = api.pay_loan_fine(loan_id)
        return JsonResponse({
            "loan_id": loan.loan_id,
            "isbn": loan.isbn,
            "card_id": loan.card_id,
            "date_out": loan.date_out.isoformat() if loan.date_out else None,
            "due_date": loan.due_date.isoformat() if loan.due_date else None,
            "date_in": loan.date_in.isoformat() if loan.date_in else None,
            "fine_amt": str(loan.fine_amt),
            "paid": loan.paid,
        })
    except Exception as e:
        import traceback
        print("[ERROR] in pay_loan_fine_view:")
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=400)

