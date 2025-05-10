// src/Dashboard.tsx
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableHead, TableBody, TableRow, TableCell } from "@/components/ui/table";

export default function Dashboard() {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 border-r flex flex-col p-6">
        <h1 className="text-2xl font-bold mb-8">Library</h1>
        <nav className="flex flex-col gap-4">
            <Button asChild variant="ghost" className="justify-start">
            <Link to="/dashboard">Dashboard</Link>
            </Button>
          <Button asChild variant="ghost" className="justify-start">
            <Link to="/books">Books</Link>
          </Button>
            <Button asChild variant="ghost" className="justify-start">
                <Link to="/members">Members</Link>
            </Button>
          <Button asChild variant="ghost" className="justify-start">
            <Link to="/settings">Settings</Link>
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
                {/* ...other rows */}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
