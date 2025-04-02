# load_borrowers.py

import django
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from borrower.utils import load_borrowers_from_csv

CSV_PATH = os.path.join('setup', 'normalize', 'output', 'borrower.csv')
load_borrowers_from_csv(CSV_PATH)
