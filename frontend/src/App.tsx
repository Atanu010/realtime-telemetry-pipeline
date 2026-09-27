import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import AuthGate from "@/pages/AuthGate";
import { getStoredToken } from "@/lib/api";
import { Toaster } from "@/components/ui/sonner";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => !!getStoredToken());

  useEffect(() => {
    const handleAuthChange = () => {
      setIsAuthenticated(!!getStoredToken());
    };

    window.addEventListener("operator-auth-changed", handleAuthChange);
    return () => window.removeEventListener("operator-auth-changed", handleAuthChange);
  }, []);

  if (!isAuthenticated) {
    return (
      <>
        <Toaster richColors />
        <AuthGate onAuthenticated={() => setIsAuthenticated(true)} />
      </>
    );
  }

  return (
    <>
      <Toaster richColors />
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </>
  );
}
