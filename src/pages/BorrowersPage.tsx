// src/pages/BorrowersPage.tsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

interface Borrower {
  card_id: string;
  ssn: string;
  bname: string;
  address: string;
  phone: string;
}

export default function BorrowersPage() {
  const [borrowers, setBorrowers] = useState<Borrower[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|null>(null);

  const [form, setForm] = useState({ bname: "", ssn: "", address: "", phone: "" });
  const [creating, setCreating] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    fetch(`/api/borrower/search?query=${encodeURIComponent(query)}&page=${page}&limit=10`, {
      credentials: "include",
    })
      .then(res => res.json().then(data => {
        if (!res.ok) throw new Error(data.error || "Failed to load");
        setBorrowers(data.borrowers);
        setTotal(data.total);
        setError(null);
      }))
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [page, query]);

  const handleInput = (e: React.ChangeEvent<HTMLInputElement|HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(f => ({ ...f, [name]: value }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await fetch("/api/borrower/create", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Create failed");
      setForm({ bname: "", ssn: "", address: "", phone: "" });
      setPage(1);
      setQuery("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r p-6 space-y-4">
        <h1 className="text-2xl font-bold">Library</h1>
        <button onClick={() => navigate("/dashboard")} className="block w-full text-left">Dashboard</button>
        <button onClick={() => navigate("/books")}     className="block w-full text-left">Books</button>
        <button onClick={() => navigate("/members")}   className="block w-full text-left">Members</button>
        <button onClick={() => navigate("/settings")}  className="block w-full text-left">Settings</button>
      </aside>

      {/* Main */}
      <main className="flex-1 p-8 space-y-8">
        {/* Create Form */}
        <div className="bg-white shadow rounded p-6">
          <h2 className="text-xl font-semibold mb-4">New Borrower</h2>
          {error && <p className="text-red-600 mb-2">{error}</p>}
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium">Name*</label>
              <input
                name="bname"
                value={form.bname}
                onChange={handleInput}
                required
                className="mt-1 block w-full border rounded p-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium">SSN*</label>
              <input
                name="ssn"
                value={form.ssn}
                onChange={handleInput}
                required
                placeholder="123-45-6789"
                className="mt-1 block w-full border rounded p-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium">Address*</label>
              <textarea
                name="address"
                value={form.address}
                onChange={handleInput}
                required
                className="mt-1 block w-full border rounded p-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium">Phone</label>
              <input
                name="phone"
                value={form.phone}
                onChange={handleInput}
                className="mt-1 block w-full border rounded p-2"
              />
            </div>
            <button
              type="submit"
              disabled={creating}
              className="bg-blue-600 text-white px-4 py-2 rounded"
            >
              {creating ? "Creating…" : "Create Borrower"}
            </button>
          </form>
        </div>

        {/* Search & List */}
        <div className="bg-white shadow rounded p-6">
          <h2 className="text-xl font-semibold mb-4">Members</h2>
          <div className="flex items-center mb-4 space-x-2">
            <input
              type="text"
              placeholder="Search by name, SSN…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              className="flex-1 border rounded p-2"
            />
            <button
              onClick={() => setPage(1)}
              className="bg-gray-200 px-4 py-2 rounded"
            >
              Search
            </button>
          </div>

          {loading ? (
            <p>Loading…</p>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {["Card ID", "Name", "SSN", "Address", "Phone"].map(h => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {borrowers.map(b => (
                  <tr key={b.card_id}>
                    <td className="px-6 py-4">{b.card_id}</td>
                    <td className="px-6 py-4">{b.bname}</td>
                    <td className="px-6 py-4">{b.ssn}</td>
                    <td className="px-6 py-4">{b.address}</td>
                    <td className="px-6 py-4">{b.phone}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="flex justify-between items-center mt-4">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="bg-gray-200 px-4 py-2 rounded"
            >
              ← Prev
            </button>
            <span>Page {page} of {Math.max(1, Math.ceil(total / 10))}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={borrowers.length < 10}
              className="bg-gray-200 px-4 py-2 rounded"
            >
              Next →
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
