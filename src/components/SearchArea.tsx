import React, { useCallback, useEffect, useState } from "react";
import { cn } from "../lib/utils";
import { Card, CardContent } from "./ui/card";
import { SearchInput } from "./SearchInput";
import { SearchOption, SearchOptionGroup } from "./SearchOptionGroup";

export interface SearchAreaProps {
    initialQuery?: string;
    onSearch?: (query: string) => void;
    optionGroups?: Array<{
        id: string;
        title?: string;
        options: SearchOption[];
    }>;
    className?: string;
}

/**
 * SearchArea component with search input and filter options
 *
 * Supports keyword-based search and filter option groups
 */
export function SearchArea({ initialQuery = "", onSearch, optionGroups = [], className }: SearchAreaProps) {
    const [query, setQuery] = useState(initialQuery);
    const [activeOptions, setActiveOptions] = useState<Record<string, string | null>>({});
    const [userTyped, setUserTyped] = useState(true); // Flag to track if changes are from user typing

    // Parse query for existing keywords
    const parseQuery = useCallback((searchQuery: string) => {
        const result: Record<string, { keyword: string; value: string }> = {};

        // Simple regex to match keyword:value or keyword:"quoted value"
        const pattern = /(\w+):(?:"([^"]+)"|([^\s]+))/g;
        let match;

        while ((match = pattern.exec(searchQuery)) !== null) {
            const keyword = match[1].toLowerCase();
            const value = match[2] || match[3]; // match[2] is quoted value, match[3] is unquoted

            result[keyword] = { keyword, value };
        }

        return result;
    }, []);

    // Update active options when query changes
    useEffect(() => {
        if (!userTyped) return; // Skip if change wasn't from user typing

        const parsedKeywords = parseQuery(query);
        const newActiveOptions = { ...activeOptions };

        // For each option group
        optionGroups.forEach((group) => {
            let foundActive = false;

            // Check if any option's keyword is in the parsed keywords
            for (const option of group.options) {
                const keyword = option.keyword.toLowerCase();

                if (
                    parsedKeywords[keyword] &&
                    parsedKeywords[keyword].value.toLowerCase() === option.value.toLowerCase()
                ) {
                    newActiveOptions[group.id] = option.id;
                    foundActive = true;
                    break;
                }
            }

            // If no option was found in the query, deactivate
            if (!foundActive && newActiveOptions[group.id]) {
                newActiveOptions[group.id] = null;
            }
        });

        // Update active options state if changed
        const hasChanges = Object.keys(newActiveOptions).some(
            (groupId) => newActiveOptions[groupId] !== activeOptions[groupId]
        );

        if (hasChanges) {
            setActiveOptions(newActiveOptions);
        }
    }, [query, optionGroups, userTyped, parseQuery, activeOptions]);

    // Handle option selection (button click)
    const handleSelectOption = useCallback(
        (groupId: string, option: SearchOption | null) => {
            // Set the flag to indicate this change is from button click, not typing
            setUserTyped(false);

            setActiveOptions((prev) => ({
                ...prev,
                [groupId]: option?.id || null,
            }));

            // Modify query based on option selection
            const parsedKeywords = parseQuery(query);
            let newQuery = query;

            if (option) {
                const keyword = option.keyword.toLowerCase();

                // Remove existing keyword for this group if present
                if (parsedKeywords[keyword]) {
                    const pattern = new RegExp(`${keyword}:(?:"[^"]+"|[^\\s]+)\\s*`, "i");
                    newQuery = newQuery.replace(pattern, "");
                }

                // Add the new keyword value
                const value = option.value;
                const formattedValue = value.includes(" ") ? `"${value}"` : value;

                // Prepend to the beginning of the query with a trailing space
                newQuery = `${keyword}:${formattedValue} ${newQuery.trim()}`.trim() + " ";

                setQuery(newQuery);

                // Call onSearch if provided
                if (onSearch) {
                    onSearch(newQuery);
                }
            } else {
                // Option is null, user is deselecting
                // Find which option was previously selected in this group
                const optionId = activeOptions[groupId];
                if (optionId) {
                    const previousOption = optionGroups
                        .find((g) => g.id === groupId)
                        ?.options.find((o) => o.id === optionId);

                    if (previousOption) {
                        const keyword = previousOption.keyword.toLowerCase();

                        // Remove this keyword from the query
                        if (parsedKeywords[keyword]) {
                            const pattern = new RegExp(`${keyword}:(?:"[^"]+"|[^\\s]+)\\s*`, "i");
                            newQuery = newQuery.replace(pattern, "");

                            setQuery(newQuery);

                            // Call onSearch if provided
                            if (onSearch) {
                                onSearch(newQuery);
                            }
                        }
                    }
                }
            }

            // Reset the flag after a short delay to allow for the effect to run
            setTimeout(() => setUserTyped(true), 0);
        },
        [query, activeOptions, optionGroups, onSearch, parseQuery]
    );

    // Handle search query changes
    const handleQueryChange = (value: string) => {
        setUserTyped(true);
        setQuery(value);

        if (onSearch) {
            onSearch(value);
        }
    };

    return (
        <Card className={cn("", className)}>
            <CardContent className="p-4 space-y-4">
                <SearchInput value={query} onChange={handleQueryChange} />

                {optionGroups.length > 0 && (
                    <div className="flex flex-wrap gap-4">
                        {optionGroups.map((group) => (
                            <React.Fragment key={group.id}>
                                <SearchOptionGroup
                                    title={group.title}
                                    options={group.options}
                                    activeOptionId={activeOptions[group.id] || null}
                                    onSelect={(option) => handleSelectOption(group.id, option)}
                                />

                                {/* Divider except for last group */}
                                {optionGroups.indexOf(group) < optionGroups.length - 1 && (
                                    <div className="w-px self-stretch bg-border" />
                                )}
                            </React.Fragment>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
