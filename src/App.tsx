import React, { useState } from 'react';

interface Book {
  isbn: string;
  title: string;
  authors: string[];
  checkedOut: boolean;
  borrowerId: string | null;
}

const mockBooks: Book[] = [
  {
    isbn: '978-3-16-148410-0',
    title: 'The Great Gatsby',
    authors: ['F. Scott Fitzgerald'],
    checkedOut: false,
    borrowerId: null,
  },
  {
    isbn: '978-0-14-044913-6',
    title: 'Crime and Punishment',
    authors: ['Fyodor Dostoevsky'],
    checkedOut: true,
    borrowerId: 'B123',
  },
  {
    isbn: '978-0-452-28423-4',
    title: 'To Kill a Mockingbird',
    authors: ['Harper Lee'],
    checkedOut: false,
    borrowerId: null,
  },
];

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredBooks, setFilteredBooks] = useState<Book[]>(mockBooks);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);

    const filtered = mockBooks.filter((book) => {
      const search = value.toLowerCase();
      return (
        book.isbn.toLowerCase().includes(search) ||
        book.title.toLowerCase().includes(search) ||
        book.authors.some((author) => author.toLowerCase().includes(search))
      );
    });
    setFilteredBooks(filtered);
  };

  return (
    <div style={{ padding: '1rem', fontFamily: 'Arial, sans-serif' }}>
      <h1>Library Book Search</h1>
      <input
        type="text"
        placeholder="Search by ISBN, title, or author"
        value={searchTerm}
        onChange={handleSearchChange}
        style={{ width: '100%', padding: '0.5rem', fontSize: '1rem', marginBottom: '1rem' }}
      />
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left', padding: '0.5rem' }}>ISBN</th>
            <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left', padding: '0.5rem' }}>Title</th>
            <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left', padding: '0.5rem' }}>Authors</th>
            <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left', padding: '0.5rem' }}>Availability</th>
            <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left', padding: '0.5rem' }}>Borrower ID</th>
          </tr>
        </thead>
        <tbody>
          {filteredBooks.map((book) => (
            <tr key={book.isbn}>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>{book.isbn}</td>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>{book.title}</td>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>{book.authors.join(', ')}</td>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>
                {book.checkedOut ? 'Checked Out' : 'Available'}
              </td>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>
                {book.checkedOut ? book.borrowerId : 'NULL'}
              </td>
            </tr>
          ))}
          {filteredBooks.length === 0 && (
            <tr>
              <td colSpan={5} style={{ padding: '1rem', textAlign: 'center' }}>
                No books found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div style={{ marginTop: '2rem' }}>
        <button disabled style={{ marginRight: '1rem' }}>
          Checkout Book (placeholder)
        </button>
        <button disabled style={{ marginRight: '1rem' }}>
          Check In Book (placeholder)
        </button>
        <button disabled style={{ marginRight: '1rem' }}>
          Manage Borrowers (placeholder)
        </button>
        <button disabled>Manage Fines (placeholder)</button>
      </div>
    </div>
  );
}

export default App;
