# Phosphorus Library Management System

## Design Notes

### Borrower Authentication Design Decision

While conceptually it would make sense for Borrowers to have user accounts for system login, this application was designed as a staff portal only. Borrowers are not implemented as users for two key reasons:

1. **Database Normalization and Backward Compatibility**: Adding a foreign key from the Borrower table to the User table would break backward compatibility with existing SQL commands and queries. The application strictly maintains 3NF (Third Normal Form) while preserving the original schema structure.

2. **Application Purpose**: This application is designed as a portal for library staff to use, not borrowers. All operations related to borrowers (checking out books, paying fines, etc.) are performed by librarians on behalf of borrowers.

The system maintains two user types:

-   **Admin**: Superuser with full system access
-   **Librarians**: Staff users who can perform all library operations

This design ensures simplicity, maintains data integrity, and preserves the original database structure.

## Description

Full Django/MySQL Library Management System with fine tracking capabilities and user authentication.

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

-   `search_books(query: str) -> List[Tuple]`: Search for books by title, ISBN, or author name
-   `checkout(card_id: str, isbn: str) -> str`: Check out a book for a borrower
-   `search_loans(card_id: str, query: str) -> List[Tuple]`: Search book loans by borrower ID
-   `checkin(loan_id: str) -> str`: Check in a book
-   `get_user_fines(card_id: str, include_paid: bool = False) -> Decimal`: Get sum of fines for a borrower
-   `get_fines(card_ids:list = [], include_paid: bool = False, sum: bool = False) -> List[Tuple]`: Get list of fines
-   `get_fines_dict(card_ids:list = [], include_paid: bool = False) -> Dict[str, Decimal]`: Get dictionary of fines by borrower
-   `pay_loan_fine(loan_id: str) -> dict`: Pay a single loan's fine
-   `pay_borrower_fines(card_id: str) -> dict`: Pay all fines for a borrower
-   `update_fines(current_date: date = date.today()) -> None`: Update fines for late books
-   `create_borrower(ssn: str, bname: str, address: str, phone: str = None, username: str = None, password: str = None) -> Tuple[str, str]`: Create new borrower with optional user account
-   `create_librarian(username: str, password: str) -> Tuple[str, str]`: Create new librarian user
-   `create_user(id: str, username: str, password: str, group: str) -> Tuple[str, str]`: Create new Django user
-   `create_book(isbn: str, title: str) -> Tuple[str, str]`: Create new book
-   `create_junction(author_id: str, isbn: str) -> Tuple[str, str]`: Connect author to book
-   `create_author(author_name: str) -> Tuple[str, str]`: Create new author

## HTTP Endpoints

The system provides the following RESTful API endpoints:

-   `GET /api/borrower/fines`: Get total fines for a single borrower
-   `POST /api/borrower/create`: Create a new borrower with optional user account
-   `POST /api/librarian/create`: Create a new librarian user
-   `POST /api/books/create`: Create a new book
-   `GET /api/books/search`: Search for books by title, ISBN, or author
-   `GET /api/loans/search`: Search for loans by borrower ID
-   `POST /api/loans/checkout`: Check out a book
-   `POST /api/loans/checkin`: Check in a book
-   `GET /api/fines/search`: Search for fines, optionally filtered by multiple borrowers
-   `POST /api/fines/pay`: Pay fines for a loan or borrower

## Files

### `api.py`

-   Includes the actual logic for handling requests and responses in the backend of the application
-   Contains all the methods that interact with the database and can be imported for usage in other files
-   Provides user management functions integrated with Django's authentication system

### `normalize.py`

-   Reads raw CSV files (`books.csv`, `borrowers.csv`)
-   Transforms data to conform to a normalized schema
-   Calls `validate.py` to ensure data integrity
-   Outputs the files
-   It also standardizes the author name initials `J K Rowling` -> `JK Rowling`

### `validate.py`

-   Validates processed CSV files
-   Checks:
    -   ISBN format correctness
    -   Author uniqueness
    -   Borrower data completeness
    -   SSN, email, and phone number formatting

### `main.py`

-   Contains example usage of all API methods
-   Demonstrates error handling and typical workflow
-   Serves as a testing playground for the application

### `reset.py`

-   Clears the database
-   Creates default user groups and initial users
-   Imports data from CSV files into the database
-   Creates Django user accounts for borrowers during import
-   Used for initializing the system

## Fine Management

The system includes robust fine management capabilities:

-   Fines are calculated at $0.25 per day for late books
-   `update_fines()` can be called manually or via cron job to calculate fines
-   Fine reporting includes options to view paid/unpaid fines and totals by borrower
-   Fines can be paid individually by loan or all at once for a borrower

## User Management

The system integrates with Django's authentication system:

-   Borrowers can have associated user accounts for system login
-   Librarians have staff-level access with special permissions
-   User creation is integrated with borrower/librarian creation
-   Default groups ("Borrowers" and "Librarians") organize permissions
-   ID ranges are maintained (Borrower card IDs start at 10000000, librarian IDs at 10000)

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
python src/normalize/normalize.py
```

To validate the data separately:

```sh
python src/normalize/validate.py
```

After running `normalize.py`, the cleaned data will be saved as `book.csv`, `authors.csv`, `book_authors.csv`, and `borrower.csv` in the project folder.

To initialize, you can first run:

```sh
python reset.py
```

You can then write your own code in `main.py`:

```sh
python main.py
```

By default, there are some examples on how to use the api.

To run server;

```sh
python manage.py runserver
user - admin
pass - admin123
http://127.0.0.1:8000/admin
```

To manually update fines:

```sh
python manage.py update_fines
```
