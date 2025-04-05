# Phosphorus

## Description

Full Django/MySQL Project

## File Structure

```
root/
  backend/          # Backend Django application
    api.py          # Contains the database interaction methods
    settings.py     # Config for the Django backend settings
    urls.py         # Defines the URL patterns for the HTTP endpoints
    views.py        # Defines the HTTP endpoints
  setup/  
    data/         # Directory to hold raw input data for normalization
    output/       # Directory to store the normalized output data
    normalize.py    # Script responsible for data normalization
    validate.py     # Script responsible for data validation
  manage.py         # Django administrative script
  main.py           # Main entry point for an example usage of the API
  setup.py          # Script for setting up the application environment and dependencies
```

## Files

### `normalize.py`

* Reads raw CSV files (`books.csv`, `borrowers.csv`)
* Transforms data to conform to a normalized schema
* Calls `validate.py` to ensure data integrity
* Outputs the files
* It also standardizes the author name initials `J K Rowling` -> `JK Rowling`

### `validate.py`

* Validates processed CSV files
* Checks:

  * ISBN format correctness
  * Author uniqueness
  * Borrower data completeness
  * SSN, email, and phone number formatting

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
   Get-Content setup/schema.sql | mysql -u phosphorus_user phosphorus_db  # On Windows Powershell
   ```
7. Update and confirm Django [settings.py](./api/settings.py):

   ```sh
   python manage.py migrate
   ```

## Running the Scripts

To normalize the data:

```sh
python src/normalize/normalize.py
```

To validate the data separately:

```sh
python src/normalize/validate.py
```

After running `normalize.py`, the cleaned data will be saved as `book.csv`, `authors.csv`, `book_authors.csv`, and `borrower.csv` in the project folder.

Before load_borrowers:

```sh
python setup_test_admin.py
```

To run the load_borrowers:

```sh
python load_borrowers.py
```

To run server;

```sh
python manage.py runserver
user - admin
pass - admin123
http://127.0.0.1:8000/admin
```
