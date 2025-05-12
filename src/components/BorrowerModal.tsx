import { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { createBorrower, searchBorrowersWithInfo } from "@/lib/api";

interface BorrowerModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreated: (borrower: { card_id: string; name: string }) => void;
}

export function BorrowerModal({ isOpen, onClose, onCreated }: BorrowerModalProps) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [formData, setFormData] = useState({
        bname: "",
        ssn: "",
        address: "",
        phone: "",
        card_id: "",
    });
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [apiError, setApiError] = useState<string>("");
    const [nextCardId, setNextCardId] = useState<string>("");
    useEffect(() => {
        if (isOpen) {
            fetchNextCardId();
        }
    }, [isOpen]);

    const fetchNextCardId = async () => {
        try {
            const response = await searchBorrowersWithInfo("sort:card_id order:desc", 1, 1);
            if (response.results.length > 0) {
                const lastId = response.results[0][0].card_id;
                // Extract the numeric part
                const numericPart = parseInt(lastId.replace(/\D/g, ""), 10);
                // Create the next ID with proper padding
                const nextNum = numericPart + 1;
                const nextId = `ID${String(nextNum).padStart(6, "0")}`;
                setNextCardId(nextId);
                // Set the card_id field to the next ID
                setFormData((prev) => ({ ...prev, card_id: nextId }));
            } else {
                const defaultId = "ID000001";
                setNextCardId(defaultId);
                setFormData((prev) => ({ ...prev, card_id: defaultId }));
            }
        } catch (error) {
            console.error("Failed to fetch next card ID:", error);
            const fallbackId = "ID000001";
            setNextCardId(fallbackId);
            setFormData((prev) => ({ ...prev, card_id: fallbackId }));
        }
    };

    const validateForm = () => {
        const newErrors: Record<string, string> = {};

        if (!formData.bname.trim()) {
            newErrors.bname = "Full name is required";
        }

        if (!formData.ssn.trim()) {
            newErrors.ssn = "SSN is required";
        } else if (!/^\d{3}-\d{2}-\d{4}$|^\d{9}$/.test(formData.ssn.trim())) {
            newErrors.ssn = "SSN must be in format XXX-XX-XXXX or 9 digits";
        }

        if (!formData.address.trim()) {
            newErrors.address = "Address is required";
        }

        // Phone is optional but if provided, should be valid
        if (formData.phone.trim() && !/^\d{3}-\d{3}-\d{4}$|^\d{10}$/.test(formData.phone.trim())) {
            newErrors.phone = "Phone must be in format XXX-XXX-XXXX or 10 digits";
        }

        // Card ID is optional but if provided, should match the format
        if (formData.card_id.trim() && !/^ID\d{6}$/.test(formData.card_id.trim())) {
            newErrors.card_id = "Card ID must be in format ID followed by 6 digits";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));

        // Clear error for this field when user starts typing
        if (errors[name]) {
            setErrors((prev) => ({
                ...prev,
                [name]: "",
            }));
        }
    };
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setIsSubmitting(true);
        setApiError(""); // Clear any previous API error

        try {
            // Format SSN to remove dashes if present
            const formattedSSN = formData.ssn.replace(/-/g, "");

            const response = await createBorrower(
                formattedSSN,
                formData.bname,
                formData.address,
                formData.phone,
                formData.card_id.trim() || undefined
            );

            onCreated({
                card_id: response.card_id,
                name: response.name,
            });

            // Reset form
            setFormData({
                bname: "",
                ssn: "",
                address: "",
                phone: "",
                card_id: "",
            });

            onClose();
        } catch (error) {
            let errorMessage = "An error occurred while creating the borrower";

            if (error instanceof Error) {
                // Check if it's an ApiError with status
                const apiError = error as unknown as ApiError;
                if (apiError.status === 400) {
                    // For 400 errors, show the specific error message
                    errorMessage = apiError.message;
                } else if (apiError.status === 500) {
                    // For 500 errors, show a generic message
                    errorMessage = "A server error occurred";
                } else {
                    // For other errors, use the error message
                    errorMessage = error.message;
                }
            }

            setApiError(errorMessage);
        } finally {
            setIsSubmitting(false);
        }
    };
    const handleClose = () => {
        // Reset form data and errors when closing
        setFormData({
            bname: "",
            ssn: "",
            address: "",
            phone: "",
            card_id: "",
        });
        setErrors({});
        setApiError("");
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-md">
                <form onSubmit={handleSubmit}>
                    {" "}
                    <DialogHeader>
                        <DialogTitle>Add New Borrower</DialogTitle>
                        <DialogDescription>
                            Enter the borrower's information to create a new library card.
                        </DialogDescription>
                    </DialogHeader>
                    {apiError && (
                        <div className="bg-destructive/10 border border-destructive px-4 py-2 rounded-md">
                            <p className="text-destructive text-sm font-medium">{apiError}</p>
                        </div>
                    )}
                    <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="bname" className="text-right">
                                Full Name
                            </Label>
                            <Input
                                id="bname"
                                name="bname"
                                className="col-span-3"
                                value={formData.bname}
                                onChange={handleChange}
                            />
                            {errors.bname && (
                                <p className="col-start-2 col-span-3 text-destructive text-sm">{errors.bname}</p>
                            )}
                        </div>

                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="ssn" className="text-right">
                                SSN
                            </Label>
                            <Input
                                id="ssn"
                                name="ssn"
                                className="col-span-3"
                                placeholder="XXX-XX-XXXX"
                                value={formData.ssn}
                                onChange={handleChange}
                            />
                            {errors.ssn && (
                                <p className="col-start-2 col-span-3 text-destructive text-sm">{errors.ssn}</p>
                            )}
                        </div>

                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="address" className="text-right">
                                Address
                            </Label>
                            <Input
                                id="address"
                                name="address"
                                className="col-span-3"
                                value={formData.address}
                                onChange={handleChange}
                            />
                            {errors.address && (
                                <p className="col-start-2 col-span-3 text-destructive text-sm">{errors.address}</p>
                            )}
                        </div>

                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="phone" className="text-right">
                                Phone
                            </Label>
                            <Input
                                id="phone"
                                name="phone"
                                className="col-span-3"
                                placeholder="XXX-XXX-XXXX (Optional)"
                                value={formData.phone}
                                onChange={handleChange}
                            />
                            {errors.phone && (
                                <p className="col-start-2 col-span-3 text-destructive text-sm">{errors.phone}</p>
                            )}
                        </div>

                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="card_id" className="text-right">
                                Card ID
                            </Label>
                            <Input
                                id="card_id"
                                name="card_id"
                                className="col-span-3"
                                placeholder={nextCardId ? `${nextCardId} (Optional)` : "Optional"}
                                value={formData.card_id}
                                onChange={handleChange}
                            />
                            {errors.card_id && (
                                <p className="col-start-2 col-span-3 text-destructive text-sm">{errors.card_id}</p>
                            )}
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={handleClose}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Creating..." : "Create Borrower"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
