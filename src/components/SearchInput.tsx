import { useState, KeyboardEvent, FormEvent } from "react";
import { Search, X } from "lucide-react";
import { cn } from "../lib/utils";
import { Button } from "./ui/button";

interface SearchInputProps {
    value: string;
    onChange: (value: string) => void;
    onSearch?: () => void;
    className?: string;
}

/**
 * Search input component for query input
 *
 * Performs search on form submission or Enter key press
 */
export function SearchInput({ value, onChange, onSearch, className }: SearchInputProps) {
    const [isFocused, setIsFocused] = useState(false);

    const handleClear = () => {
        onChange("");
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter" && onSearch) {
            e.preventDefault();
            onSearch();
        }
    };

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (onSearch) {
            onSearch();
        }
    };

    return (
        <form onSubmit={handleSubmit} className="w-full">
            <div
                className={cn(
                    "flex items-center gap-2 h-9 w-full rounded-md border bg-background px-3 py-1 text-sm shadow-sm transition-all",
                    isFocused && "ring-1 ring-ring",
                    className
                )}
            >
                <Search className="h-4 w-4 shrink-0 opacity-50" />
                <input
                    className="flex-grow border-0 bg-transparent p-0 outline-none placeholder:text-muted-foreground focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    onKeyDown={handleKeyDown}
                    placeholder="Search..."
                />
                {value && (
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-5 w-5 p-0 opacity-70 hover:opacity-100"
                        onClick={handleClear}
                    >
                        <X className="h-4 w-4" />
                        <span className="sr-only">Clear</span>
                    </Button>
                )}
                <Button type="submit" className="sr-only">
                    Search
                </Button>
            </div>
        </form>
    );
}
