# Phosphorus Library Management System

Phosphorus is a Django/MySQL-based library management system for efficient staff operations, robust fine tracking, and secure user authentication. The backend provides a comprehensive API for managing books, borrowers, loans, and fines, with a focus on maintainability, data integrity, and ease of use for library staff.

## API Endpoints

All endpoints are under `/api/` except for the Django admin interface.

### Authentication

-   `POST /api/auth/login` — Authenticate user and start session
    -   Body: `{ "username": str, "password": str }`
    -   Response: `{ "message": str, "username": str, "id": int }` or `{ "error": str }`
-   `POST /api/auth/logout` — Log out current user and end session
    -   Response: `{ "message": str }`
-   `GET /api/auth/unauthorized` — Always returns 401 unauthorized
    -   Response: `{ "error": "Unauthorized" }`

### Books

-   `GET /api/books/search` — Search for books by title, ISBN, or author
    -   Query: `?query=...&page=1&limit=10` (pagination is required)
    -   Response: `{ "books": [{ "isbn": str, "title": str, "authors": [str] }], "total": int, "page": int }`
-   `GET /api/books/search_with_loan` — Search for books with their current loan status
    -   Query: `?query=...&page=1&limit=10` (pagination is required)
    -   Response: `{ "results": [[{ "isbn": str, "title": str, "authors": [str] }, {loan or null}]], "total": int, "page": int }`
-   `GET /api/books/get` — Get a single book by ISBN
    -   Query: `?isbn=...`
    -   Response: `{ "isbn": str, "title": str, "authors": [str] }` or `{ "error": str }`

### Borrowers

-   `POST /api/borrower/create` — Create a new borrower
    -   Body: `{ "ssn": str, "bname": str, "address": str, "phone"?: str, "card_id"?: str }`
    -   Response: `{ "message": str, "card_id": str, "name": str }` or `{ "error": str }`
-   `GET /api/borrower/search` — Search for borrowers
    -   Query: `?query=...&page=1&limit=10` (pagination is required)
    -   Response: `{ "borrowers": [{ "card_id": str, "ssn": str, "bname": str, "address": str, "phone": str }], "total": int, "page": int }`
-   `GET /api/borrower/search_with_fine` — Search for borrowers with their total fines
    -   Query: `?query=...&page=1&limit=10` (pagination is required)
    -   Response: `{ "results": [[borrower, total_fines]], "total": int, "page": int }`
-   `GET /api/borrower/search_with_info` — Search for borrowers with their active loan count, total loan count, and total fines owed
    -   Query: `?query=...&page=1&limit=10` (pagination is required)
    -   Response: `{ "results": [[borrower, active_loans, total_loans, fine_owed]], "total": int, "page": int }`
-   `GET /api/borrower/fines` — Get total fines for a borrower
    -   Query: `?card_id=...&include_paid=true|false`
    -   Response: `{ "card_id": str, "total_fines": float }` or `{ "error": str }`

### Librarians

-   `POST /api/librarian/create` — Create a new librarian user
    -   Body: `{ "username": str, "password": str }`
    -   Response: `{ "message": str, "username": str, "id": int }` or `{ "error": str }`

### Loans

-   `GET /api/loans/search` — Search for loans
    -   Query: `?query=...&page=1&limit=10` (pagination is required)
    -   Response: `{ "loans": [{ "loan_id": str, "isbn": str, "card_id": str, "date_out": str, "due_date": str, "date_in": str, "fine_amt": float, "paid": bool }], "total": int, "page": int }`
-   `GET /api/loans/search_with_book` — Search for loans with book details
    -   Query: `?query=...&page=1&limit=10` (pagination is required)
    -   Response: `{ "results": [[loan, book]], "total": int, "page": int }`
-   `POST /api/loans/checkout` — Check out a book
    -   Body: `{ "card_id": str, "isbn": str }`
    -   Response: `{ "message": str, "loan_id": str }` or `{ "error": str }`
-   `POST /api/loans/checkin` — Check in a book
    -   Body: `{ "loan_id": str }`
    -   Response: `{ "message": str, "loan_id": str }` or `{ "error": str }`

### Admin

-   `/admin/` — Django admin interface

## Pagination

All search endpoints require the following pagination parameters:

-   `page`: Page number (1-indexed)
-   `limit`: Number of results per page

These parameters are required to ensure proper API behavior and prevent excessive data transfers.

## File Structure

```
root/
  backend/          # Backend Django application
    api.py          # Core API logic
    settings.py     # Django backend settings
    urls.py         # URL patterns for HTTP endpoints
    views.py        # HTTP endpoint handlers
    database/       # Database models and commands
  setup/
    data/           # Raw input data for normalization
    output/         # Normalized output data
    schema.sql      # SQL schema definition
    normalize.py    # Data normalization script
    validate.py     # Data validation script
  manage.py         # Django administrative script
  main.py           # Example API usage
  reset.py          # Database reset and data import
  requirements.txt  # Python package dependencies
```

## API Methods (backend/api.py)

-   `search_books(query: Query) -> Results[Book]`
-   `search_books_with_loan(query: Query) -> Results[Tuple[Book, Optional[Loan]]]`
-   `get_book(isbn: str) -> Book`
-   `search_loans(query: Query) -> Results[Loan]`
-   `search_loans_with_book(query: Query) -> Results[Tuple[Loan, Book]]`
-   `search_borrowers(query: Query) -> Results[Borrower]`
-   `search_borrowers_with_fine(card_id: str, query: Query) -> Results[Tuple[Borrower, Decimal]]`
-   `search_borrowers_with_info(card_id: str, query: Query) -> Results[Tuple[Borrower, int, Decimal]]`
-   `checkout(card_id: str, isbn: str) -> Loan`
-   `checkin(loan_id: str) -> Loan`
-   `get_user_fines(card_id: str, include_paid: bool = False) -> Decimal`
-   `get_fines(card_ids: list = [], include_paid: bool = False, sum: bool = False) -> List[Loan]`
-   `get_fines_grouped(card_ids: list = [], include_paid: bool = False) -> Dict[str, Decimal]`
-   `pay_loan_fine(loan_id: str) -> Loan`
-   `pay_borrower_fines(card_id: str) -> List[Loan]`
-   `update_fines(current_date: date = date.today()) -> None`
-   `create_borrower(ssn: str, bname: str, address: str, phone: str = None, card_id: str = None) -> Borrower`
-   `create_librarian(username: str, password: str) -> User`
-   `create_user(username: str, password: str, group: str) -> User`
-   `create_book(isbn: str, title: str, authors: List[str] = []) -> Book`

## Data Model Notes

-   `Book.authors` is a list of strings (author names).
-   `Loan.date_out`, `Loan.due_date`, and `Loan.date_in` are of type `date` or `None`.

## Fine Management

-   Fines are $0.25 per day for late books
-   `update_fines()` can be run manually or scheduled
-   Fine reporting supports paid/unpaid status and borrower summaries
-   Fines can be paid per loan or in bulk for a borrower

## User Management

-   Librarians have staff-level access and permissions
-   Admins have full system access
-   User creation is integrated with librarian and borrower creation as needed
-   Default groups ("Librarians") organize permissions

## Installation & Setup

1. Install Python 3, MySQL, and clone the repository:
    ```sh
    python --version
    mysql --version
    git clone https://github.com/Boden-C/phosphorus
    cd phosphorus
    ```
2. Create and activate a virtual environment:
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On macOS/Linux
    .venv\Scripts\activate     # On Windows
    ```
3. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
4. Enter MySQL and create the database/user:
    ```sh
    mysql -u root
    CREATE DATABASE IF NOT EXISTS phosphorus_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER 'phosphorus_user'@'localhost' IDENTIFIED BY '';
    GRANT ALL PRIVILEGES ON phosphorus_db.* TO 'phosphorus_user'@'localhost';
    FLUSH PRIVILEGES;
    exit
    ```
5. Setup the database:
    ```sh
    mysql -u phosphorus_user phosphorus_db < setup/schema.sql
    ```
6. Update and confirm Django settings:
    ```sh
    python manage.py migrate
    ```

## Running the Application

To normalize the data:

```sh
python setup/normalize.py
```

To validate the data:

```sh
python setup/validate.py
```

After running `normalize.py`, cleaned data will be saved as `book.csv`, `authors.csv`, `book_authors.csv`, and `borrower.csv`.

To initialize or reset:

```sh
python reset.py
```

To run example code:

```sh
python main.py
```

To start the development server:

```sh
python manage.py runserver
```

To start the Electron development server:

```sh
npm run electron:dev
```

To start the general (Next.js or frontend) development server:

```sh
npm run dev

It should display this:-

VITE v6.3.2  ready in 580 ms

➜  Local:   http://localhost:5173/  (your local URL may vary)
➜  Network: use --host to expose
➜  press h + enter to show help
```

```
localhost:8000/admin
```

Default admin credentials:

-   user: admin
-   pass: adminpassword

To manually update fines:

```sh
python manage.py update_fines
```

```markdown

```
