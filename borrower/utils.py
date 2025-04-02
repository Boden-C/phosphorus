# borrower/utils.py

import csv
from .models import Borrower
from django.core.exceptions import ValidationError

def load_borrowers_from_csv(csv_path):
    created = 0
    skipped = 0

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print("📄 CSV Columns:", reader.fieldnames)

        for row in reader:
            try:
                ssn = row['Ssn'].strip()
                bname = row['Bname'].strip()
                address = row['Address'].strip()
                phone = row.get('Phone', '').strip()

                if Borrower.objects.filter(ssn=ssn).exists():
                    print(f"Borrower with SSN {ssn} already exists. Skipping.")
                    skipped += 1
                    continue

                borrower = Borrower(ssn=ssn, bname=bname, address=address, phone=phone)
                borrower.full_clean()
                borrower.save()
                print(f"Created {bname} → Card ID: {borrower.card_id}")
                created += 1

            except ValidationError as ve:
                print(f"Validation error for SSN {ssn}: {ve}")
                skipped += 1
            except Exception as e:
                print(f"Error for SSN {ssn}: {e}")
                skipped += 1

    print(f"\n📊 Finished loading. Created: {created}, Skipped: {skipped}")
