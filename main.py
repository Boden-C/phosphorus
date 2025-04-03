"""
This is the entry point used only for testing purposes.
It has an example of how to use the API methods.
This does not call the HTTP endpoints directly, instead it imports the api methods from backend/api.py.

If you are looking for the implementation of the API methods, check the backend/api.py file.
If you are looking for the HTTP endpoints, check the backend/views.py file.
If you are looking for managing the database, check the manage.py file.
"""
import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import csv
from backend.api import create_borrower

CSV_PATH = "setup/normalize/output/borrower.csv"

def main():
    created = 0
    skipped = 0

    try:
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            print("CSV Headers:", reader.fieldnames)

            for row in reader:
                ssn = row['Ssn'].strip()
                bname = row['Bname'].strip()
                address = row['Address'].strip()
                phone = row.get('Phone', '').strip()

                result = create_borrower(ssn, bname, address, phone)

                if result:
                    print(f"Created: {result}")
                    created += 1
                else:
                    print(f"Skipped (duplicate or error): {ssn}")
                    skipped += 1

    except FileNotFoundError:
        print("CSV file not found:", CSV_PATH)
    except Exception as e:
        print("Unexpected error:", str(e))

    print(f"\nDone. Created: {created}, Skipped: {skipped}")

if __name__ == "__main__":
    main()
