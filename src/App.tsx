import React, { Suspense, lazy, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Checkout = lazy(() => import("./pages/Checkout"));
const Borrowers = lazy(() => import("./pages/Borrowers"));
const Loans = lazy(() => import("./pages/Loans"));
const Test = lazy(() => import("./pages/Test"));

const App: React.FC = () => {
    useEffect(() => {
        const updateDarkMode = () => {
            if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
                document.body.classList.add("dark");
            } else {
                document.body.classList.remove("dark");
            }
        };
        updateDarkMode();
        const mq = window.matchMedia("(prefers-color-scheme: dark)");
        mq.addEventListener("change", updateDarkMode);
        return () => mq.removeEventListener("change", updateDarkMode);
    }, []);

    return (
        <AuthProvider>
            <Router>
                <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
                    <Routes>
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route
                            path="/checkout"
                            element={
                                <ProtectedRoute>
                                    <Checkout />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/borrowers"
                            element={
                                <ProtectedRoute>
                                    <Borrowers />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/loans"
                            element={
                                <ProtectedRoute>
                                    <Loans />
                                </ProtectedRoute>
                            }
                        />
                        <Route path="/test" element={<Test />} />
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="*" element={<Navigate to="/dashboard" replace />} />
                    </Routes>
                </Suspense>
            </Router>
        </AuthProvider>
    );
};

export default App;
