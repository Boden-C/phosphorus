# Project Phosphorus

## Description

It currently normalizes raw csv data from src/normalize/data, validates it, and outputs it.

### BONUS

Added proper logging and for the data values, see [validate.py](./src/normalize/validate.py)

## File Structure

```
src/
├── normalize/
│   ├── data/                 # Raw CSV files
│   ├── log_config.py         # Logger setup
│   ├── normalize.py          # Data normalization scripts
│   ├── validate.py           # Data validation scripts
├── schema.sql                # Schema for future database
.gitignore                    # Python gitignore
output/                       # Normalized CSV files
```

## Files

### `normalize.py`

* Reads raw CSV files (`books.csv`, `borrowers.csv`)
* Transforms data to conform to a normalized schema
* Calls `validate.py` to ensure data integrity
* Outputs the files

### `validate.py`

* Validates processed CSV files
* Checks:

  * ISBN format correctness
  * Author uniqueness
  * Borrower data completeness
  * SSN, email, and phone number formatting

## Installation & Setup

1. Clone the repository:

   ```sh
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
