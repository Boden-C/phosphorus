import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import * as api from "@/lib/api";

interface User {
    username: string;
    is_staff?: boolean;
}

interface AuthContextType {
    isAuthenticated: boolean;
    user: User | null;
    login: (username: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    isLoading: boolean;
    error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Hook for accessing authentication context
 */
export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

/**
 * Provider component for authentication state
 * Manages user sessions and provides login/logout functionality
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // Check authentication status on mount
    useEffect(() => {
        const checkAuthStatus = async () => {
            try {
                setIsLoading(true);
                const userData = await api.getCurrentUser();

                if (userData && userData.username) {
                    setUser({
                        username: userData.username,
                        is_staff: userData.is_staff,
                    });
                    setIsAuthenticated(true);
                }
            } catch (err) {
                setUser(null);
                setIsAuthenticated(false);
            } finally {
                setIsLoading(false);
            }
        };

        checkAuthStatus();
    }, []);

    const login = async (username: string, password: string) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await api.login(username, password);

            if (response && response.username) {
                setUser({
                    username: response.username,
                });
                setIsAuthenticated(true);
            } else {
                throw new Error(response.message || "Login failed");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to login");
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = async () => {
        setIsLoading(true);
        setError(null);

        try {
            await api.logout();
            setUser(null);
            setIsAuthenticated(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to logout");
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const value = {
        isAuthenticated,
        user,
        login,
        logout,
        isLoading,
        error,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
