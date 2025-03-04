import pandas as pd

# Import the datasets
books = pd.read_csv("books.csv", delimiter="\t", dtype=str)
borrowers = pd.read_csv("borrowers.csv")

# Show the datasets to understand
print(books.head())
print(borrowers.head())

# Rename the author column
# Change column name to make merge possible
books = books.rename(columns={"Author": "Name", "ISBN10": "Isbn"})

# Change column name to make merge possible
borrowers = borrowers.rename(columns={"ID0000id": "Card_id", "ssn": "Ssn"})
borrowers["Bname"] = borrowers["first_name"] + " " + borrowers["last_name"]
borrowers["Address"] = borrowers["address"] + ", " + borrowers["city"] + ", " + borrowers["state"]
columns_to_keep = ["Card_id", "Ssn", "Bname", "Address", "phone"]
borrowers = borrowers[columns_to_keep]

# Create the Book Table
# Extract only the Isbn and Title columns
book_table = books[["Isbn", "Title"]].copy()

# Check table
print(book_table.head())

# Create the Authors table
# Extract only the unique authors
unique_authors = pd.DataFrame(books["Name"].unique(), columns=["Name"])

# Create author ids for each author
unique_authors["Author_id"] = range(1, len(unique_authors) + 1)

# Change the order of the columns
unique_authors = unique_authors[["Author_id", "Name"]]

# Check table
print(unique_authors.head())


# Create the book_authors table
# Merge the unique authors author id column with books isbn colum
book_authors = books.merge(unique_authors, on="Name")[["Isbn", "Author_id"]]

# Rename the columns
book_authors.columns = ["Isbn", "Author_id"]

# Check table
print(book_authors.head())

# Export tables to CSV
book_table.to_csv("Book.csv", index=False)
unique_authors.to_csv("Author.csv", index=False)
book_authors.to_csv("Book_Authors.csv", index=False)
borrowers.to_csv("Borrower.csv", index=False)
