import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
  roles?: string[];  // ako je zadato, korisnik mora imati bar jednu od uloga
}

export function ProtectedRoute({ children, roles }: Props) {
  const { isAuthenticated, hasRole, loading } = useAuth();

  if (loading) {
    return <p style={{ padding: "32px" }}>Učitavanje...</p>;
  }

  // nije prijavljen → na login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // prijavljen ali nema potrebnu ulogu → na početnu
  if (roles && !hasRole(...roles)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}