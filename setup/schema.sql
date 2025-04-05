CREATE TABLE IF NOT EXISTS BOOK (
    Isbn VARCHAR(13) PRIMARY KEY, -- Default to ISBN13
    Title VARCHAR(255) NOT NULL,
    CHECK (CHAR_LENGTH(Isbn) = 13)
);

-- Authors table with Author_id as primary key (auto-increment)
CREATE TABLE AUTHORS (
    Author_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL
);

-- Junction table for many-to-many relationship between books and authors
CREATE TABLE BOOK_AUTHORS (
    Author_id INT,
    Isbn VARCHAR(13), -- ISBN13
    PRIMARY KEY (Author_id, Isbn),
    FOREIGN KEY (Author_id) REFERENCES AUTHORS(Author_id) ON DELETE CASCADE,
    FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn) ON DELETE CASCADE
);

CREATE TABLE BORROWER (
    Card_id VARCHAR(10) PRIMARY KEY,
    Ssn VARCHAR(20) UNIQUE NOT NULL,
    Bname VARCHAR(100) NOT NULL, -- Kept to maintain original schema
    Address VARCHAR(255), -- Also contains City and State to maintain original schema
    Phone VARCHAR(20)
);

CREATE TABLE BOOK_LOANS (
    Loan_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    Isbn VARCHAR(13) NOT NULL,
    Card_id VARCHAR(10) NOT NULL,
    Date_out DATE NOT NULL,
    Due_date DATE NOT NULL,
    Date_in DATE,
    FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn),
    FOREIGN KEY (Card_id) REFERENCES BORROWER(Card_id),
    CHECK (Due_date >= Date_out),
    CHECK (Date_in IS NULL OR Date_in >= Date_out)
);

CREATE TABLE FINES (
    Loan_id INT PRIMARY KEY,
    Fine_amt DECIMAL(10,2) NOT NULL CHECK (Fine_amt >= 0),
    Paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (Loan_id) REFERENCES BOOK_LOANS(Loan_id)
);

