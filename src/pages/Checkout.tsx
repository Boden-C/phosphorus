import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sidebar } from "@/components/Sidebar";
import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { checkoutBook } from "@/lib/api";

/**
 * Checkout page component that allows checking out books by ISBN and borrower card ID
 */
export default function Checkout() {
    const [isbn, setIsbn] = useState("");
    const [cardId, setCardId] = useState("ID");
    const [isLoading, setIsLoading] = useState(false);
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    // Handle URL parameters on component mount
    useEffect(() => {
        const isbnParam = searchParams.get("isbn");
        const cardParam = searchParams.get("card");

        if (isbnParam) {
            setIsbn(isbnParam);
        }

        if (cardParam) {
            setCardId(cardParam);
        }
    }, [searchParams]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!isbn.trim()) {
            toast.error("ISBN is required");
            return;
        }

        if (!cardId.trim() || cardId === "ID") {
            toast.error("Valid Card ID is required");
            return;
        }

        setIsLoading(true);

        try {
            const response = await checkoutBook(cardId, isbn);
            toast.success(`Book checked out successfully. Loan ID: ${response.loan_id}`);

            // Reset form or navigate back to dashboard
            navigate("/");
        } catch (error) {
            toast.error(error instanceof Error ? error.message : "Unknown error occurred");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-screen flex overflow-hidden">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 p-10 overflow-y-scroll">
                <h1 className="text-3xl font-bold mb-6">Book Checkout</h1>

                <Card className="max-w-md mx-auto">
                    <CardHeader>
                        <CardTitle>Checkout Form</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <Label htmlFor="isbn">ISBN</Label>
                                <Input
                                    id="isbn"
                                    value={isbn}
                                    onChange={(e) => setIsbn(e.target.value)}
                                    placeholder="Enter ISBN"
                                    disabled={isLoading}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="cardId">Card ID</Label>
                                <Input
                                    id="cardId"
                                    value={cardId}
                                    onChange={(e) => setCardId(e.target.value)}
                                    placeholder="Enter Card ID"
                                    disabled={isLoading}
                                />
                            </div>

                            <Button type="submit" className="w-full" disabled={isLoading}>
                                {isLoading ? "Processing..." : "Checkout Book"}
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
