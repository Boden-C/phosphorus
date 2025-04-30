import React, { Suspense, lazy, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

const Dashboard = lazy(() => import("./pages/Dashboard"));

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
        const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
        mediaQuery.addEventListener("change", updateDarkMode);
        return () => mediaQuery.removeEventListener("change", updateDarkMode);
    }, []);

    return (
        <Router>
            <Suspense fallback={<div>Loading...</div>}>
                <Routes>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
            </Suspense>
        </Router>
    );
};

export default App;
