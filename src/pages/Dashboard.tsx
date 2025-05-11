import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/contexts/AuthContext";
import { useLocation, Link } from "react-router-dom";
import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { SearchArea } from "@/components/SearchArea";
import { Button } from "@/components/ui/button";
import { searchBooksWithLoan } from "@/lib/api";
import { SearchOption, SortDirection, SortOption, SortFieldOption } from "@/components/SearchOptionGroup";
import { CheckCircle, XCircle } from "lucide-react";
import { DataTable, TooltipCell, ColumnConfig } from "@/components/DataTable";

/**
 * Dashboard component that displays a searchable book list with loan information
 * with search on submission, improved loading state and infinite scroll pagination
 */
export default function Dashboard() {
    const { isAuthenticated } = useAuth();
    const location = useLocation();
    const from = location.state?.from;
    const [isLoading, setIsLoading] = useState(false);
    const [results, setResults] = useState<[Book, Loan | null][]>([]);
    const [totalBooks, setTotalBooks] = useState(0);
    const [sortField, setSortField] = useState<string>("title");
    const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedAvailabilityOption, setSelectedAvailabilityOption] = useState<SearchOption | null>(null);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const loaderRef = useRef<HTMLDivElement>(null);
    const ITEMS_PER_PAGE = 50;

    // Handle redirects from protected routes
    useEffect(() => {
        if (from && !isAuthenticated) {
            console.log(`Login required to access: ${from}`);
        }
    }, [from, isAuthenticated]);

    // Construct full search query with sort parameters
    const buildSearchQuery = useCallback(
        (baseQuery: string) => {
            // Extract sort and order if they're already in the query
            const sortRegex = /\bsort:([^\s]+)/;
            const orderRegex = /\border:([^\s]+)/;
            const availableRegex = /\bavailable:([^\s]+)/;

            let query = baseQuery.trim();

            // Remove existing sort and order terms
            query = query.replace(sortRegex, "").replace(orderRegex, "").replace(availableRegex, "").trim();

            // Add current sort and order
            query = `${query} sort:${sortField} order:${sortDirection}`.trim();

            // Add availability filter if selected
            if (selectedAvailabilityOption) {
                query = `${query} ${selectedAvailabilityOption.keyword}:${selectedAvailabilityOption.value}`;
            }

            return query;
        },
        [sortField, sortDirection, selectedAvailabilityOption]
    );

    // Initial search on component mount
    useEffect(() => {
        executeSearch("", 1, true);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Re-execute search when filter parameters change
    useEffect(() => {
        if (searchQuery !== "" || results.length > 0 || selectedAvailabilityOption !== null) {
            executeSearch(searchQuery, 1, true);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sortField, sortDirection, selectedAvailabilityOption]);

    // Setup intersection observer for infinite scrolling
    useEffect(() => {
        const options = {
            root: null,
            rootMargin: "20px",
            threshold: 0.1,
        };

        const observer = new IntersectionObserver(handleObserver, options);

        if (loaderRef.current) {
            observer.observe(loaderRef.current);
        }

        return () => {
            if (loaderRef.current) {
                observer.unobserve(loaderRef.current);
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [hasMore, isLoading]);

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
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [hasMore, isLoading, searchQuery]
    );

    // Execute search with current filter parameters
    const executeSearch = useCallback(
        (baseQuery: string, pageNum: number, resetResults: boolean) => {
            const query = buildSearchQuery(baseQuery);
            setIsLoading(true);

            searchBooksWithLoan(query, pageNum, ITEMS_PER_PAGE)
                .then((response) => {
                    if (resetResults) {
                        setResults(response.results);
                    } else {
                        setResults((prevResults) => [...prevResults, ...response.results]);
                    }

                    setTotalBooks(response.total);
                    setHasMore(response.results.length > 0 && pageNum * ITEMS_PER_PAGE < response.total);
                })
                .catch((error) => {
                    console.error("Error searching books:", error);
                    if (resetResults) {
                        setResults([]);
                    }
                    setTotalBooks(0);
                    setHasMore(false);
                })
                .finally(() => {
                    setIsLoading(false);
                });
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [buildSearchQuery]
    );

    // Search handler for the SearchArea component - only triggered on submit
    const handleSearch = useCallback(
        (query: string) => {
            setSearchQuery(query);
            setPage(1);
            executeSearch(query, 1, true);
        },
        [executeSearch]
    );

    // Handle availability option selection
    const handleAvailabilitySelect = useCallback((option: SearchOption | null) => {
        setSelectedAvailabilityOption(option);
        setPage(1); // Reset page on filter change
    }, []);

    // Handle sort field change
    const handleSortFieldChange = useCallback((field: SortFieldOption) => {
        setSortField(field.value);
        setPage(1); // Reset page on filter change
    }, []);

    // Handle sort direction change
    const handleSortChange = useCallback((direction: SortDirection) => {
        setSortDirection(direction);
        setPage(1); // Reset page on filter change
    }, []);

    // Column definitions for the book table
    const columns = useMemo<ColumnConfig<[Book, Loan | null]>[]>(
        () => [
            {
                key: "isbn",
                header: "ISBN",
                width: "10%",
                headerClassName: "text-xs",
                cellClassName: "font-mono text-xs text-muted-foreground",
                render: ([book]) => <TooltipCell content={book.isbn} />,
            },
            {
                key: "title",
                header: "Title",
                width: "45%",
                cellClassName: "font-medium",
                render: ([book]) => <TooltipCell content={book.title} />,
            },
            {
                key: "authors",
                header: "Authors",
                width: "30%",
                render: ([book]) => <TooltipCell content={book.authors.join(", ")} />,
            },
            {
                key: "status",
                header: "Status",
                width: "5%",
                headerClassName: "text-center",
                cellClassName: "text-center",
                render: ([, loan]) => {
                    const isAvailable = !loan || loan.date_in !== null;
                    return isAvailable ? (
                        <CheckCircle className="h-5 w-5 inline-block text-green-500" aria-label="Available" />
                    ) : (
                        <XCircle className="h-5 w-5 inline-block text-red-500" aria-label="Checked out" />
                    );
                },
            },
            {
                key: "borrower",
                header: "Borrower",
                width: "10%",
                headerClassName: "text-xs",
                cellClassName: "text-xs text-muted-foreground",
                render: ([book, loan]) => {
                    return loan && !loan.date_in ? (
                        <TooltipCell content={loan.card_id} />
                    ) : (
                        <Button size="sm" variant="outline" disabled={!isAuthenticated} asChild>
                            <Link to={`/checkout?isbn=${book.isbn}`}>Checkout</Link>
                        </Button>
                    );
                },
            },
        ],
        [isAuthenticated]
    );

    // Search options for filtering
    const availabilityOptions: SearchOption[] = [
        {
            id: "available",
            label: "Only Available",
            keyword: "available",
            value: "true",
        },
    ];

    // Sort field options
    const sortFieldOptions: SortFieldOption[] = [
        {
            id: "title",
            label: "Title",
            value: "title",
        },
        {
            id: "isbn",
            label: "ISBN",
            value: "isbn",
        },
        {
            id: "author",
            label: "Author",
            value: "author",
        },
    ];

    // Sort direction options
    const sortDirectionOptions: SortOption[] = [
        { direction: "asc", label: "Ascending" },
        { direction: "desc", label: "Descending" },
    ];

    return (
        <div className="h-screen flex overflow-hidden">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 p-10 overflow-y-scroll">
                <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

                {/* Search Area */}
                <div className="mb-6">
                    <SearchArea
                        initialQuery={searchQuery}
                        onSearch={handleSearch}
                        optionGroups={[
                            {
                                id: "availability",
                                title: "Availability",
                                options: availabilityOptions,
                                onChange: handleAvailabilitySelect,
                            },
                        ]}
                        sortConfig={{
                            id: "sort",
                            title: "Sort",
                            sortFields: sortFieldOptions,
                            activeSortFieldId: sortFieldOptions.find((sf) => sf.value === sortField)?.id || "title",
                            onSortFieldChange: handleSortFieldChange,
                            sortOptions: sortDirectionOptions,
                            defaultSortDirection: sortDirection,
                            onSortChange: handleSortChange,
                        }}
                    />
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Books Overview {totalBooks > 0 && `(${totalBooks} books found)`}</CardTitle>
                    </CardHeader>
                    <CardContent className="px-0 sm:px-2">
                        {results.length > 0 ? (
                            <div
                                className={`transition-opacity duration-200 ${isLoading && page === 1 ? "opacity-60" : "opacity-100"}`}
                            >
                                <DataTable
                                    data={results}
                                    columns={columns}
                                    getRowKey={(item, index) => `${item[0].isbn}-${index}`}
                                    getRowClassName={([, loan]) => (!loan || loan.date_in !== null ? "" : "opacity-80")}
                                />

                                {/* Intersection observer target for infinite scrolling */}
                                <div ref={loaderRef} className="py-4 flex justify-center">
                                    {/* Only show loading indicator when fetching more data, not during initial load */}
                                    {isLoading && page > 1 && <p>Loading more...</p>}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-10">
                                {isLoading ? (
                                    <p>Searching...</p>
                                ) : totalBooks === 0 &&
                                  (searchQuery.trim() !== "" || selectedAvailabilityOption !== null) ? (
                                    <p>No books found. Try adjusting your search query or filters.</p>
                                ) : (
                                    <p>Enter terms to search for books and press Enter to search.</p>
                                )}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
