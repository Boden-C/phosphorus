import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Sidebar } from "@/components/Sidebar";

export default function Checkout() {
    return (
        <div className="min-h-screen flex">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 p-10">
                <Card>
                    <CardHeader>
                        <CardTitle>Book Checkout</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>ISBN</TableHead>
                                    <TableHead>Title</TableHead>
                                    <TableHead>Author</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Action</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                <TableRow>
                                    <TableCell>9780743273565</TableCell>
                                    <TableCell>The Great Gatsby</TableCell>
                                    <TableCell>F. Scott Fitzgerald</TableCell>
                                    <TableCell>Available</TableCell>
                                    <TableCell>Checkout</TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>9780060935467</TableCell>
                                    <TableCell>To Kill a Mockingbird</TableCell>
                                    <TableCell>Harper Lee</TableCell>
                                    <TableCell>Available</TableCell>
                                    <TableCell>Checkout</TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
