"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import type { UserRole } from "@/lib/types";

interface Props {
  role: UserRole;
  children: React.ReactNode;
}

export function ProtectedRoute({ role, children }: Props) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace(`/auth/login?redirect=${encodeURIComponent(window.location.pathname)}`);
      return;
    }
    if (user.role !== role) {
      router.replace(user.role === "recruiter" ? "/recruiter" : "/candidate");
    }
  }, [user, loading, role, router]);

  if (loading || !user || user.role !== role) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return <>{children}</>;
}
