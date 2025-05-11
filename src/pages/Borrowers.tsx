import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sidebar } from "@/components/Sidebar";
import { Link, useLocation } from "react-router-dom";
import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { SearchArea } from "@/components/SearchArea";
import { Button } from "@/components/ui/button";
import { searchBorrowersWithInfo } from "@/lib/api";
import { SearchOption, SortDirection, SortFieldOption } from "@/components/SearchOptionGroup";
import { DataTable, TooltipCell, ColumnConfig } from "@/components/DataTable";

/**
 * Borrowers management page with search functionality and borrower information
 */
export default function Borrowers() {
    const location = useLocation();
    const [isLoading, setIsLoading] = useState(false);
    const [results, setResults] = useState<[Borrower, number, number, number][]>([]);
    const [totalBorrowers, setTotalBorrowers] = useState(0);
    const [sortField, setSortField] = useState<string>("card_id");
    const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedStatusOption, setSelectedStatusOption] = useState<SearchOption | null>(null);
    const ITEMS_PER_PAGE = 20;
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const loaderRef = useRef<HTMLDivElement>(null);

    // Construct full search query with parameters
    const buildSearchQuery = useCallback(
        (baseQuery: string) => {
            // Extract existing keywords if present
            const sortRegex = /\bsort:([^\s]+)/;
            const orderRegex = /\border:([^\s]+)/;
            const loansRegex = /\bloan_is:([^\s]+)/;
            const finesRegex = /\bfine_is:([^\s]+)/;

            let query = baseQuery.trim();

            // Remove existing keywords
            query = query
                .replace(sortRegex, "")
                .replace(orderRegex, "")
                .replace(loansRegex, "")
                .replace(finesRegex, "")
                .trim();

            // Add current sort and order
            query = `${query} sort:${sortField} order:${sortDirection}`.trim();

            // Add status filter if selected
            if (selectedStatusOption) {
                query = `${query} ${selectedStatusOption.keyword}:${selectedStatusOption.value}`;
            }

            return query;
        },
        [sortField, sortDirection, selectedStatusOption]
    );

    // Execute search with current filter parameters
    const executeSearch = useCallback(
        (baseQuery: string, pageNum: number, resetResults: boolean) => {
            const query = buildSearchQuery(baseQuery);
            setIsLoading(true);

            searchBorrowersWithInfo(query, pageNum, ITEMS_PER_PAGE)
                .then((response) => {
                    if (resetResults) {
                        setResults(response.results);
                    } else {
                        setResults((prevResults) => [...prevResults, ...response.results]);
                    }

                    setTotalBorrowers(response.total);
                    setHasMore(response.results.length > 0 && pageNum * ITEMS_PER_PAGE < response.total);
                })
                .catch((error) => {
                    console.error("Error searching borrowers:", error);
                    if (resetResults) {
                        setResults([]);
                    }
                    setTotalBorrowers(0);
                    setHasMore(false);
                })
                .finally(() => {
                    setIsLoading(false);
                });
        },
        [buildSearchQuery]
    );

    // Search handler - triggered on submit
    const handleSearch = useCallback(
        (query: string) => {
            setSearchQuery(query);
            setPage(1);
            executeSearch(query, 1, true);
        },
        [executeSearch]
    );

    // Handle status option selection
    const handleStatusSelect = useCallback((option: SearchOption | null) => {
        setSelectedStatusOption(option);
        // Execute search with updated filter
    }, []);

    // Handle sort field change
    const handleSortFieldChange = useCallback((field: SortFieldOption) => {
        setSortField(field.value);
        // Sort field changes are handled via useEffect
    }, []);

    // Handle sort direction change
    const handleSortChange = useCallback((direction: SortDirection) => {
        setSortDirection(direction);
        // Sort direction changes are handled via useEffect
    }, []);

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

    // Extract query from URL search params on component mount and when location changes
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const queryParam = params.get("query") || "";

        // Update the search query state
        setSearchQuery(queryParam);

        // Pre-select filter options from URL query if present
        const loanStatusMatch = queryParam.match(/loan_is:([^\s]+)/);
        if (loanStatusMatch) {
            const value = loanStatusMatch[1];
            const option = statusOptions.find((opt) => opt.value === value);
            if (option) {
                setSelectedStatusOption(option);
            }
        }

        const fineStatusMatch = queryParam.match(/fine_is:([^\s]+)/);
        if (fineStatusMatch) {
            const value = fineStatusMatch[1];
            const option = statusOptions.find((opt) => opt.value === value && opt.keyword === "fine_is");
            if (option) {
                setSelectedStatusOption(option);
            }
        }

        executeSearch(queryParam, 1, true);
        setPage(1);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [location.search]);

    // Re-execute search when filter parameters change
    useEffect(() => {
        if (searchQuery !== "" || results.length > 0 || selectedStatusOption !== null) {
            executeSearch(searchQuery, 1, true);
            setPage(1);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sortField, sortDirection, selectedStatusOption]);

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

    // Column definitions for the borrowers table
    const columns = useMemo<ColumnConfig<[Borrower, number, number, number]>[]>(
        () => [
            {
                key: "card_id",
                header: "Card ID",
                width: "12%",
                cellClassName: "font-mono text-xs",
                render: ([borrower]) => <TooltipCell content={borrower.card_id} />,
            },
            {
                key: "name",
                header: "Borrower Name",
                width: "25%",
                cellClassName: "font-medium",
                render: ([borrower]) => <TooltipCell content={borrower.bname} />,
            },
            {
                key: "phone",
                header: "Phone",
                width: "15%",
                render: ([borrower]) => <TooltipCell content={borrower.phone || "-"} />,
            },
            {
                key: "total_loans",
                header: "Total Loans",
                width: "12%",
                render: ([borrower, , total_loans]) =>
                    total_loans > 0 ? (
                        <Button variant="link" className="p-0 h-auto" asChild>
                            <Link to={`/loans?query=card:${borrower.card_id}`}>{total_loans}</Link>
                        </Button>
                    ) : (
                        <span>0</span>
                    ),
            },
            {
                key: "fines",
                header: "Fines Owed",
                width: "15%",
                render: ([borrower, , , fineAmount]) =>
                    fineAmount > 0 ? (
                        <Button variant="link" className="p-0 h-auto text-destructive" asChild>
                            <Link to={`/loans?query=card:${borrower.card_id} fine_is:owed`}>
                                ${fineAmount.toFixed(2)}
                            </Link>
                        </Button>
                    ) : (
                        <span className="text-muted-foreground">None</span>
                    ),
            },
            {
                key: "checkin",
                header: "Checkin",
                width: "16%",
                render: ([borrower, active_loans]) =>
                    active_loans > 0 ? (
                        <Button variant="outline" size="sm" asChild>
                            <Link to={`/loans?query=card:${borrower.card_id} loan_is:active`}>
                                Checkin {active_loans} {active_loans === 1 ? "Book" : "Books"}
                            </Link>
                        </Button>
                    ) : (
                        <span className="text-muted-foreground">None</span>
                    ),
            },
        ],
        []
    );

    // Search options for filtering
    const statusOptions: SearchOption[] = [
        {
            id: "active_loans",
            label: "Has Active Loans",
            keyword: "loan_is",
            value: "active",
        },
        {
            id: "owes_fines",
            label: "Owes Fines",
            keyword: "fine_is",
            value: "owed",
        },
    ];

    // Sort field options
    const sortFieldOptions: SortFieldOption[] = [
        {
            id: "card_id",
            label: "Card ID",
            value: "card_id",
        },
        {
            id: "name",
            label: "Name",
            value: "borrower",
        },
        {
            id: "fines",
            label: "Fines",
            value: "fine_amt",
        },
    ];

    return (
        <div className="h-screen flex overflow-hidden">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 p-10 overflow-y-scroll">
                <h1 className="text-3xl font-bold mb-6">Borrowers Management</h1>
                {/* Search Area */}
                <div className="mb-6">
                    <SearchArea
                        key={searchQuery} // Add key prop to force re-render when searchQuery changes
                        initialQuery={searchQuery}
                        onSearch={handleSearch}
                        optionGroups={[
                            {
                                id: "status",
                                title: "Filter",
                                options: statusOptions,
                                onChange: handleStatusSelect,
                            },
                        ]}
                        sortConfig={{
                            id: "sort",
                            title: "Sort By",
                            sortFields: sortFieldOptions,
                            activeSortFieldId: sortFieldOptions.find((sf) => sf.value === sortField)?.id || "card_id",
                            onSortFieldChange: handleSortFieldChange,
                            defaultSortDirection: sortDirection,
                            onSortChange: handleSortChange,
                        }}
                    />
                </div>
                <Card>
                    <CardHeader>
                        <CardTitle>Borrowers {totalBorrowers > 0 && `(${totalBorrowers} found)`}</CardTitle>
                    </CardHeader>
                    <CardContent className="px-0 sm:px-2">
                        {results.length > 0 ? (
                            <div
                                className={`transition-opacity duration-200 ${isLoading && page === 1 ? "opacity-60" : "opacity-100"}`}
                            >
                                <DataTable data={results} columns={columns} getRowKey={(item) => item[0].card_id} />

                                {/* Intersection observer target for infinite scrolling */}
                                <div ref={loaderRef} className="py-4 flex justify-center">
                                    {isLoading && page > 1 && <p>Loading more...</p>}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-10">
                                {isLoading ? (
                                    <p>Searching...</p>
                                ) : totalBorrowers === 0 && searchQuery.trim() !== "" ? (
                                    <p>No borrowers found. Try adjusting your search query or filters.</p>
                                ) : (
                                    <p>Enter terms to search for borrowers and press Enter to search.</p>
                                )}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
