import React, { useState } from "react";
import { SearchArea } from "../components/SearchArea";
import { SearchOption } from "../components/SearchOptionGroup";
import { Sidebar } from "@/components/Sidebar";

// Example option groups
const availabilityOptions: SearchOption[] = [
    { id: "available", label: "Available", keyword: "available", value: "true" },
    { id: "unavailable", label: "Checked Out", keyword: "available", value: "false" },
];

const sortOptions: SearchOption[] = [
    { id: "sort-title", label: "Sort by Title", keyword: "sort", value: "title" },
    { id: "sort-author", label: "Sort by Author", keyword: "sort", value: "author" },
    { id: "sort-date", label: "Sort by Date", keyword: "sort", value: "date" },
];

const optionGroups = [
    {
        id: "availability",
        title: "Availability",
        options: availabilityOptions,
    },
    {
        id: "sort",
        title: "Sort By",
        options: sortOptions,
    },
];

/**
 * Test page demonstrating the SearchArea component
 */
const Test: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState<string>("");

    // Search handler function
    const handleSearch = (query: string) => {
        setSearchQuery(query);
        console.log("Search query:", query);
    };

    return (
        <div className="h-screen flex overflow-hidden">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 p-10 overflow-y-auto">
                <h1 className="text-2xl font-bold">Search Component Test</h1>

                <p className="text-muted-foreground">
                    Search using keywords like <code>author:"John Doe"</code>, <code>title:Hobbit</code>, or{" "}
                    <code>isbn:9781234567897</code>, or use the option buttons below.
                </p>

                <SearchArea
                    onSearch={handleSearch}
                    optionGroups={optionGroups}
                    initialQuery="The Lord of the Rings author:Tolkien"
                />

                {searchQuery && (
                    <div className="mt-4 p-2 bg-muted rounded-md">
                        <h3 className="font-medium">Current search query:</h3>
                        <code>{searchQuery}</code>
                    </div>
                )}

                <div className="p-4 border rounded-md bg-muted/20 mt-4">
                    <h2 className="font-semibold mb-2">Example Search Queries:</h2>
                    <ul className="space-y-1 list-disc list-inside text-sm">
                        <li>
                            <code>The Hobbit</code> - Simple text search
                        </li>
                        <li>
                            <code>author:"J.R.R. Tolkien"</code> - Search by author (quoted)
                        </li>
                        <li>
                            <code>title:Hobbit available:true</code> - Multiple keywords
                        </li>
                        <li>
                            <code>sort:date</code> - Sort results by date
                        </li>
                    </ul>
                </div>
            </main>
        </div>
    );
};

export default Test;
