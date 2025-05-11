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

    const [openNew, setOpenNew] = useState(false);
    const [form, setForm] = useState({ name: "", ssn: "", address: "", phone: "" });
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async () => {
        setError("");
        setSuccess("");

        if (!form.name || !form.ssn || !form.address) {
            setError("Name, SSN, and Address are required.");
            return;
        }

        try {
            const res = await fetch("/api/borrower/create", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    bname: form.name,
                    ssn: form.ssn,
                    address: form.address,
                    phone: form.phone || null,
                }),
            });

            const data = await res.json();

            if (!res.ok) {
                setError(data.error || "Failed to create borrower.");
                return;
            }

            setSuccess("Borrower created successfully.");
            setForm({ name: "", ssn: "", address: "", phone: "" });
            setOpenNew(false);
            handleSearch("");
        } catch (err) {
            setError("Server error. Please try again.");
        }
    };

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

    const handleStatusSelect = useCallback((option: SearchOption | null) => setSelectedStatusOption(option), []);
    const handleSortFieldChange = useCallback((field: SortFieldOption) => setSortField(field.value), []);
    const handleSortChange = useCallback((direction: SortDirection) => setSortDirection(direction), []);

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

    const columns = useMemo<ColumnConfig<[Borrower, number, number, number]>[]>(() => [
        { key: "card_id", header: "Card ID", width: "12%", cellClassName: "font-mono text-xs", render: ([b]) => <TooltipCell content={b.card_id} /> },
        { key: "name", header: "Borrower Name", width: "25%", cellClassName: "font-medium", render: ([b]) => <TooltipCell content={b.bname} /> },
        { key: "phone", header: "Phone", width: "15%", render: ([b]) => <TooltipCell content={b.phone || "-"} /> },
        { key: "total_loans", header: "Total Loans", width: "12%", render: ([b, , total_loans]) => total_loans > 0 ? <Button variant="link" className="p-0 h-auto" asChild><Link to={`/loans?query=card:${b.card_id}`}>{total_loans}</Link></Button> : <span>0</span> },
        { key: "fines", header: "Fines Owed", width: "15%", render: ([b, , , fine]) => fine > 0 ? <Button variant="link" className="p-0 h-auto text-destructive" asChild><Link to={`/loans?query=card:${b.card_id} fine_is:owed`}>${fine.toFixed(2)}</Link></Button> : <span className="text-muted-foreground">None</span> },
        { key: "checkin", header: "Checkin", width: "16%", render: ([b, active_loans]) => active_loans > 0 ? <Button variant="outline" size="sm" asChild><Link to={`/loans?query=card:${b.card_id} loan_is:active`}>Checkin {active_loans} {active_loans === 1 ? "Book" : "Books"}</Link></Button> : <span className="text-muted-foreground">None</span> },
    ], []);

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
                    <Button onClick={() => setOpenNew(true)}>New Borrower</Button>
                </div>
                <div className="mb-6">
                    <SearchArea
                        key={searchQuery}
                        initialQuery={searchQuery}
                        onSearch={handleSearch}
                        optionGroups={[{ id: "status", title: "Filter", options: statusOptions, onChange: handleStatusSelect }]}
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

                {/* Add New Borrower Modal */}
                {openNew && (
                <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-md p-6 w-full max-w-md space-y-4 text-gray-800">
                    <h2 className="text-xl font-semibold">Add New Borrower</h2>

                    <div className="space-y-3">
                        {[
                        { key: "name", label: "Name" },
                        { key: "ssn", label: "SSN" },
                        { key: "address", label: "Address" },
                        { key: "phone", label: "Phone (optional)" },
                        ].map(({ key, label }) => (
                        <div key={key}>
                            <label htmlFor={key} className="block text-sm text-gray-700 font-medium">
                            {label}
                            </label>
                            <input
                            id={key}
                            name={key}
                            value={form[key as keyof typeof form]}
                            onChange={handleChange}
                            placeholder={`Enter ${label.toLowerCase()}`}
                            className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
                            />
                        </div>
                        ))}
                        {error && <p className="text-sm text-red-600">{error}</p>}
                        {success && <p className="text-sm text-green-600">{success}</p>}
                    </div>

                    <div className="flex justify-end gap-3 pt-3">
                        <button
                        onClick={() => setOpenNew(false)}
                        className="px-4 py-2 rounded-md text-sm bg-gray-100 hover:bg-gray-200"
                        >
                        Cancel
                        </button>
                        <button
                        onClick={handleSubmit}
                        className="px-4 py-2 rounded-md text-sm bg-neutral-800 text-white hover:bg-neutral-900"
                        >
                        Create
                        </button>
                    </div>
                    </div>
                </div>
                )}
            </main>
        </div>
    );
}
