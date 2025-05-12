import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sidebar } from "@/components/Sidebar";
import { Link, useLocation } from "react-router-dom";
import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { SearchArea } from "@/components/SearchArea";
import { Button } from "@/components/ui/button";
import { searchBorrowersWithInfo } from "@/lib/api";
import { SearchOption, SortDirection, SortFieldOption } from "@/components/SearchOptionGroup";
import { DataTable, TooltipCell, ColumnConfig } from "@/components/DataTable";

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
    const [finesPaid, setFinesPaid] = useState<Record<string, number>>({});

    const buildSearchQuery = useCallback((baseQuery: string) => {
        const sortRegex = /\bsort:([^\s]+)/;
        const orderRegex = /\border:([^\s]+)/;
        const loansRegex = /\bloan_is:([^\s]+)/;
        const finesRegex = /\bfine_is:([^\s]+)/;

        let query = baseQuery.trim();
        query = query.replace(sortRegex, "").replace(orderRegex, "").replace(loansRegex, "").replace(finesRegex, "").trim();
        query = `${query} sort:${sortField} order:${sortDirection}`.trim();
        if (selectedStatusOption) {
            query = `${query} ${selectedStatusOption.keyword}:${selectedStatusOption.value}`;
        }
        return query;
    }, [sortField, sortDirection, selectedStatusOption]);

    const executeSearch = useCallback((baseQuery: string, pageNum: number, resetResults: boolean) => {
        const query = buildSearchQuery(baseQuery);
        setIsLoading(true);
        searchBorrowersWithInfo(query, pageNum, ITEMS_PER_PAGE)
            .then((response) => {
                if (resetResults) setResults(response.results);
                else setResults((prev) => [...prev, ...response.results]);
                setTotalBorrowers(response.total);
                setHasMore(response.results.length > 0 && pageNum * ITEMS_PER_PAGE < response.total);
            })
            .catch(() => {
                if (resetResults) setResults([]);
                setTotalBorrowers(0);
                setHasMore(false);
            })
            .finally(() => setIsLoading(false));
    }, [buildSearchQuery]);

    const handleSearch = useCallback((query: string) => {
        setSearchQuery(query);
        setPage(1);
        executeSearch(query, 1, true);
    }, [executeSearch]);

    const handleObserver = useCallback((entries: IntersectionObserverEntry[]) => {
        const target = entries[0];
        if (target.isIntersecting && hasMore && !isLoading) {
            setPage((prev) => {
                const nextPage = prev + 1;
                executeSearch(searchQuery, nextPage, false);
                return nextPage;
            });
        }
    }, [hasMore, isLoading, searchQuery, executeSearch]);

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const queryParam = params.get("query") || "";
        setSearchQuery(queryParam);
        executeSearch(queryParam, 1, true);
        setPage(1);
    }, [location.search]);

    useEffect(() => {
        if (searchQuery !== "" || results.length > 0 || selectedStatusOption !== null) {
            executeSearch(searchQuery, 1, true);
            setPage(1);
        }
    }, [sortField, sortDirection, selectedStatusOption]);

    useEffect(() => {
        const options = { root: null, rootMargin: "20px", threshold: 0.1 };
        const observer = new IntersectionObserver(handleObserver, options);
        const currentRef = loaderRef.current;
        if (currentRef) observer.observe(currentRef);
        return () => { if (currentRef) observer.unobserve(currentRef); };
    }, [hasMore, isLoading]);

    useEffect(() => {
        async function fetchFinesPaid() {
            const promises = results.map(async ([b]) => {
                try {
                    const res = await fetch(`/api/borrower/fines?card_id=${b.card_id}&include_paid=true`, {
                        credentials: "include",
                    });
                    const data = await res.json();
                    if (data && data.total_fines !== undefined) {
                        const owed = results.find(([br]) => br.card_id === b.card_id)?.[3] || 0;
                        const paid = data.total_fines - owed;
                        return [b.card_id, paid > 0 ? paid : 0];
                    }
                } catch {
                    return [b.card_id, 0];
                }
                return [b.card_id, 0];
            });

            const entries = await Promise.all(promises);
            const map = Object.fromEntries(entries);
            setFinesPaid(map);
        }

        if (results.length > 0) {
            fetchFinesPaid();
        }
    }, [results]);

    const columns = useMemo<ColumnConfig<[Borrower, number, number, number]>[]>(() => [
        { key: "card_id", header: "Card ID", width: "12%", render: ([b]) => <TooltipCell content={b.card_id} /> },
        { key: "name", header: "Borrower Name", width: "25%", render: ([b]) => <TooltipCell content={b.bname} /> },
        { key: "phone", header: "Phone", width: "15%", render: ([b]) => <TooltipCell content={b.phone || "-"} /> },
        { key: "total_loans", header: "Total Loans", width: "12%", render: ([b, , total_loans]) => total_loans > 0 ? <Button variant="link" className="p-0 h-auto" asChild><Link to={`/loans?query=card:${b.card_id}`}>{total_loans}</Link></Button> : <span>0</span> },
        { key: "fines", header: "Fines Owed", width: "15%", render: ([b, , , fine]) => fine > 0 ? <Button variant="link" className="p-0 h-auto text-destructive" asChild><Link to={`/loans?query=card:${b.card_id} fine_is:owed`}>${fine.toFixed(2)}</Link></Button> : <span className="text-muted-foreground">None</span> },
        { key: "fines_paid", header: "Fines Paid", width: "12%", render: ([b]) => {
            const paid = finesPaid[b.card_id] || 0;
            return paid > 0 ? <span className="text-green-600 font-medium">${paid.toFixed(2)}</span> : <span className="text-muted-foreground">None</span>;
        }},
        { key: "checkin", header: "Checkin", width: "16%", render: ([b, active_loans]) => active_loans > 0 ? <Button variant="outline" size="sm" asChild><Link to={`/loans?query=card:${b.card_id} loan_is:active`}>Checkin {active_loans} {active_loans === 1 ? "Book" : "Books"}</Link></Button> : <span className="text-muted-foreground">None</span> },
    ], [finesPaid]);

    const statusOptions: SearchOption[] = [
        { id: "active_loans", label: "Has Active Loans", keyword: "loan_is", value: "active" },
        { id: "owes_fines", label: "Owes Fines", keyword: "fine_is", value: "owed" },
    ];

    const sortFieldOptions: SortFieldOption[] = [
        { id: "card_id", label: "Card ID", value: "card_id" },
        { id: "name", label: "Name", value: "borrower" },
        { id: "fines", label: "Fines", value: "fine_amt" },
    ];

    return (
        <div className="h-screen flex overflow-hidden">
            <Sidebar />
            <main className="flex-1 p-10 overflow-y-scroll">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-3xl font-bold">Borrowers Management</h1>
                    <Button onClick={() => window.location.href='/borrowers/create'}>New Borrower</Button>
                </div>
                <div className="mb-6">
                    <SearchArea
                        key={searchQuery}
                        initialQuery={searchQuery}
                        onSearch={handleSearch}
                        optionGroups={[{ id: "status", title: "Filter", options: statusOptions, onChange: setSelectedStatusOption }]}
                        sortConfig={{
                            id: "sort",
                            title: "Sort By",
                            sortFields: sortFieldOptions,
                            activeSortFieldId: sortFieldOptions.find((sf) => sf.value === sortField)?.id || "card_id",
                            onSortFieldChange: setSortField,
                            defaultSortDirection: sortDirection,
                            onSortChange: setSortDirection,
                        }}
                    />
                </div>
                <Card>
                    <CardHeader>
                        <CardTitle>Borrowers {totalBorrowers > 0 && `(${totalBorrowers} found)`}</CardTitle>
                    </CardHeader>
                    <CardContent className="px-0 sm:px-2">
                        {results.length > 0 ? (
                            <div className={`transition-opacity duration-200 ${isLoading && page === 1 ? "opacity-60" : "opacity-100"}`}>
                                <DataTable data={results} columns={columns} getRowKey={(item) => item[0].card_id} />
                                <div ref={loaderRef} className="py-4 flex justify-center">
                                    {isLoading && page > 1 && <p>Loading more...</p>}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-10">
                                {isLoading ? <p>Searching...</p> : <p>No borrowers found.</p>}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
