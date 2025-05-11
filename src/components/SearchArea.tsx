import React, { useCallback, useEffect, useState, useRef } from "react";
import { cn } from "../lib/utils";
import { Card, CardContent } from "./ui/card";
import { SearchInput } from "./SearchInput";
import { SearchOption, SearchOptionGroup, SortDirection, SortOption, SortFieldOption } from "./SearchOptionGroup";

export interface SearchAreaProps {
    initialQuery?: string;
    onSearch?: (query: string) => void;
    optionGroups?: Array<{
        id: string;
        title?: string;
        options: SearchOption[];
        onChange?: (option: SearchOption | null) => void;
    }>;
    sortConfig?: {
        id: string;
        title?: string;
        sortFields?: SortFieldOption[];
        activeSortFieldId?: string;
        onSortFieldChange?: (field: SortFieldOption) => void;
        sortOptions?: SortOption[];
        defaultSortDirection?: SortDirection;
        onSortChange?: (direction: SortDirection) => void;
    };
    className?: string;
}

/**
 * SearchArea component with search input and filter options
 *
 * Supports keyword-based search, filter option groups, and sort configuration
 * that appears on the right side of the component
 */
export function SearchArea({ initialQuery = "", onSearch, optionGroups = [], sortConfig, className }: SearchAreaProps) {
    const [query, setQuery] = useState(initialQuery);
    const [activeOptions, setActiveOptions] = useState<Record<string, string | null>>({});
    const [userTyped, setUserTyped] = useState(true); // Flag to track if changes are from user typing
    const [sortDirection, setSortDirection] = useState<SortDirection>(sortConfig?.defaultSortDirection || "asc");
    const [sortField, setSortField] = useState<string | undefined>(sortConfig?.activeSortFieldId);
    const activeOptionsUpdateTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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

    // Update active options when query changes (debounced)
    useEffect(() => {
        if (!userTyped) return;
        if (activeOptionsUpdateTimeoutRef.current) {
            clearTimeout(activeOptionsUpdateTimeoutRef.current);
        }
        activeOptionsUpdateTimeoutRef.current = setTimeout(() => {
            const parsedKeywords = parseQuery(query);
            const newCalculatedActiveState: Record<string, string | null> = {};
            optionGroups.forEach((group) => {
                newCalculatedActiveState[group.id] = null;
                for (const option of group.options) {
                    const keyword = option.keyword.toLowerCase();
                    if (
                        parsedKeywords[keyword] &&
                        parsedKeywords[keyword].value.toLowerCase() === option.value.toLowerCase()
                    ) {
                        newCalculatedActiveState[group.id] = option.id;
                        break;
                    }
                }
            });
            setActiveOptions((currentInternalState) => {
                let needsUpdate = false;
                const updatedState = { ...currentInternalState };
                optionGroups.forEach((group) => {
                    const groupId = group.id;
                    const newOptionForGroup =
                        groupId in newCalculatedActiveState ? newCalculatedActiveState[groupId] : null;
                    if (currentInternalState[groupId] !== newOptionForGroup) {
                        updatedState[groupId] = newOptionForGroup;
                        needsUpdate = true;
                    }
                });
                return needsUpdate ? updatedState : currentInternalState;
            });
        }, 150);
        return () => {
            if (activeOptionsUpdateTimeoutRef.current) {
                clearTimeout(activeOptionsUpdateTimeoutRef.current);
            }
        };
    }, [query, optionGroups, userTyped, parseQuery]);

    // Handle option selection (button click)
    const handleSelectOption = useCallback(
        (groupId: string, optionToSet: SearchOption | null) => {
            setUserTyped(false);
            setActiveOptions((prev) => ({
                ...prev,
                [groupId]: optionToSet?.id || null,
            }));
            if (activeOptionsUpdateTimeoutRef.current) {
                clearTimeout(activeOptionsUpdateTimeoutRef.current);
            }
            const group = optionGroups.find((g) => g.id === groupId);
            if (!group) {
                if (onSearch && query.trim() !== (initialQuery || "")) {
                    onSearch(query.trim());
                }
                setTimeout(() => setUserTyped(true), 0);
                return;
            }
            const currentQuery = query;
            const keywordsInGroup = new Set(group.options.map((opt) => opt.keyword.toLowerCase()));
            const queryTerms = currentQuery.trim().split(/\s+/).filter(Boolean);
            const remainingTerms = queryTerms.filter((term) => {
                const match = term.match(/^([^:]+):/);
                if (match) {
                    const keyword = match[1].toLowerCase();
                    return !keywordsInGroup.has(keyword);
                }
                return true;
            });
            const newQueryParts = [...remainingTerms];
            if (optionToSet) {
                const keyword = optionToSet.keyword.toLowerCase();
                const value = optionToSet.value;
                const formattedValue = value.includes(" ") ? `"${value}"` : value;
                newQueryParts.unshift(`${keyword}:${formattedValue}`);
            }
            let newQueryString = newQueryParts.join(" ").trim();
            if (newQueryString) {
                newQueryString += " ";
            }
            setQuery(newQueryString);
            if (onSearch) {
                onSearch(newQueryString.trim());
            }
            setTimeout(() => setUserTyped(true), 0);
            if (group.onChange) {
                group.onChange(optionToSet);
            }
        },
        [query, optionGroups, onSearch, initialQuery]
    );

    // Handle sort field change
    const handleSortFieldChange = useCallback(
        (field: SortFieldOption) => {
            setSortField(field.id);

            // Update the query with the sort field
            updateQueryWithSortParams(query, field.value, sortDirection);

            // Call handler if provided
            if (sortConfig?.onSortFieldChange) {
                sortConfig.onSortFieldChange(field);
            }
        },
        [query, sortDirection, sortConfig]
    );

    // Handle sort direction change
    const handleSortChange = useCallback(
        (direction: SortDirection) => {
            setSortDirection(direction);

            // Get the sort field value to update the query
            const sortFieldObj = sortConfig?.sortFields?.find((f) => f.id === sortField);
            const sortFieldValue = sortFieldObj?.value || "title";

            // Update the query with the sort field and direction
            updateQueryWithSortParams(query, sortFieldValue, direction);

            // Call handler if provided
            if (sortConfig?.onSortChange) {
                sortConfig.onSortChange(direction);
            }
        },
        [query, sortField, sortConfig]
    );

    // Update query with sort parameters
    const updateQueryWithSortParams = useCallback(
        (currentQuery: string, field: string, direction: SortDirection) => {
            setUserTyped(false);

            // Remove existing sort and order terms
            let newQuery = currentQuery
                .replace(/\bsort:(?:"[^"]+"|[^\s]+)\s*/gi, "")
                .replace(/\border:(?:"[^"]+"|[^\s]+)\s*/gi, "")
                .trim();

            // Add the new sort parameters
            newQuery = `${newQuery} sort:${field} order:${direction}`.trim();

            setQuery(newQuery);

            // Call onSearch if provided
            if (onSearch) {
                onSearch(newQuery);
            }

            // Reset the flag after a short delay
            setTimeout(() => setUserTyped(true), 0);
        },
        [onSearch]
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

                <div className="flex justify-between items-start">
                    {/* Filter Option Groups */}
                    {optionGroups.length > 0 && (
                        <div className="flex flex-wrap gap-4 flex-1">
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

                    {/* Sort Options - Right Side */}
                    {sortConfig && (
                        <div className="ml-4 pl-4 border-l border-border">
                            <SearchOptionGroup
                                title={sortConfig.title}
                                options={[]}
                                activeOptionId={null}
                                onSelect={() => {}}
                                isSortGroup={true}
                                sortFields={sortConfig.sortFields}
                                activeSortFieldId={sortConfig.activeSortFieldId}
                                onSortFieldChange={handleSortFieldChange}
                                sortOptions={sortConfig.sortOptions}
                                defaultSortDirection={sortConfig.defaultSortDirection || "asc"}
                                onSortChange={handleSortChange}
                            />
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
