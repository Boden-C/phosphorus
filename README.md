# Phosphorus Library Management System

Phosphorus is a Django/MySQL-based library management system designed for efficient staff operations, robust fine tracking, and secure user authentication. The backend provides a comprehensive API for managing books, borrowers, loans, and fines, with a focus on maintainability, data integrity, and ease of use for library staff.

### Borrower Authentication Design

Borrowers are not implemented as system users. All borrower-related operations (checkout, fine payment, etc.) are performed by staff on their behalf. This is because it is not possible to add the authentication for Borrowers while still maintaining backwards compatability and 3NF.

The system maintains two user types:

- **Admin**: Superuser with full system access
- **Librarians**: Staff users who perform all library operations

## File Structure

```
root/
  backend/          # Backend Django application
    api.py          # Contains the database interaction methods
    settings.py     # Config for the Django backend settings
    urls.py         # Defines the URL patterns for the HTTP endpoints
    views.py        # Defines the HTTP endpoints
    database/       # Database models and commands
  setup/
    data/           # Directory to hold raw input data for normalization
    output/         # Directory to store the normalized output data
    schema.sql      # SQL schema definition
    normalize.py    # Script responsible for data normalization
    validate.py     # Script responsible for data validation
  manage.py         # Django administrative script
  main.py           # Main entry point for an example usage of the API
  reset.py          # Script for resetting the database and importing data
  requirements.txt  # Python package dependencies
```

## API Methods

The `api.py` file includes the following standardized functions:

- `search_books(query: str) -> List[Tuple]`: Search for books by title, ISBN, or author name
- `checkout(card_id: str, isbn: str) -> str`: Check out a book for a borrower
- `search_loans(card_id: str, query: str) -> List[Tuple]`: Search book loans by borrower ID
- `checkin(loan_id: str) -> str`: Check in a book
- `get_user_fines(card_id: str, include_paid: bool = False) -> Decimal`: Get sum of fines for a borrower
- `get_fines(card_ids:list = [], include_paid: bool = False, sum: bool = False) -> List[Tuple]`: Get list of fines
- `get_fines_dict(card_ids:list = [], include_paid: bool = False) -> Dict[str, Decimal]`: Get dictionary of fines by borrower
- `pay_loan_fine(loan_id: str) -> dict`: Pay a single loan's fine
- `pay_borrower_fines(card_id: str) -> dict`: Pay all fines for a borrower
- `update_fines(current_date: date = date.today()) -> None`: Update fines for late books
- `create_borrower(ssn: str, bname: str, address: str, phone: str = None, username: str = None, password: str = None) -> Tuple[str, str]`: Create new borrower with optional user account
- `create_librarian(username: str, password: str) -> Tuple[str, str]`: Create new librarian user
- `create_user(id: str, username: str, password: str, group: str) -> Tuple[str, str]`: Create new Django user
- `create_book(isbn: str, title: str) -> Tuple[str, str]`: Create new book
- `create_junction(author_id: str, isbn: str) -> Tuple[str, str]`: Connect author to book
- `create_author(author_name: str) -> Tuple[str, str]`: Create new author

## HTTP Endpoints

The system provides the following RESTful API endpoints (see [backend/urls.py](backend/urls.py)):

- `POST /api/auth/login`: Authenticate user and start session
- `POST /api/auth/logout`: Log out current user and end session
- `GET /api/auth/unauthorized`: Always returns 401 unauthorized
- `GET /api/borrower/fines`: Get total fines for a single borrower
- `POST /api/borrower/create`: Create a new borrower with optional user account
- `POST /api/librarian/create`: Create a new librarian user
- `POST /api/books/create`: Create a new book
- `GET /api/books/search`: Search for books by title, ISBN, or author
- `GET /api/loans/search`: Search for loans by borrower ID
- `POST /api/loans/checkout`: Check out a book
- `POST /api/loans/checkin`: Check in a book
- `GET /api/fines/search`: Search for fines, optionally filtered by multiple borrowers
- `POST /api/fines/pay`: Pay fines for a loan or borrower

## Files

### `api.py`

- Implements backend logic for all database operations
- Provides user management integrated with Django authentication

### `normalize.py`

- Reads and normalizes raw CSV data
- Calls `validate.py` for data integrity
- Outputs cleaned files
- Standardizes author name formatting

### `validate.py`

- Validates processed CSV files
- Checks ISBN, author uniqueness, borrower completeness, and formatting

### `main.py`

- Demonstrates example API usage and error handling
- Serves as a testing playground

### `reset.py`

- Resets the database and imports data
- Creates default user groups and initial users
- Used for system initialization

## Fine Management

- Fines are calculated at $0.25 per day for late books
- `update_fines()` can be run manually or scheduled
- Fine reporting supports paid/unpaid status and borrower summaries
- Fines can be paid per loan or in bulk for a borrower

## User Management

The system integrates with Django's authentication system:

- Librarians have staff-level access and permissions
- Admins have full system access
- User creation is integrated with librarian and borrower creation as needed
- Default groups ("Librarians") organize permissions

## Installation & Setup

1. Make sure you have installed Python 3, MySQL, and have cloned the repository:

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
4. Enter into MySQL:

   ```sh
   mysql -u root  # -p if you have password
   ```
5. Create the database and the user:

   ```sql
   CREATE DATABASE IF NOT EXISTS phosphorus_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'phosphorus_user'@'localhost' IDENTIFIED BY '';  -- Default to empty password
   GRANT ALL PRIVILEGES ON phosphorus_db.* TO 'phosphorus_user'@'localhost';
   FLUSH PRIVILEGES;
   exit
   ```
6. Setup the database:

   ```sh
   mysql -u phosphorus_user phosphorus_db < setup/schema.sql
   ```

   Or if you are using Windows Powershell:

   ```pwsh
   Get-Content setup/schema.sql | mysql -u phosphorus_user phosphorus_db  # On Windows Powershell
   ```
7. Update and confirm Django [settings.py](./api/settings.py):

   ```sh
   python manage.py migrate
   ```

## Running the Application

To normalize the data:

```sh
python setup/normalize.py
```

To validate the data separately:

```sh
python setup/validate.py
```

After running `normalize.py`, the cleaned data will be saved as `book.csv`, `authors.csv`, `book_authors.csv`, and `borrower.csv`.

To initialize or reset, run:

```sh
python reset.py
```

You can then use the API or run example code in `main.py`:

```sh
python main.py
```

To start the development server:

```sh
python manage.py runserver
```

This is a development server that can only be accessed over HTTP. If you see a SSL Error you are accessing it through HTTPS.

Access the admin interface at:

```
localhost:8000/admin
```

Default admin credentials:

- user: admin
- pass: adminpassword

To manually update fines:

```sh
python manage.py update_fines
```
