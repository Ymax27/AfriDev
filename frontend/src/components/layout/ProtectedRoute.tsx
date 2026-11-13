import { Navigate, Outlet, useLocation } from "react-router-dom";

import { Spinner } from "@/components/ui";
import { useAuthStore } from "@/stores/auth-store";

export function ProtectedRoute({ adminOnly = false }: { adminOnly?: boolean }) {
  const { user, status } = useAuthStore();
  const location = useLocation();

  if (status === "idle" || status === "loading") return <Spinner label="…" />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (adminOnly && !user.is_admin) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
