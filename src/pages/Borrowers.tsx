import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Sidebar } from "@/components/Sidebar";

export default function Borrowers() {
    return (
        <div className="min-h-screen flex">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 p-10">
                <Card>
                    <CardHeader>
                        <CardTitle>Borrowers Management</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Email</TableHead>
                                    <TableHead>Books Borrowed</TableHead>
                                    <TableHead>Status</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                <TableRow>
                                    <TableCell>John Doe</TableCell>
                                    <TableCell>john.doe@example.com</TableCell>
                                    <TableCell>2</TableCell>
                                    <TableCell>Active</TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>Jane Smith</TableCell>
                                    <TableCell>jane.smith@example.com</TableCell>
                                    <TableCell>1</TableCell>
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
