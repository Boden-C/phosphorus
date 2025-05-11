import { cn } from "../lib/utils";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";

export type SortDirection = "asc" | "desc";

export interface SortOption {
    direction: SortDirection;
    label: string;
}

export interface SearchOption {
    id: string;
    label: string;
    keyword: string;
    value: string;
}

export interface SortFieldOption {
    id: string;
    label: string;
    value: string;
}

interface SearchOptionGroupProps {
    title?: string;
    options: SearchOption[];
    activeOptionId: string | null;
    onSelect: (option: SearchOption | null) => void;
    className?: string;
    sortOptions?: SortOption[];
    defaultSortDirection?: SortDirection;
    onSortChange?: (direction: SortDirection) => void;
    isSortGroup?: boolean;
    sortFields?: SortFieldOption[];
    activeSortFieldId?: string;
    onSortFieldChange?: (field: SortFieldOption) => void;
}

/**
 * Group of search filter options that can be selected exclusively.
 * Can be configured as a special sorting group with field and direction dropdowns.
 */
export function SearchOptionGroup({
    title,
    options,
    activeOptionId,
    onSelect,
    className,
    sortOptions,
    defaultSortDirection = "asc",
    onSortChange,
    isSortGroup = false,
    sortFields = [],
    activeSortFieldId,
    onSortFieldChange,
}: SearchOptionGroupProps) {
    const handleToggle = (option: SearchOption) => {
        if (option.id === activeOptionId) {
            // Deselect if already active
            onSelect(null);
        } else {
            // Select the new option
            onSelect(option);
        }
    };

    // If this is a sort group, render the sort field and direction dropdowns
    if (isSortGroup) {
        const activeSortField = sortFields.find((field) => field.id === activeSortFieldId) || sortFields[0];

        return (
            <div className={cn("flex flex-col gap-2", className)}>
                {title && <div className="text-xs font-medium text-muted-foreground">{title}</div>}

                <div className="flex items-center gap-2">
                    <div className="flex flex-col gap-1">
                        <Select
                            defaultValue={activeSortField?.id}
                            onValueChange={(value) => {
                                const field = sortFields.find((f) => f.id === value);
                                if (field && onSortFieldChange) {
                                    onSortFieldChange(field);
                                }
                            }}
                        >
                            <SelectTrigger className="w-[120px] h-5">
                                <SelectValue placeholder="Select field" />
                            </SelectTrigger>
                            <SelectContent>
                                {sortFields.map((field) => (
                                    <SelectItem key={field.id} value={field.id}>
                                        {field.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="flex flex-col gap-1">
                        <Select
                            defaultValue={defaultSortDirection}
                            onValueChange={(value) => onSortChange?.(value as SortDirection)}
                        >
                            <SelectTrigger className="w-[120px] h-5">
                                <SelectValue placeholder="Sort order" />
                            </SelectTrigger>
                            <SelectContent>
                                {sortOptions?.map((option) => (
                                    <SelectItem key={option.direction} value={option.direction}>
                                        {option.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </div>
            </div>
        );
    }

    // Standard option group with buttons
    return (
        <div className={cn("flex flex-col gap-1", className)}>
            {title && <div className="text-xs font-medium text-muted-foreground mb-1">{title}</div>}
            <div className="flex flex-wrap gap-1.5">
                {options.map((option) => {
                    const isActive = option.id === activeOptionId;
                    return (
                        <Button
                            key={option.id}
                            size="sm"
                            variant={isActive ? "default" : "outline"}
                            onClick={() => handleToggle(option)}
                            className={cn("text-xs h-7", isActive && "font-medium")}
                        >
                            {option.label}
                        </Button>
                    );
                })}
            </div>
        </div>
    );
}
