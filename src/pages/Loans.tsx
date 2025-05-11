import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sidebar } from "@/components/Sidebar";
import { useLocation } from "react-router-dom";
import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { SearchArea } from "@/components/SearchArea";
import { Button } from "@/components/ui/button";
import { searchLoansWithBook, checkinBook, payLoanFine } from "@/lib/api";
import { SearchOption, SortDirection, SortFieldOption } from "@/components/SearchOptionGroup";
import { DataTable, TooltipCell, ColumnConfig } from "@/components/DataTable";
import { toast } from "sonner";

/**
 * Loans management page with search functionality and loan information
 */
export default function Loans() {
    const location = useLocation();
    const [isLoading, setIsLoading] = useState(false);
    const [results, setResults] = useState<[Loan, Book][]>([]);
    const [totalLoans, setTotalLoans] = useState(0);
    const [sortField, setSortField] = useState<string>("date_out");
    const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedLoanStatus, setSelectedLoanStatus] = useState<SearchOption | null>(null);
    const [selectedFineStatus, setSelectedFineStatus] = useState<SearchOption | null>(null);
    const [selectedDueStatus, setSelectedDueStatus] = useState<SearchOption | null>(null);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const loaderRef = useRef<HTMLDivElement>(null);
    const ITEMS_PER_PAGE = 20;
    const [processingLoanIds, setProcessingLoanIds] = useState<Set<string>>(new Set());

    // Construct full search query with all parameters
    const buildSearchQuery = useCallback(
        (baseQuery: string) => {
            // Extract existing keywords
            const sortRegex = /\bsort:([^\s]+)/;
            const orderRegex = /\border:([^\s]+)/;
            const loanStatusRegex = /\bloan_is:([^\s]+)/;
            const fineStatusRegex = /\bfine_is:([^\s]+)/;
            const dueStatusRegex = /\bdue:([^\s]+)/;

            let query = baseQuery.trim();

            // Remove existing keywords
            query = query
                .replace(sortRegex, "")
                .replace(orderRegex, "")
                .replace(loanStatusRegex, "")
                .replace(fineStatusRegex, "")
                .replace(dueStatusRegex, "")
                .trim();

            // Add current sort and order
            query = `${query} sort:${sortField} order:${sortDirection}`.trim();

            // Add filters if selected
            if (selectedLoanStatus) {
                query = `${query} ${selectedLoanStatus.keyword}:${selectedLoanStatus.value}`;
            }

            if (selectedFineStatus) {
                query = `${query} ${selectedFineStatus.keyword}:${selectedFineStatus.value}`;
            }

            if (selectedDueStatus) {
                query = `${query} ${selectedDueStatus.keyword}:${selectedDueStatus.value}`;
            }

            return query;
        },
        [sortField, sortDirection, selectedLoanStatus, selectedFineStatus, selectedDueStatus]
    );

    // Execute search with current filter parameters
    const executeSearch = useCallback(
        (baseQuery: string, pageNum: number, resetResults: boolean) => {
            const query = buildSearchQuery(baseQuery);
            setIsLoading(true);

            searchLoansWithBook(query, pageNum, ITEMS_PER_PAGE)
                .then((response) => {
                    if (resetResults) {
                        setResults(response.results);
                    } else {
                        setResults((prevResults) => [...prevResults, ...response.results]);
                    }

                    setTotalLoans(response.total);
                    setHasMore(response.results.length > 0 && pageNum * ITEMS_PER_PAGE < response.total);
                })
                .catch((error) => {
                    console.error("Error searching loans:", error);
                    if (resetResults) {
                        setResults([]);
                    }
                    setTotalLoans(0);
                    setHasMore(false);
                })
                .finally(() => {
                    setIsLoading(false);
                });
        },
        [buildSearchQuery]
    );

    // Intersection observer handler
    const handleObserver = useCallback(
        (entries: IntersectionObserverEntry[]) => {
            const target = entries[0];
            if (target.isIntersecting && hasMore && !isLoading) {
                setPage((prevPage) => {
                    const nextPage = prevPage + 1;
                    executeSearch(searchQuery, nextPage, false);
                    return nextPage;
                });
            }
        },
        [hasMore, isLoading, searchQuery, executeSearch]
    );

    // Extract query from URL search params on component mount and initialize filters
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const queryParam = params.get("query");
        if (queryParam) {
            setSearchQuery(queryParam);

            // Pre-select filter options from URL query
            const loanStatusMatch = queryParam.match(/loan_is:([^\s]+)/);
            if (loanStatusMatch) {
                const value = loanStatusMatch[1];
                const option = loanStatusOptions.find((opt) => opt.value === value);
                if (option) {
                    setSelectedLoanStatus(option);
                }
            }

            const fineStatusMatch = queryParam.match(/fine_is:([^\s]+)/);
            if (fineStatusMatch) {
                const value = fineStatusMatch[1];
                const option = fineStatusOptions.find((opt) => opt.value === value);
                if (option) {
                    setSelectedFineStatus(option);
                }
            }

            const dueStatusMatch = queryParam.match(/due:([^\s]+)/);
            if (dueStatusMatch) {
                const value = dueStatusMatch[1];
                const option = dueStatusOptions.find((opt) => opt.value === value);
                if (option) {
                    setSelectedDueStatus(option);
                }
            }

            executeSearch(queryParam, 1, true);
        } else {
            executeSearch("", 1, true);
        }
        setPage(1);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [location.search]);

    // Re-execute search when filter parameters change
    useEffect(() => {
        if (
            searchQuery !== "" ||
            results.length > 0 ||
            selectedLoanStatus !== null ||
            selectedFineStatus !== null ||
            selectedDueStatus !== null
        ) {
            executeSearch(searchQuery, 1, true);
            setPage(1);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sortField, sortDirection, selectedLoanStatus, selectedFineStatus, selectedDueStatus]);

    // Setup intersection observer for infinite scrolling
    useEffect(() => {
        const options = {
            root: null,
            rootMargin: "20px",
            threshold: 0.1,
        };

        const observer = new IntersectionObserver(handleObserver, options);
        const currentRef = loaderRef.current;

        if (currentRef) {
            observer.observe(currentRef);
        }

        return () => {
            if (currentRef) {
                observer.unobserve(currentRef);
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [hasMore, isLoading]);

    // Search handler - triggered on submit
    const handleSearch = useCallback(
        (query: string) => {
            setSearchQuery(query);
            setPage(1);
            executeSearch(query, 1, true);
        },
        [executeSearch]
    );

    // Handle loan option selection
    const handleLoanStatusSelect = useCallback((option: SearchOption | null) => {
        setSelectedLoanStatus(option);
        setPage(1);
    }, []);

    // Handle fine option selection
    const handleFineStatusSelect = useCallback((option: SearchOption | null) => {
        setSelectedFineStatus(option);
        setPage(1);
    }, []);

    // Handle due option selection
    const handleDueStatusSelect = useCallback((option: SearchOption | null) => {
        setSelectedDueStatus(option);
        setPage(1);
    }, []);

    // Handle sort field change
    const handleSortFieldChange = useCallback((field: SortFieldOption) => {
        setSortField(field.value);
        setPage(1);
    }, []);

    // Handle sort direction change
    const handleSortChange = useCallback((direction: SortDirection) => {
        setSortDirection(direction);
        setPage(1);
    }, []);

    // Handle check-in book
    const handleCheckin = useCallback(
        async (loanId: string) => {
            setProcessingLoanIds((prev) => new Set(prev).add(loanId));

            try {
                await checkinBook(loanId);
                toast.success("Book checked in successfully");
                // Refresh the data
                executeSearch(searchQuery, page, true);
            } catch (error) {
                toast.error(error instanceof Error ? error.message : "Failed to check in book");
            } finally {
                setProcessingLoanIds((prev) => {
                    const updated = new Set(prev);
                    updated.delete(loanId);
                    return updated;
                });
            }
        },
        [executeSearch, page, searchQuery]
    );

    // Handle pay fine
    const handlePayFine = useCallback(
        async (loanId: string) => {
            setProcessingLoanIds((prev) => new Set(prev).add(loanId));

            try {
                await payLoanFine(loanId);
                toast.success("Fine paid successfully");
                // Refresh the data
                executeSearch(searchQuery, page, true);
            } catch (error) {
                toast.error(error instanceof Error ? error.message : "Failed to pay fine");
            } finally {
                setProcessingLoanIds((prev) => {
                    const updated = new Set(prev);
                    updated.delete(loanId);
                    return updated;
                });
            }
        },
        [executeSearch, page, searchQuery]
    );

    // Format date for display with status context
    const formatDate = useCallback((loan: Loan) => {
        const today = new Date();

        if (loan.date_in) {
            return `Returned on ${loan.date_in}`;
        } else if (loan.due_date) {
            const dueDate = new Date(loan.due_date);
            if (dueDate < today) {
                return `Past due ${loan.due_date}`;
            } else {
                return `Due by ${loan.due_date}`;
            }
        }

        return "Unknown";
    }, []);

    // Column definitions for the loans table
    const columns = useMemo<ColumnConfig<[Loan, Book]>[]>(
        () => [
            {
                key: "loan_id",
                header: "Loan ID",
                width: "10%",
                cellClassName: "font-mono text-xs",
                render: ([loan]) => <TooltipCell content={loan.loan_id} />,
            },
            {
                key: "borrower",
                header: "Borrower",
                width: "15%",
                cellClassName: "font-medium",
                render: ([loan]) => <TooltipCell content={loan.card_id} />,
            },
            {
                key: "book",
                header: "Book",
                width: "30%",
                render: ([, book]) => <TooltipCell content={book.title} />,
            },
            {
                key: "date_out",
                header: "Date Out",
                width: "10%",
                render: ([loan]) => <span>{loan.date_out || "N/A"}</span>,
            },
            {
                key: "due_date",
                header: "Due Date",
                width: "15%",
                render: ([loan]) => (
                    <span
                        className={`${!loan.date_in && new Date(loan.due_date!) < new Date() ? "text-destructive font-medium" : ""}`}
                    >
                        {formatDate(loan)}
                    </span>
                ),
            },
            {
                key: "fine",
                header: "Fine",
                width: "12%",
                render: ([loan]) => {
                    if (loan.fine_amt <= 0) {
                        return <span className="text-muted-foreground">-</span>;
                    }

                    if (loan.paid) {
                        return <span className="text-muted-foreground">Paid ${loan.fine_amt.toFixed(2)}</span>;
                    }

                    return (
                        <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-destructive"
                            onClick={() => handlePayFine(loan.loan_id)}
                            disabled={processingLoanIds.has(loan.loan_id)}
                        >
                            Pay ${loan.fine_amt.toFixed(2)}
                        </Button>
                    );
                },
            },
            {
                key: "actions",
                header: "Actions",
                width: "8%",
                render: ([loan]) => {
                    // Only show check-in button for active loans
                    if (!loan.date_in) {
                        return (
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-7 hover:bg-secondary hover:text-secondary-foreground"
                                onClick={() => handleCheckin(loan.loan_id)}
                                disabled={processingLoanIds.has(loan.loan_id)}
                            >
                                Checkin
                            </Button>
                        );
                    }
                    return null;
                },
            },
        ],
        [formatDate, handleCheckin, handlePayFine, processingLoanIds]
    );

    // Loan status filter options
    const loanStatusOptions: SearchOption[] = [
        {
            id: "active",
            label: "Active",
            keyword: "loan_is",
            value: "active",
        },
        {
            id: "returned",
            label: "Returned",
            keyword: "loan_is",
            value: "returned",
        },
    ];

    // Fine status filter options
    const fineStatusOptions: SearchOption[] = [
        {
            id: "owed",
            label: "Fine Owed",
            keyword: "fine_is",
            value: "owed",
        },
        {
            id: "paid",
            label: "Fine Paid",
            keyword: "fine_is",
            value: "paid",
        },
    ];

    // Due date status filter options
    const dueStatusOptions: SearchOption[] = [
        {
            id: "past",
            label: "Past Due",
            keyword: "due",
            value: "past",
        },
        {
            id: "future",
            label: "Due in Future",
            keyword: "due",
            value: "future",
        },
    ];

    // Sort field options
    const sortFieldOptions: SortFieldOption[] = [
        {
            id: "date_out",
            label: "Date Out",
            value: "date_out",
        },
        {
            id: "due_date",
            label: "Due Date",
            value: "due_date",
        },
        {
            id: "borrower",
            label: "Borrower",
            value: "borrower",
        },
        {
            id: "title",
            label: "Book Title",
            value: "title",
        },
    ];

    return (
        <div className="h-screen flex overflow-hidden">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 p-10 overflow-y-scroll">
                <h1 className="text-3xl font-bold mb-6">Loans Management</h1>
                {/* Search Area */}
                <div className="mb-6">
                    <SearchArea
                        key={searchQuery} // Add key prop to force re-render when searchQuery changes
                        initialQuery={searchQuery}
                        onSearch={handleSearch}
                        optionGroups={[
                            {
                                id: "loan_status",
                                title: "Loan Status",
                                options: loanStatusOptions,
                                onChange: handleLoanStatusSelect,
                            },
                            {
                                id: "fine_status",
                                title: "Fine Status",
                                options: fineStatusOptions,
                                onChange: handleFineStatusSelect,
                            },
                            {
                                id: "due_status",
                                title: "Due Date",
                                options: dueStatusOptions,
                                onChange: handleDueStatusSelect,
                            },
                        ]}
                        sortConfig={{
                            id: "sort",
                            title: "Sort By",
                            sortFields: sortFieldOptions,
                            activeSortFieldId: sortFieldOptions.find((sf) => sf.value === sortField)?.id || "date_out",
                            onSortFieldChange: handleSortFieldChange,
                            defaultSortDirection: sortDirection,
                            onSortChange: handleSortChange,
                        }}
                    />
                </div>
                <Card>
                    <CardHeader>
                        <CardTitle>Loans {totalLoans > 0 && `(${totalLoans} found)`}</CardTitle>
                    </CardHeader>
                    <CardContent className="px-0 sm:px-2">
                        {results.length > 0 ? (
                            <div
                                className={`transition-opacity duration-200 ${isLoading && page === 1 ? "opacity-60" : "opacity-100"}`}
                            >
                                <DataTable
                                    data={results}
                                    columns={columns}
                                    getRowKey={(item) => item[0].loan_id}
                                    getRowClassName={([loan]) => {
                                        if (!loan.date_in && loan.due_date && new Date(loan.due_date) < new Date()) {
                                            return "bg-destructive/5";
                                        }
                                        return "";
                                    }}
                                />

                                {/* Intersection observer target for infinite scrolling */}
                                <div ref={loaderRef} className="py-4 flex justify-center">
                                    {isLoading && page > 1 && <p>Loading more...</p>}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-10">
                                {isLoading ? (
                                    <p>Searching...</p>
                                ) : totalLoans === 0 && searchQuery.trim() !== "" ? (
                                    <p>No loans found. Try adjusting your search query or filters.</p>
                                ) : (
                                    <p>Enter terms to search for loans and press Enter to search.</p>
                                )}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
