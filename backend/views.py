"""
HTTP endpoints for the backend of the application.
This module contains the views that handle HTTP requests and responses.

The logic is located in the api.py file, which these call.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from api import create_borrower


@csrf_exempt
def create_borrower(request):
    if request.method == "POST":
        try:
            borrower = create_borrower(
                ssn=request.POST["ssn"],
                bname=request.POST["bname"],
                address=request.POST["address"],
                phone=request.POST.get("phone"),
                email=request.POST.get("email"),
            )
            return JsonResponse({"message": "Borrower created", "card_id": borrower.card_id})
        except ValidationError as ve:
            return JsonResponse({"error": ve.message_dict}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        # Add this response for non-POST methods like GET
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
