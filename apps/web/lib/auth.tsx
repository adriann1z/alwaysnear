"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";

import { api, setAuthTokenGetter, setUnauthorizedHandler } from "@/lib/api";
import type { User } from "@/lib/types";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  loading: boolean;
  error: string | null;
  login: (payload: { email: string; password: string }) => Promise<void>;
  signup: (payload: {
    email: string;
    password: string;
    display_name: string;
    phone?: string | null;
    timezone?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const TOKEN_KEY = "always-near-token";

// Stage 10 choice: JWTs are kept in sessionStorage so they persist only for the
// current browser tab/session and are cleared by the auth expiry handler.
const getStoredToken = () =>
  typeof window === "undefined" ? null : window.sessionStorage.getItem(TOKEN_KEY);
const setStoredToken = (token: string) => window.sessionStorage.setItem(TOKEN_KEY, token);
const clearStoredToken = () => window.sessionStorage.removeItem(TOKEN_KEY);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    setAuthTokenGetter(getStoredToken);
    setUnauthorizedHandler(() => {
      clearStoredToken();
      setToken(null);
      setUser(null);
      router.replace("/login");
    });
    const stored = getStoredToken();
    setToken(stored);
    if (!stored) {
      setIsLoading(false);
    }
  }, [router]);

  const refreshUser = useCallback(async () => {
    const stored = getStoredToken();
    if (!stored) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      setError(null);
      const me = await api.auth.me();
      setUser(me.user);
      setToken(stored);
    } catch (refreshError) {
      clearStoredToken();
      setToken(null);
      setUser(null);
      setError(refreshError instanceof Error ? refreshError.message : "Session expired");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser, token]);

  const storeToken = useCallback(async (nextToken: string) => {
    setStoredToken(nextToken);
    setToken(nextToken);
  }, []);

  const login = useCallback(
    async (payload: { email: string; password: string }) => {
      setError(null);
      const response = await api.auth.login(payload);
      await storeToken(response.access_token);
      await refreshUser();
    },
    [refreshUser, storeToken]
  );

  const signup = useCallback(
    async (payload: {
      email: string;
      password: string;
      display_name: string;
      phone?: string | null;
      timezone?: string;
    }) => {
      setError(null);
      const response = await api.auth.signup(payload);
      await storeToken(response.access_token);
      await refreshUser();
    },
    [refreshUser, storeToken]
  );

  const logout = useCallback(async () => {
    try {
      if (getStoredToken()) {
        await api.auth.logout();
      }
    } finally {
      clearStoredToken();
      setToken(null);
      setUser(null);
      router.push("/login");
    }
  }, [router]);

  const value = useMemo(
    () => ({
      token,
      user,
      isLoading,
      loading: isLoading,
      error,
      login,
      signup,
      logout,
      refreshUser,
      refreshMe: refreshUser
    }),
    [error, isLoading, login, logout, refreshUser, signup, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) {
      router.replace("/login");
    }
  }, [isLoading, router, token]);

  if (isLoading) {
    return <div className="p-8 text-sm text-ink/70">Loading...</div>;
  }

  if (!token) {
    return null;
  }

  return <>{children}</>;
}

export function RequireAdmin({ children }: { children: ReactNode }) {
  const { token, user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && (!token || user?.role !== "admin")) {
      router.replace("/login");
    }
  }, [isLoading, router, token, user?.role]);

  if (isLoading) {
    return <div className="p-8 text-sm text-ink/70">Loading...</div>;
  }

  if (!token || user?.role !== "admin") {
    return null;
  }

  return <>{children}</>;
}
