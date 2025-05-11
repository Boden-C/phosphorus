import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { BookOpen, BookmarkCheck, Users, Calendar, LogIn, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { LoginModal } from "@/components/LoginModal";

export interface SidebarProps {
    /**
     * Optional class name to apply to the sidebar container
     */
    className?: string;
}

/**
 * Sidebar component for application navigation
 */
export const Sidebar: React.FC<SidebarProps> = ({ className }) => {
    const { isAuthenticated, user, logout, isLoading } = useAuth();
    const [showLoginModal, setShowLoginModal] = useState(false);

    const handleAuthAction = () => {
        if (isAuthenticated) {
            // Sign out
            logout();
        } else {
            // Show login modal
            setShowLoginModal(true);
        }
    };

    return (
        <>
            <aside className={cn("w-64 border-r flex flex-col p-6 h-screen", className)}>
                <h1 className="text-2xl font-bold mb-8">Phosphorus Library</h1>
                <nav className="flex flex-col gap-4 flex-grow">
                    <NavLink
                        to="/dashboard"
                        className={({ isActive }) =>
                            cn("flex items-center gap-2", isActive ? "text-primary" : "text-muted-foreground")
                        }
                    >
                        {({ isActive }) => (
                            <Button variant={isActive ? "secondary" : "ghost"} className="w-full justify-start">
                                <BookOpen size={18} className="mr-2" />
                                Dashboard
                            </Button>
                        )}
                    </NavLink>

                    <NavLink
                        to="/checkout"
                        className={({ isActive }) =>
                            cn(
                                "flex items-center gap-2",
                                isActive && isAuthenticated ? "text-primary" : "text-muted-foreground"
                            )
                        }
                    >
                        {({ isActive }) => (
                            <Button
                                variant={isActive && isAuthenticated ? "secondary" : "ghost"}
                                className="w-full justify-start"
                                disabled={!isAuthenticated}
                            >
                                <BookmarkCheck size={18} className="mr-2" />
                                Checkout
                            </Button>
                        )}
                    </NavLink>

                    <NavLink
                        to="/borrowers"
                        className={({ isActive }) =>
                            cn(
                                "flex items-center gap-2",
                                isActive && isAuthenticated ? "text-primary" : "text-muted-foreground"
                            )
                        }
                    >
                        {({ isActive }) => (
                            <Button
                                variant={isActive && isAuthenticated ? "secondary" : "ghost"}
                                className="w-full justify-start"
                                disabled={!isAuthenticated}
                            >
                                <Users size={18} className="mr-2" />
                                Borrowers
                            </Button>
                        )}
                    </NavLink>

                    <NavLink
                        to="/loans"
                        className={({ isActive }) =>
                            cn(
                                "flex items-center gap-2",
                                isActive && isAuthenticated ? "text-primary" : "text-muted-foreground"
                            )
                        }
                    >
                        {({ isActive }) => (
                            <Button
                                variant={isActive && isAuthenticated ? "secondary" : "ghost"}
                                className="w-full justify-start"
                                disabled={!isAuthenticated}
                            >
                                <Calendar size={18} className="mr-2" />
                                Loans
                            </Button>
                        )}
                    </NavLink>
                </nav>

                <div className="mt-auto pt-4 border-t">
                    {isAuthenticated && user && (
                        <div className="mb-2 text-sm text-muted-foreground flex items-center">
                            <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                            <span className="font-medium">{user.username}</span>
                        </div>
                    )}
                    <Button
                        variant="outline"
                        className="w-full justify-start"
                        onClick={handleAuthAction}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            "Loading..."
                        ) : isAuthenticated ? (
                            <>
                                <LogOut size={18} className="mr-2" />
                                Sign Out
                            </>
                        ) : (
                            <>
                                <LogIn size={18} className="mr-2" />
                                Sign In
                            </>
                        )}
                    </Button>
                </div>
            </aside>

            <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
        </>
    );
};
