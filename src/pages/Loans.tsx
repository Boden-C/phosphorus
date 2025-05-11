import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Sidebar } from "@/components/Sidebar";

export default function Loans() {
    return (
        <div className="h-screen flex overflow-hidden">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 p-10 overflow-y-scroll">
                <Card>
                    <CardHeader>
                        <CardTitle>Active Loans</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Book Title</TableHead>
                                    <TableHead>Borrower</TableHead>
                                    <TableHead>Checkout Date</TableHead>
                                    <TableHead>Due Date</TableHead>
                                    <TableHead>Status</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                <TableRow>
                                    <TableCell>1984</TableCell>
                                    <TableCell>John Doe</TableCell>
                                    <TableCell>2024-06-15</TableCell>
                                    <TableCell>2024-07-10</TableCell>
                                    <TableCell>Active</TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>Pride and Prejudice</TableCell>
                                    <TableCell>Jane Smith</TableCell>
                                    <TableCell>2024-06-20</TableCell>
                                    <TableCell>2024-07-15</TableCell>
                                    <TableCell>Active</TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
