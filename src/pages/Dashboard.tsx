import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function Dashboard() {
    return (
        <div className="min-h-screen flex">
            {/* Sidebar */}
            <aside className="w-64 border-r flex flex-col p-6">
                <h1 className="text-2xl font-bold mb-8">Library</h1>
                <nav className="flex flex-col gap-4">
                    <Button variant="ghost" className="justify-start">
                        Dashboard
                    </Button>
                    <Button variant="ghost" className="justify-start">
                        Books
                    </Button>
                    <Button variant="ghost" className="justify-start">
                        Members
                    </Button>
                    <Button variant="ghost" className="justify-start">
                        Settings
                    </Button>
                </nav>
            </aside>
            {/* Main Content */}
            <main className="flex-1 p-10">
                <Card>
                    <CardHeader>
                        <CardTitle>Books Overview</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Title</TableHead>
                                    <TableHead>Author</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Due Date</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                <TableRow>
                                    <TableCell>The Great Gatsby</TableCell>
                                    <TableCell>F. Scott Fitzgerald</TableCell>
                                    <TableCell>Available</TableCell>
                                    <TableCell>-</TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>1984</TableCell>
                                    <TableCell>George Orwell</TableCell>
                                    <TableCell>Checked Out</TableCell>
                                    <TableCell>2024-07-10</TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>To Kill a Mockingbird</TableCell>
                                    <TableCell>Harper Lee</TableCell>
                                    <TableCell>Available</TableCell>
                                    <TableCell>-</TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
