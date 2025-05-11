/**
 * API client for interacting with the Phosphorus Library Management System backend.
 * Based on the endpoints defined in backend/urls.py and implementations in backend/api.py.
 */

let API_BASE_URL = "";

/**
 * Sets the base URL for all API requests.
 * @param baseUrl The base URL to use.
 */
export const setApiBaseUrl = (baseUrl: string): void => {
    API_BASE_URL = baseUrl;
};

/**
 * Handles API errors and returns a standardized error response.
 */
const handleApiError = async (response: Response): Promise<never> => {
    let errorMessage = "An unknown error occurred";

    try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.error || response.statusText;
    } catch {
        errorMessage = response.statusText || errorMessage;
    }

    const error = new Error(errorMessage) as ApiError;
    error.status = response.status;
    throw error;
};

/**
 * Base function to make API requests with proper error handling.
 */
const apiRequest = async <T>(url: string, options: RequestInit = {}): Promise<T> => {
    const fullUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
    const response = await fetch(fullUrl, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
        credentials: "include", // Send cookies for session authentication
    });

    if (!response.ok) {
        await handleApiError(response);
    }

    return response.json() as Promise<T>;
};

/**
 * Authentication API functions
 */

export const login = (username: string, password: string): Promise<LoginResponse> => {
    return apiRequest<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
    });
};

export const logout = (): Promise<AuthResponse> => {
    return apiRequest<AuthResponse>("/api/auth/logout", {
        method: "POST",
    });
};

/**
 * Gets the currently authenticated user
 */
export const getCurrentUser = (): Promise<UserResponse> => {
    return apiRequest<{ success: boolean; user: UserResponse }>("/api/auth/me")
        .then((response) => response.user)
        .catch((error) => {
            if (error.status === 401) {
                throw new Error("Not authenticated");
            }
            throw error;
        });
};

/**
 * Book API functions
 */

export const searchBooks = (query: string, page = 1, limit = 100): Promise<BookSearchResponse> => {
    return apiRequest<BookSearchResponse>(
        `/api/books/search?query=${encodeURIComponent(query)}&page=${page}&limit=${limit}`
    );
};

export const searchBooksWithLoan = (query: string, page = 1, limit = 100): Promise<BookWithLoanResponse> => {
    return apiRequest<BookWithLoanResponse>(
        `/api/books/search_with_loan?query=${encodeURIComponent(query)}&page=${page}&limit=${limit}`
    );
};

export const getBook = (isbn: string): Promise<Book> => {
    return apiRequest<Book>(`/api/books/get?isbn=${encodeURIComponent(isbn)}`);
};

export const createBook = (isbn: string, title: string, authors: string[] = []): Promise<BookCreateResponse> => {
    return apiRequest<BookCreateResponse>("/api/books/create", {
        method: "POST",
        body: JSON.stringify({ isbn, title, authors }),
    });
};

/**
 * Borrower API functions
 */

export const createBorrower = (
    ssn: string,
    bname: string,
    address: string,
    phone?: string,
    card_id?: string
): Promise<BorrowerCreateResponse> => {
    return apiRequest<BorrowerCreateResponse>("/api/borrower/create", {
        method: "POST",
        body: JSON.stringify({ ssn, bname, address, phone, card_id }),
    });
};

export const searchBorrowers = (query: string, page = 1, limit = 10): Promise<BorrowerSearchResponse> => {
    return apiRequest<BorrowerSearchResponse>(
        `/api/borrower/search?query=${encodeURIComponent(query)}&page=${page}&limit=${limit}`
    );
};

export const searchBorrowersWithFine = (query: string, page = 1, limit = 10): Promise<BorrowerWithFineResponse> => {
    return apiRequest<BorrowerWithFineResponse>(
        `/api/borrower/search_with_fine?query=${encodeURIComponent(query)}&page=${page}&limit=${limit}`
    );
};

export const getBorrowerFines = (cardId: string, includePaid = false): Promise<BorrowerFinesResponse> => {
    return apiRequest<BorrowerFinesResponse>(
        `/api/borrower/fines?card_id=${encodeURIComponent(cardId)}&include_paid=${includePaid}`
    );
};

/**
 * Librarian API functions
 */

export const createLibrarian = (username: string, password: string): Promise<LibrarianCreateResponse> => {
    return apiRequest<LibrarianCreateResponse>("/api/librarian/create", {
        method: "POST",
        body: JSON.stringify({ username, password }),
    });
};

/**
 * Loan API functions
 */

export const searchLoans = (query: string, page = 1, limit = 10): Promise<LoanSearchResponse> => {
    return apiRequest<LoanSearchResponse>(
        `/api/loans/search?query=${encodeURIComponent(query)}&page=${page}&limit=${limit}`
    );
};

export const searchLoansWithBook = (query: string, page = 1, limit = 10): Promise<LoanWithBookResponse> => {
    return apiRequest<LoanWithBookResponse>(
        `/api/loans/search_with_book?query=${encodeURIComponent(query)}&page=${page}&limit=${limit}`
    );
};

export const checkoutBook = (cardId: string, isbn: string): Promise<CheckoutResponse> => {
    return apiRequest<CheckoutResponse>("/api/loans/checkout", {
        method: "POST",
        body: JSON.stringify({ card_id: cardId, isbn }),
    });
};

export const checkinBook = (loanId: string): Promise<CheckinResponse> => {
    return apiRequest<CheckinResponse>("/api/loans/checkin", {
        method: "POST",
        body: JSON.stringify({ loan_id: loanId }),
    });
};
