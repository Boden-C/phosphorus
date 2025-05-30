/// <reference types="vite/client" />

// Base types for authentication
interface AuthResponse {
    message: string;
}

interface LoginResponse extends AuthResponse {
    username: string;
    id: number;
}

interface UserResponse {
    username: string;
    is_staff?: boolean;
    email?: string;
}

// Chat message types
interface ChatMessage {
    role: "user" | "assistant" | "system" | "tool";
    content: string;
    tool_call_id?: string;
    name?: string;
}

interface ChatRequest {
    message: string;
    history?: ChatMessage[];
}

interface ChatResponse {
    response: string;
    history: ChatMessage[];
    error?: string;
}

// Auth context types
interface AuthContextType {
    isAuthenticated: boolean;
    user: User | null;
    login: (username: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    isLoading: boolean;
    error: string | null;
}

interface User {
    username: string;
}

// API Error type
class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

// Core data model types that match the backend
interface Book {
    isbn: string;
    title: string;
    authors: string[];
}

interface Borrower {
    card_id: string;
    ssn: string;
    bname: string;
    address: string;
    phone: string;
}

interface Loan {
    loan_id: string;
    isbn: string;
    card_id: string;
    date_out: string | null;
    due_date: string | null;
    date_in: string | null;
    fine_amt: number;
    paid: boolean;
}

// API response types
interface BookSearchResponse {
    books: Book[];
    total: number;
    page: number;
}

interface BookWithLoanResponse {
    results: [Book, Loan | null][];
    total: number;
    page: number;
}

interface BorrowerSearchResponse {
    borrowers: Borrower[];
    total: number;
    page: number;
}

interface BorrowerWithInfoResponse {
    results: [Borrower, number, number, number][]; // [Borrower, active_loans, total_loans, fines_owed]
    total: number;
    page: number;
}

interface BorrowerFinesResponse {
    card_id: string;
    total_fines: number;
}

interface LoanSearchResponse {
    loans: Loan[];
    total: number;
    page: number;
}

interface LoanWithBookResponse {
    results: [Loan, Book][];
    total: number;
    page: number;
}

// Create/modify operation responses
interface BookCreateResponse {
    message: string;
    isbn: string;
    title: string;
    authors: string[];
}

interface BorrowerCreateResponse {
    message: string;
    card_id: string;
    name: string;
}

interface LibrarianCreateResponse {
    message: string;
    username: string;
    id: number;
}

interface CheckoutResponse {
    message: string;
    loan_id: string;
}

interface CheckinResponse {
    message: string;
    loan_id: string;
}

// Test-specific types
interface TestContext {
    authenticatedUser?: {
        username: string;
        id: number;
    };
    createdBook?: {
        isbn: string;
        title: string;
        authors: string[];
    };
    createdBorrower?: {
        card_id: string;
        name: string;
    };
    createdLoan?: {
        loan_id: string;
    };
}
