import { cn } from "../lib/utils";
import { Button } from "./ui/button";

export interface SearchOption {
    id: string;
    label: string;
    keyword: string;
    value: string;
}

interface SearchOptionGroupProps {
    title?: string;
    options: SearchOption[];
    activeOptionId: string | null;
    onSelect: (option: SearchOption | null) => void;
    className?: string;
}

/**
 * Group of search filter options that can be selected exclusively
 */
export function SearchOptionGroup({ title, options, activeOptionId, onSelect, className }: SearchOptionGroupProps) {
    const handleToggle = (option: SearchOption) => {
        if (option.id === activeOptionId) {
            // Deselect if already active
            onSelect(null);
        } else {
            // Select the new option
            onSelect(option);
        }
    };

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
