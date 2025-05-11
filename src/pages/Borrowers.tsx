"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Sidebar } from "@/components/Sidebar";


export default function Borrowers() {
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ name: "", ssn: "", address: "", phone: "" });
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async () => {
        setError("");
        setSuccess("");

        if (!form.name || !form.ssn || !form.address) {
            setError("Name, SSN, and Address are required.");
            return;
        }

        try {
            const res = await fetch("/api/borrower/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    bname: form.name,
                    ssn: form.ssn,
                    address: form.address,
                    phone: form.phone || null,
                }),
            });

            const data = await res.json();

            if (!res.ok) {
                setError(data.error || "Something went wrong.");
                return;
            }

            setSuccess(`Borrower "${data.name}" created successfully with card ID ${data.card_id}.`);
            setForm({ name: "", ssn: "", address: "", phone: "" });
            setTimeout(() => {
                setOpen(false);
                window.location.reload(); // or use React state if dynamic loading
            }, 1000);
        } catch (err) {
            setError("Server error. Please try again.");
        }
    };

    return (
        <div className="h-screen flex overflow-hidden">
            <Sidebar />
            <main className="flex-1 p-10 overflow-y-scroll">
                <Card>
                    <CardHeader className="flex items-center justify-between">
                        <CardTitle>Borrowers Management</CardTitle>
                        <Button onClick={() => setOpen(true)}>New Borrower</Button>
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

                {/* Create Borrower Modal */}
                {open && (
                    <div className="fixed inset-0 bg-black/30 backdrop-blur-xs flex items-center justify-center z-50">
                            <div className="bg-white rounded-lg p-6 w-full max-w-md space-y-4 shadow-lg">
                                <h2 className="text-xl font-bold">Add New Borrower</h2>
                                
                                <div>
                                    <label className="block text-sm font-medium">Name</label>
                                    <input
                                        name="name"
                                        value={form.name}
                                        onChange={handleChange}
                                        className="w-full border rounded p-2 mt-1"
                                        placeholder="Enter name"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium">SSN</label>
                                    <input
                                        name="ssn"
                                        value={form.ssn}
                                        onChange={handleChange}
                                        className="w-full border rounded p-2 mt-1"
                                        placeholder="Enter SSN"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium">Address</label>
                                    <input
                                        name="address"
                                        value={form.address}
                                        onChange={handleChange}
                                        className="w-full border rounded p-2 mt-1"
                                        placeholder="Enter address"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium">Phone (optional)</label>
                                    <input
                                        name="phone"
                                        value={form.phone}
                                        onChange={handleChange}
                                        className="w-full border rounded p-2 mt-1"
                                        placeholder="Enter phone"
                                    />
                                </div>

                                {error && <p className="text-red-600 text-sm">{error}</p>}
                                {success && <p className="text-green-600 text-sm">{success}</p>}

                                <div className="flex justify-end gap-2">
                                    <button
                                        onClick={() => setOpen(false)}
                                        className="px-4 py-2 border rounded bg-gray-200"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleSubmit}
                                        className="px-4 py-2 border rounded bg-blue-600 text-white"
                                    >
                                        Create
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
            </main>
        </div>
    );
}
