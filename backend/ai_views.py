"""
AI chat views for Phosphorus project.
This module handles AI chat functionality using OpenRouter API.
"""

import json
import os
import traceback
import requests
import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Model
from setup.logger import log
from dotenv import load_dotenv

from .api import (
    search_books,
    search_books_with_loan,
    search_loans_with_book,
    search_borrowers_with_info,
    checkout,
    checkin,
    get_user_fines,
    get_fines,
    pay_loan_fine,
    pay_borrower_fines,
    update_fines,
    create_borrower,
    create_librarian,
    create_user,
)
from .query import Query

# Load environment variables from .env.local
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.local")
load_dotenv(dotenv_path)

# Get API key from environment
AI_API_KEY = os.environ.get("AI_API_KEY", "")
MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"  # Default model, can be configurable

# OpenRouter API Endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def search_books_tool(query: str) -> Any:
    """
    Search for books and their loan status using a search query.
    """
    try:
        q = Query(any_term=query)
        results = search_books_with_loan(q)
        return [
            {
                "book": {
                    "isbn": b.isbn,
                    "title": b.title,
                    "authors": b.authors,
                },
                "loan": l.__dict__ if l else None,
            }
            for b, l in results.items
        ]
    except Exception as e:
        return {"error": str(e)}


def search_loans_tool(query: str) -> Any:
    """
    Search for loans and book details using a search query.
    """
    try:
        q = Query(any_term=query)
        results = search_loans_with_book(q)
        return [
            {
                "loan": l.__dict__,
                "book": b.__dict__,
            }
            for l, b in results.items
        ]
    except Exception as e:
        return {"error": str(e)}


def search_borrowers_tool(card_id: str, query: str) -> Any:
    """
    Search for borrowers and info using card_id and a search query.
    """
    try:
        q = Query(any_term=query)
        results = search_borrowers_with_info(card_id, q)
        return [
            {
                "borrower": b.__dict__,
                "active_loans": active,
                "total_loans": total,
                "fines": float(fines),
            }
            for b, active, total, fines in results.items
        ]
    except Exception as e:
        return {"error": str(e)}


def checkout_tool(card_id: str, isbn: str) -> Any:
    """
    Checkout a book using card_id and isbn.
    """
    try:
        loan = checkout(card_id, isbn)
        return loan.__dict__
    except Exception as e:
        return {"error": str(e)}


def checkin_tool(loan_id: str) -> Any:
    """
    Check in a book using loan_id.
    """
    try:
        loan = checkin(loan_id)
        return loan.__dict__
    except Exception as e:
        return {"error": str(e)}


def get_user_fines_tool(card_id: str, include_paid: bool = False) -> Any:
    """
    Get total fines using card_id.
    """
    try:
        total = get_user_fines(card_id, include_paid)
        return {"card_id": card_id, "total_fines": float(total)}
    except Exception as e:
        return {"error": str(e)}


def get_fines_tool(card_ids: list = [], include_paid: bool = False, sum: bool = False) -> Any:
    """
    Get loans with fines using card_ids.
    """
    try:
        loans = get_fines(card_ids, include_paid, sum)
        return [l.__dict__ for l in loans]
    except Exception as e:
        return {"error": str(e)}


def pay_loan_fine_tool(loan_id: str) -> Any:
    """
    Pay a loan fine using loan_id.
    """
    try:
        loan = pay_loan_fine(loan_id)
        return loan.__dict__
    except Exception as e:
        return {"error": str(e)}


def pay_borrower_fines_tool(card_id: str) -> Any:
    """
    Pay all fines for a borrower using card_id.
    """
    try:
        loans = pay_borrower_fines(card_id)
        return [l.__dict__ for l in loans]
    except Exception as e:
        return {"error": str(e)}


def update_fines_tool(day: str = None) -> Any:
    """
    Update fines for all overdue books.
    """
    try:
        day = day or datetime.datetime.now().date()
        update_fines(datetime.datetime.strptime(day, "%Y-%m-%d").date())
        return {"status": "Fines updated"}
    except Exception as e:
        return {"error": str(e)}


def create_borrower_tool(
    ssn: str, bname: str, address: str, phone: Optional[str] = None, card_id: Optional[str] = None
) -> Any:
    """
    Create a borrower using ssn, bname, address, phone, card_id.
    """
    try:
        borrower = create_borrower(ssn, bname, address, phone, card_id)
        return borrower.__dict__
    except Exception as e:
        return {"error": str(e)}


def create_librarian_tool(username: str, password: str) -> Any:
    """
    Create a librarian using username and password.
    """
    try:
        user = create_librarian(username, password)
        return {"username": user.username, "id": user.id}
    except Exception as e:
        return {"error": str(e)}


def create_user_tool(username: str, password: str, group: str) -> Any:
    """
    Create a user with group using username, password, group.
    """
    try:
        user = create_user(username, password, group)
        return {"username": user.username, "id": user.id}
    except Exception as e:
        return {"error": str(e)}


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_books_tool",
            "description": "Search for books and include their current loan status. Returns a list of books with their loan info if checked out.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search string for books and loans."}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_loans_tool",
            "description": "Search for loans and include the associated book details.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search string for loans and books."}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_borrowers_tool",
            "description": "Search for borrowers and include their active loan count, total loan count, and total outstanding fines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "Borrower card ID (can be empty string for all)."},
                    "query": {"type": "string", "description": "Search string for borrowers."},
                },
                "required": ["card_id", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checkout_tool",
            "description": "Checkout a book for a borrower.",
            "parameters": {
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "Borrower card ID."},
                    "isbn": {"type": "string", "description": "Book ISBN."},
                },
                "required": ["card_id", "isbn"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checkin_tool",
            "description": "Check in a book by marking the loan as returned.",
            "parameters": {
                "type": "object",
                "properties": {"loan_id": {"type": "string", "description": "Loan ID to check in."}},
                "required": ["loan_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_fines_tool",
            "description": "Get the total fine amount for a borrower's card.",
            "parameters": {
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "Borrower card ID."},
                    "include_paid": {"type": "boolean", "description": "Include paid fines (default false)."},
                },
                "required": ["card_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fines_tool",
            "description": "Get loans with fines for given card IDs or all cards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "card_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of card IDs (empty for all).",
                    },
                    "include_paid": {"type": "boolean", "description": "Include paid fines (default false)."},
                    "sum": {"type": "boolean", "description": "Sum fines by card (default false)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pay_loan_fine_tool",
            "description": "Mark a loan's fine as paid.",
            "parameters": {
                "type": "object",
                "properties": {"loan_id": {"type": "string", "description": "Loan ID to pay fine for."}},
                "required": ["loan_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pay_borrower_fines_tool",
            "description": "Mark all fines for a borrower as paid.",
            "parameters": {
                "type": "object",
                "properties": {"card_id": {"type": "string", "description": "Borrower card ID."}},
                "required": ["card_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_fines_tool",
            "description": "Calculate and update fines for all overdue books.",
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string",
                        "description": "Optional, date to calculate fines for in YYYY-MM-DD."
                    },
                    "include_paid": {"type": "boolean", "description": "Include paid fines (default false)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_borrower_tool",
            "description": "Create a new borrower in the system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ssn": {"type": "string", "description": "Social security number."},
                    "bname": {"type": "string", "description": "Borrower name."},
                    "address": {"type": "string", "description": "Borrower address."},
                    "phone": {"type": "string", "description": "Borrower phone number (optional)."},
                    "card_id": {"type": "string", "description": "Card ID to assign (optional)."},
                },
                "required": ["ssn", "bname", "address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_librarian_tool",
            "description": "Create a new librarian user account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Librarian username."},
                    "password": {"type": "string", "description": "Librarian password."},
                },
                "required": ["username", "password"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_user_tool",
            "description": "Create a new user account with specified group.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Username."},
                    "password": {"type": "string", "description": "Password."},
                    "group": {"type": "string", "description": "User group/role."},
                },
                "required": ["username", "password", "group"],
            },
        },
    },
]

TOOL_MAPPING = {
    "search_books_tool": search_books_tool,
    "search_loans_tool": search_loans_tool,
    "search_borrowers_tool": search_borrowers_tool,
    "checkout_tool": checkout_tool,
    "checkin_tool": checkin_tool,
    "get_user_fines_tool": get_user_fines_tool,
    "get_fines_tool": get_fines_tool,
    "pay_loan_fine_tool": pay_loan_fine_tool,
    "pay_borrower_fines_tool": pay_borrower_fines_tool,
    "update_fines_tool": update_fines_tool,
    "create_borrower_tool": create_borrower_tool,
    "create_librarian_tool": create_librarian_tool,
    "create_user_tool": create_user_tool,
}


def json_serialize(obj: Any) -> Any:
    """
    Recursively convert objects to JSON serializable types.

    Handles:
    - datetime.date/datetime objects -> ISO format string
    - Decimal objects -> float
    - Custom objects with __dict__ -> dict
    - Lists/tuples -> list with serialized items
    - Dictionaries -> dict with serialized values
    """
    if obj is None:
        return None

    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()

    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, (list, tuple)):
        return [json_serialize(item) for item in obj]

    if isinstance(obj, dict):
        return {key: json_serialize(value) for key, value in obj.items()}

    if isinstance(obj, Model):
        # Django model objects
        serialized = {}
        for key, value in obj.__dict__.items():
            if not key.startswith("_"):  # Skip private fields
                serialized[key] = json_serialize(value)
        return serialized

    if hasattr(obj, "__dict__"):
        # General object serialization
        return json_serialize(obj.__dict__)

    # Return the object as-is for basic types (strings, numbers, booleans)
    return obj


def call_llm(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    log.info(f"[AI] Calling LLM. API_KEY present: {bool(AI_API_KEY)}")
    log.info(f"[AI] Payload: {json.dumps({'model': MODEL, 'tools': tools, 'messages': messages}, indent=2)[:1000]}")
    if not AI_API_KEY:
        log.error("[AI] API_KEY is not set.")
        raise ValueError("API_KEY is not set. Please check your environment variables.")
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "Library Assistant",
    }
    payload = {"model": MODEL, "tools": tools, "messages": messages}
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        log.info(f"[AI] OpenRouter response status: {response.status_code}")
        log.info(f"[AI] OpenRouter response text: {response.text[:1000]}")
    except Exception as e:
        log.error(f"[AI] Exception during OpenRouter call: {e}")
        raise
    if response.status_code != 200:
        log.error(f"[AI] OpenRouter API error: {response.status_code} {response.text}")
        raise Exception(f"OpenRouter API error: {response.status_code} {response.text}")
    return response.json()


def process_tool_calls(tool_calls: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process tool calls and append results to messages."""
    for tool_call in tool_calls:
        function_info = tool_call.get("function", {})
        tool_name = function_info.get("name")
        tool_args = json.loads(function_info.get("arguments", "{}"))

        # Execute the tool function with the provided arguments
        tool_result = TOOL_MAPPING[tool_name](**tool_args)

        # Convert tool result to JSON-serializable format
        serialized_result = json_serialize(tool_result)

        # Add the tool result to messages
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "name": tool_name,
                "parameters": tool_args,
                "content": json.dumps(serialized_result),
            }
        )

    return messages


@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    log.info("[AI] /api/chat/ endpoint called.")
    try:
        log.info(f"[AI] Raw request body: {request.body}")
        try:
            data = json.loads(request.body)
            log.info(f"[AI] Parsed request data: {data}")
        except json.JSONDecodeError:
            log.error("[AI] Invalid JSON in request body.")
            return JsonResponse({"error": "Invalid JSON in request body", "history": []}, status=400)
        user_message = data.get("message", "")
        if not user_message:
            log.error("[AI] No message provided in request.")
            return JsonResponse({"error": "No message provided", "history": []}, status=400)
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for the Phosphorus library management system. Always use your given system tools, then respond based on them to help the user.",
            }
        ]
        messages.append({"role": "user", "content": user_message})
        log.info(f"[AI] Full message history: {messages}")
        try:
            while True:
                log.info("[AI] Entering agentic loop.")
                response_data = call_llm(messages)
                log.info(f"[AI] LLM response: {response_data}")
                choice = response_data.get("choices", [{}])[0]
                assistant_message = choice.get("message", {})
                log.info(f"[AI] Assistant message: {assistant_message}")
                if not assistant_message:
                    error_msg = {"role": "assistant", "content": "I couldn't generate a response. Please try again."}
                    messages.append(error_msg)
                    log.error("[AI] No assistant message returned.")
                    return JsonResponse({"response": error_msg["content"], "history": messages})
                messages.append(assistant_message)
                tool_calls = assistant_message.get("tool_calls", [])
                log.info(f"[AI] Tool calls: {tool_calls}")
                if tool_calls:
                    messages = process_tool_calls(tool_calls, messages)
                    log.info(f"[AI] Messages after tool call: {messages}")
                else:
                    break
        except Exception as inner_error:
            error_msg = {
                "role": "assistant",
                "content": f"An error occurred while processing your request: {str(inner_error)}",
            }
            messages.append(error_msg)
            log.error(f"[AI] Error in AI conversation loop: {inner_error}, {traceback.format_exc()}")
            return JsonResponse({"response": error_msg["content"], "history": messages})
        log.info(f"[AI] Final assistant message: {assistant_message.get('content', '')}")
        return JsonResponse({"response": assistant_message.get("content", ""), "history": messages})
    except Exception as e:
        log.error(f"[AI] Error in AI chat: {e}, {traceback.format_exc()}")
        error_history = [{"role": "assistant", "content": f"Server error: {str(e)}"}]
        return JsonResponse(
            {"error": str(e), "response": f"Server error: {str(e)}", "history": error_history}, status=500
        )
