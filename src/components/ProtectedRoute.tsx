import React, { useEffect, useState } from "react";
import { Outlet, Navigate } from "react-router-dom";

export default function ProtectedRoute() {
  const [status, setStatus] = useState<"loading"|"ok"|"fail">("loading");

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then(res => {
        setStatus(res.ok ? "ok" : "fail");
      })
      .catch(() => setStatus("fail"));
  }, []);

  if (status === "loading") {
    return <div className="p-8">Checking authentication…</div>;
  }
  if (status === "fail") {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
