import React from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

/**
 * Configuration for a column in the DataTable
 */
export interface ColumnConfig<T> {
    /** Unique identifier for the column */
    key: string;
    /** Header text displayed for the column */
    header: string;
    /** Width of the column (CSS value like "10%" or "150px") */
    width: string;
    /** Custom renderer for the cell content */
    render: (item: T, index: number) => React.ReactNode;
    /** Optional class names to apply to the header cell */
    headerClassName?: string;
    /** Optional class names to apply to the data cells in this column */
    cellClassName?: string;
}

/**
 * Props for the DataTable component
 */
export interface DataTableProps<T> {
    /** Array of data items to display in the table */
    data: T[];
    /** Configuration for each column */
    columns: ColumnConfig<T>[];
    /** Function to determine the unique key for each row */
    getRowKey: (item: T, index: number) => string;
    /** Optional class to apply to a row based on the item */
    getRowClassName?: (item: T, index: number) => string;
    /** Optional maximum height for the table content */
    maxHeight?: string;
}

/**
 * A generic, reusable table component that renders data according to provided column configurations.
 * Supports tooltips for truncated content, custom cell rendering, and row styling.
 */
export function DataTable<T>({ data, columns, getRowKey, getRowClassName, maxHeight }: DataTableProps<T>) {
    return (
        <div className="overflow-x-auto" style={maxHeight ? { maxHeight, overflowY: "auto" } : undefined}>
            <Table className="table-fixed">
                <colgroup>
                    {columns.map((column) => (
                        <col key={column.key} style={{ width: column.width }} />
                    ))}
                </colgroup>
                <TableHeader>
                    <TableRow>
                        {columns.map((column) => (
                            <TableHead key={column.key} className={column.headerClassName}>
                                {column.header}
                            </TableHead>
                        ))}
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.length > 0 ? (
                        data.map((item, index) => (
                            <TableRow
                                key={getRowKey(item, index)}
                                className={getRowClassName ? getRowClassName(item, index) : undefined}
                            >
                                {columns.map((column) => (
                                    <TableCell key={column.key} className={column.cellClassName}>
                                        {column.render(item, index)}
                                    </TableCell>
                                ))}
                            </TableRow>
                        ))
                    ) : (
                        <TableRow>
                            <TableCell colSpan={columns.length} className="text-center py-4">
                                No data available
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        </div>
    );
}

/**
 * Creates a cell with a tooltip that appears when content is truncated
 *
 * @param content - The text content to display
 * @param className - Optional class names for styling
 * @returns A cell with tooltip functionality
 */
export function TooltipCell({ content, className = "" }: { content: string; className?: string }) {
    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger className={`text-left w-full truncate block ${className}`}>{content}</TooltipTrigger>
                <TooltipContent>
                    <p>{content}</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}
