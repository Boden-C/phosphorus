/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import {
    setApiBaseUrl,
    login,
    logout,
    searchBooks,
    createBook,
    createBorrower,
    createLibrarian,
    searchBorrowers,
    checkoutBook,
    checkinBook,
} from "./lib/api";

/**
 * Runs all integration tests against the real API in the browser.
 * No mocking, no test framework. Results are logged to the console.
 */
export async function runTests(): Promise<void> {
    setApiBaseUrl(""); // Set to your API base URL if needed
    const testUser = { username: "librarian1", password: "librarian1password" };
    const testBorrower = {
        ssn: "123-45-6789",
        bname: "Test Borrower",
        address: "123 Test St",
        phone: "555-1234",
        card_id: "TST123",
    };
    const testBook = { isbn: "9780000000001", title: "Test Book", authors: ["Author One"] };
    const testLibrarian = { username: "librarian1", password: "librarian1password" };
    let loanId: string | undefined;

    function logResult(name: string, passed: boolean, info?: string) {
        if (passed) {
            console.log(`✅ ${name}`);
        } else {
            console.error(`❌ ${name}${info ? ": " + info : ""}`);
        }
    }

    // 1. Test unauthenticated request fails
    try {
        await searchBorrowers("Test");
        logResult("Unauthenticated should fail", false);
    } catch (e) {
        logResult("Unauthenticated should fail", true);
    }

    // 2. Test login fails for wrong credentials
    try {
        await login("notarealuser", "wrongpass");
        logResult("Login with wrong credentials should fail", false);
    } catch (e) {
        logResult("Login with wrong credentials should fail", true);
    }

    // 3. Test login success
    try {
        await login(testUser.username, testUser.password);
        logResult("Login with correct credentials should succeed", true);
    } catch (e) {
        logResult("Login with correct credentials should succeed", false, (e as Error).message);
        return;
    }

    // 4. Test authenticated createBook (ignore duplicate error)
    try {
        await createBook(testBook.isbn, testBook.title, testBook.authors);
        logResult("Authenticated createBook should succeed (or already exist)", true);
    } catch (e) {
        if ((e as any).status === 400) {
            logResult("Authenticated createBook duplicate", true);
        } else {
            logResult("Authenticated createBook", false, (e as Error).message);
        }
    }

    // 5. Test createBorrower (ignore duplicate error)
    try {
        await createBorrower(
            testBorrower.ssn,
            testBorrower.bname,
            testBorrower.address,
            testBorrower.phone,
            testBorrower.card_id
        );
        logResult("Create borrower should succeed (or already exist)", true);
    } catch (e) {
        if ((e as any).status === 400) {
            logResult("Create borrower duplicate", true);
        } else {
            logResult("Create borrower", false, (e as Error).message);
        }
    }

    // 6. Test createLibrarian (ignore duplicate error)
    try {
        await createLibrarian(testLibrarian.username, testLibrarian.password);
        logResult("Create librarian should succeed (or already exist)", true);
    } catch (e) {
        if ((e as any).status === 400) {
            logResult("Create librarian duplicate", true);
        } else {
            logResult("Create librarian", false, (e as Error).message);
        }
    }

    // 7. Test searchBooks
    try {
        const books = await searchBooks("Test Book");
        if (books.books.some((b) => b.isbn === testBook.isbn)) {
            logResult("searchBooks finds created book", true);
        } else {
            logResult("searchBooks finds created book", false);
        }
    } catch (e) {
        logResult("searchBooks", false, (e as Error).message);
    }

    // 8. Test searchBorrowers
    try {
        const borrowers = await searchBorrowers("Test Borrower");
        if (borrowers.borrowers.some((b) => b.card_id === testBorrower.card_id)) {
            logResult("searchBorrowers finds created borrower", true);
        } else {
            logResult("searchBorrowers finds created borrower", false);
        }
    } catch (e) {
        logResult("searchBorrowers", false, (e as Error).message);
    }

    // 9. Test checkoutBook
    try {
        const checkout = await checkoutBook(testBorrower.card_id, testBook.isbn);
        loanId = checkout.loan_id;
        logResult("checkoutBook should succeed (if not already checked out)", true);
    } catch (e) {
        if ((e as any).status === 400) {
            logResult("checkoutBook duplicate or already checked out", true);
        } else {
            logResult("checkoutBook", false, (e as Error).message);
        }
    }

    // 10. Test checkinBook (if loanId is available)
    if (loanId) {
        try {
            await checkinBook(loanId);
            logResult("checkinBook should succeed", true);
        } catch (e) {
            logResult("checkinBook", false, (e as Error).message);
        }
    } else {
        logResult("checkinBook skipped (no loanId)", true);
    }

    // 11. Test logout
    try {
        await logout();
        logResult("Logout should succeed", true);
    } catch (e) {
        logResult("Logout", false, (e as Error).message);
    }
}
