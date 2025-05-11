"""
Authentication views for the Phosphorus Library Management System.
"""

from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
import json
from setup.logger import log
import traceback
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def me_view(request):
    """
    GET /api/auth/me
    Returns basic info about the currently logged-in user.
    """
    user = request.user
    return JsonResponse({
        "success": True,
        "user": {
            "username":     user.username,
            "is_staff":     user.is_staff,
            "is_superuser": user.is_superuser,
            "id":           user.id,
        }
    })


@csrf_exempt
def login_view(request):
    """
    Authenticate a user and create a session.

    POST Parameters:
        username (str): The username
        password (str): The password

    Returns:
        JsonResponse: Authentication result with user info or error message
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else request.POST
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return JsonResponse({"error": "Username and password are required"}, status=400)

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return JsonResponse(
                    {
                        "success": True,
                        "user": {
                            "username": user.username,
                            "is_staff": user.is_staff,
                            "is_superuser": user.is_superuser,
                        },
                    }
                )
            else:
                return JsonResponse({"error": "Invalid credentials"}, status=401)

        except Exception as e:
            log(f"Exception in login_view: {e}\n{traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)


def current_user_view(request):
    """
    Get the currently authenticated user.

    Returns:
        JsonResponse: User information or error message
    """
    if request.user.is_authenticated:
        return JsonResponse(
            {
                "success": True,
                "user": {
                    "username": request.user.username,
                    "is_staff": request.user.is_staff,
                    "is_superuser": request.user.is_superuser,
                },
            }
        )
    else:
        return JsonResponse({"error": "Not authenticated"}, status=401)


@csrf_exempt
def logout_view(request):
    """
    Log out the current user.

    Returns:
        JsonResponse: Success message
    """
    logout(request)
    return JsonResponse({"success": True, "message": "Logged out successfully"})


def unauthorized_view(request):
    """
    Handle unauthorized access attempts.

    Returns:
        JsonResponse: Error message for unauthorized access
    """
    return JsonResponse(
        {"error": "Authentication required", "message": "You must be logged in as staff to access this resource"},
        status=401,
    )
