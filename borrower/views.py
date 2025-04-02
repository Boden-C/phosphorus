from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from .models import Borrower

@csrf_exempt
def create_borrower(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            borrower = Borrower(
                ssn=data['ssn'],
                bname=data['bname'],
                address=data['address'],
                phone=data.get('phone')
            )
            borrower.full_clean()
            borrower.save()
            return JsonResponse({'message': 'Borrower created', 'card_id': borrower.card_id})
        except ValidationError as ve:
            return JsonResponse({'error': ve.message_dict}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        # Add this response for non-POST methods like GET
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
