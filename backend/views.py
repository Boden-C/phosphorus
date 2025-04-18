"""
HTTP endpoints for the backend of the application.
This module contains the views that handle HTTP requests and responses.

The logic is located in the api.py file, which these call.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from backend import api


@csrf_exempt
def create_borrower(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else request.POST
            card_id, bname = api.create_borrower(
                ssn=data.get("ssn"),
                bname=data.get("bname"),
                address=data.get("address"),
                phone=data.get("phone"),
            )
            return JsonResponse({"message": "Borrower created", "card_id": card_id, "name": bname})
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)


@csrf_exempt
def create_book(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else request.POST
            isbn, title = api.create_book(
                isbn=data.get("isbn"),
                title=data.get("title"),
            )

            # Handle authors if provided
            authors = data.get("authors")
            if authors:
                author_ids = []
                for author_name in authors:
                    author_id, _ = api.create_author(author_name)
                    api.create_junction(author_id, isbn)
                    author_ids.append(author_id)

                return JsonResponse(
                    {"message": "Book created with authors", "isbn": isbn, "title": title, "author_ids": author_ids}
                )

            return JsonResponse({"message": "Book created", "isbn": isbn, "title": title})
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)


@csrf_exempt
def search_books(request):
    if request.method == "GET":
        try:
            query = request.GET.get("query", "")
            results = api.search_books(query)

            # Format results as list of dictionaries for JSON
            books = []
            for result in results:
                books.append({"isbn": result[0], "title": result[1], "authors": result[2]})

            return JsonResponse({"books": books})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)


@csrf_exempt
def search_loans(request):
    if request.method == "GET":
        try:
            card_id = request.GET.get("card_id", "")
            query = request.GET.get("query", "")

            if not card_id:
                return JsonResponse({"error": "Card ID is required"}, status=400)

            results = api.search_loans(card_id, query)

            # Format results as list of dictionaries for JSON
            loans = []
            for result in results:
                loans.append(
                    {
                        "loan_id": result[0],
                        "isbn": result[1],
                        "card_id": result[2],
                        "date_out": result[3],
                        "due_date": result[4],
                        "date_in": result[5],
                    }
                )

            return JsonResponse({"loans": loans})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)


@csrf_exempt
def checkout_loan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else request.POST
            card_id = data.get("card_id")
            isbn = data.get("isbn")

            if not card_id or not isbn:
                return JsonResponse({"error": "Both card_id and isbn are required"}, status=400)

            loan_id = api.checkout(card_id, isbn)
            return JsonResponse({"message": "Book checked out successfully", "loan_id": loan_id})
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)


@csrf_exempt
def checkin_loan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else request.POST
            loan_id = data.get("loan_id")

            if not loan_id:
                return JsonResponse({"error": "loan_id is required"}, status=400)

            api.checkin(loan_id)
            return JsonResponse({"message": "Book checked in successfully", "loan_id": loan_id})
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)


@csrf_exempt
def search_fines(request):
    if request.method == "GET":
        try:
            card_id = request.GET.get("card_id")
            card_ids_str = request.GET.get("card_ids")
            include_paid = request.GET.get("include_paid", "false").lower() == "true"
            sum_only = request.GET.get("sum", "false").lower() == "true"

            # Parse card_ids if provided
            card_ids = []
            if card_ids_str:
                try:
                    card_ids = json.loads(card_ids_str)
                    if not isinstance(card_ids, list):
                        return JsonResponse({"error": "card_ids must be a valid JSON array"}, status=400)
                except json.JSONDecodeError:
                    return JsonResponse({"error": "Invalid card_ids JSON format"}, status=400)

            # If card_id is provided, add it to card_ids
            if card_id and not card_ids:
                card_ids = [card_id]

            if sum_only:
                if card_id and not card_ids_str:
                    # Get sum of fines for a specific borrower
                    total = api.get_user_fines(card_id, include_paid)
                    return JsonResponse({"card_id": card_id, "total_fines": float(total)})
                else:
                    # Get sum of fines for all borrowers or specific set of borrowers
                    fines_dict = api.get_fines_dict(card_ids=card_ids, include_paid=include_paid)
                    return JsonResponse({"borrowers": {k: float(v) for k, v in fines_dict.items()}})
            else:
                # Get detailed fine records
                fines = api.get_fines(card_ids=card_ids, include_paid=include_paid)

                # Format results as list of dictionaries for JSON
                formatted_fines = []
                for fine in fines:
                    formatted_fines.append(
                        {
                            "loan_id": fine[0],
                            "card_id": fine[1],
                            "fine_amt": float(fine[2]),
                            "paid": fine[3],
                            "book_title": fine[4],
                            "due_date": fine[5],
                            "date_in": fine[6],
                        }
                    )

                return JsonResponse({"fines": formatted_fines})
        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)


@csrf_exempt
def pay_fine(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else request.POST
            loan_id = data.get("loan_id")
            card_id = data.get("card_id")

            # Can't provide both loan_id and card_id
            if loan_id and card_id:
                return JsonResponse({"error": "Provide either loan_id or card_id, not both"}, status=400)

            # Must provide one of them
            if not loan_id and not card_id:
                return JsonResponse({"error": "Either loan_id or card_id is required"}, status=400)

            # Pay for specific loan
            if loan_id:
                result = api.pay_loan_fine(loan_id)
                return JsonResponse(result)

            # Pay all fines for a borrower
            else:
                result = api.pay_borrower_fines(card_id)
                return JsonResponse(result)

        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)


@csrf_exempt
def borrower_fines(request):
    """
    Get total fines for a specific borrower.
    """
    if request.method == "GET":
        try:
            card_id = request.GET.get("card_id")

            if not card_id:
                return JsonResponse({"error": "Card ID is required"}, status=400)

            include_paid = request.GET.get("include_paid", "false").lower() == "true"

            # Get total fines for the borrower
            total = api.get_user_fines(card_id, include_paid)
            return JsonResponse({"card_id": card_id, "total_fines": float(total)})

        except ValidationError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)
