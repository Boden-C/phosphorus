import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, SendIcon, X, ExternalLink, Code } from "lucide-react";
import { sendChatMessage } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface ChatMessage {
    role: "user" | "assistant" | "system" | "tool";
    content: string;
    name?: string; // For tool messages
    tool_call_id?: string;
    parameters?: Record<string, any>; // Tool parameters
}

interface ChatPopupProps {
    isOpen: boolean;
    onClose: () => void;
}

/**
 * AI Chat popup component that provides an interface for users to interact with
 * the library's AI assistant
 */
export const ChatPopup: React.FC<ChatPopupProps> = ({ isOpen, onClose }) => {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showJsonDialog, setShowJsonDialog] = useState(false);
    const [currentToolResult, setCurrentToolResult] = useState<string>("");
    const [currentToolName, setCurrentToolName] = useState<string>("");
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Focus input field when popup opens
    useEffect(() => {
        if (isOpen && inputRef.current) {
            setTimeout(() => {
                inputRef.current?.focus();
            }, 100);
        }
    }, [isOpen]);

    // Scroll to bottom when messages update
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);
    const handleSendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: ChatMessage = {
            role: "user",
            content: input,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await sendChatMessage(userMessage.content, messages.length > 0 ? messages : undefined);

            // Validate response structure before updating messages
            if (response && Array.isArray(response.history)) {
                setMessages(response.history);
            } else {
                throw new Error("Invalid response format from server");
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "Unknown error";
            console.error("Chat error:", error);

            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: `Sorry, I encountered a technical issue: ${errorMessage}. Please try again later.`,
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed bottom-4 right-4 z-50">
            {" "}
            <Card className="w-[350px] h-[500px] flex flex-col shadow-lg">
                <CardHeader className="py-3 px-4 flex flex-row items-center justify-between border-b">
                    <h3 className="text-sm font-medium">Library Assistant</h3>
                    <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
                        <X size={16} />
                    </Button>
                </CardHeader>
                <CardContent className="p-4 overflow-y-auto flex-grow">
                    {messages.length === 0 ? (
                        <div className="text-center text-muted-foreground py-8">
                            <p>Hello! I'm your library assistant.</p>
                            <p className="mt-2">Ask me anything about books or our library.</p>
                        </div>
                    ) : (
                        messages.map((message, index) => {
                            if (message.role === "tool") {
                                // Handle tool message
                                let displayName = "results";
                                let path = "/books";
                                let actionText = "Used search";

                                // Set appropriate path and text based on tool name
                                if (message.name?.includes("book")) {
                                    displayName = "Book";
                                    path = "/books";
                                } else if (message.name?.includes("borrower")) {
                                    displayName = "Borrower";
                                    path = "/borrowers";
                                } else if (message.name?.includes("loan")) {
                                    displayName = "Loans";
                                    path = "/loans";
                                } else if (message.name?.includes("fine")) {
                                    displayName = "Fines";
                                    path = "/fines";
                                    actionText = "Used fines tool";
                                } else if (message.name?.includes("checkout")) {
                                    displayName = "Loans";
                                    path = "/loans";
                                    actionText = "Checked out book";
                                } else if (message.name?.includes("checkin")) {
                                    displayName = "Loans";
                                    path = "/loans";
                                    actionText = "Returned book";
                                } // Create parameter display text if parameters exist
                                const hasParameters = message.parameters && Object.keys(message.parameters).length > 0;
                                let paramText = "";
                                if (hasParameters && message.parameters) {
                                    const params = Object.entries(message.parameters)
                                        .map(
                                            ([key, val]) =>
                                                `${key}: ${typeof val === "string" ? val : JSON.stringify(val)}`
                                        )
                                        .join(", ");
                                    paramText = `(${params})`;
                                }

                                const handleViewJson = () => {
                                    setCurrentToolName(message.name || "Tool result");
                                    setCurrentToolResult(message.content || "{}");
                                    setShowJsonDialog(true);
                                };

                                return (
                                    <div key={index} className="mb-2 text-left">
                                        <div className="flex flex-col">
                                            <div className="flex items-center">
                                                <div className="text-xs text-muted-foreground italic mr-1">
                                                    {actionText} {paramText}
                                                </div>
                                                <a href={path} className="flex items-center text-xs text-primary">
                                                    <span>view {displayName}</span>
                                                    <ExternalLink size={12} className="ml-1" />
                                                </a>
                                            </div>
                                            <button
                                                onClick={handleViewJson}
                                                className="flex items-center text-xs text-muted-foreground hover:text-primary mt-1"
                                            >
                                                <Code size={12} className="mr-1" />
                                                View result data
                                            </button>
                                        </div>
                                    </div>
                                );
                            } else if (message.role !== "system") {
                                // Regular user or assistant message
                                return (
                                    <div
                                        key={index}
                                        className={`mb-4 ${message.role === "user" ? "text-right" : "text-left"}`}
                                    >
                                        <div
                                            className={`inline-block px-4 py-2 rounded-lg max-w-[85%] ${
                                                message.role === "user"
                                                    ? "bg-primary text-primary-foreground"
                                                    : "bg-muted text-muted-foreground"
                                            }`}
                                        >
                                            {message.content}
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        })
                    )}
                    {isLoading && (
                        <div className="flex justify-start mb-4">
                            <div className="bg-muted p-3 rounded-lg">
                                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </CardContent>
                <CardFooter className="border-t p-3">
                    <div className="flex w-full items-center space-x-2">
                        <Input
                            ref={inputRef}
                            placeholder="Type your message..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={isLoading}
                            className="flex-grow"
                        />
                        <Button size="icon" onClick={handleSendMessage} disabled={isLoading || !input.trim()}>
                            <SendIcon className="h-4 w-4" />
                        </Button>
                    </div>
                </CardFooter>{" "}
            </Card>
            {/* JSON Result Dialog */}
            <Dialog open={showJsonDialog} onOpenChange={setShowJsonDialog}>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
                    <DialogHeader>
                        <DialogTitle>{currentToolName}</DialogTitle>
                    </DialogHeader>
                    <div className="bg-muted rounded-md p-4 overflow-auto max-h-[60vh]">
                        <pre className="text-xs whitespace-pre-wrap">
                            {(() => {
                                try {
                                    return JSON.stringify(JSON.parse(currentToolResult), null, 2);
                                } catch (e) {
                                    return currentToolResult;
                                }
                            })()}
                        </pre>
                    </div>
                    <div className="flex justify-end">
                        <Button variant="outline" onClick={() => setShowJsonDialog(false)}>
                            Close
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};
