// src/App.tsx
import React, { Suspense, lazy, useEffect } from "react";    // ← add useEffect here
import {
  HashRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";

const LoginPage     = lazy(() => import("./pages/LoginPage"));
const Dashboard     = lazy(() => import("./pages/Dashboard"));
const BorrowersPage = lazy(() => import("./pages/BorrowersPage"));

const App: React.FC = () => {
  useEffect(() => {
    const updateDarkMode = () => {
      if (
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches
      ) {
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
    <Router>
      <Suspense fallback={<div>Loading…</div>}>
        <Routes>
          {/* public */}
          <Route path="/login" element={<LoginPage />} />

          {/* everything below requires auth */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/members" element={<BorrowersPage />} />
          </Route>

          {/* catch-all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </Router>
  );
};

export default App;
