"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authService, User, LoginCredentials, RegisterUserPayload } from "@/services/auth.service";

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  loginWithGoogle: (credential: string) => Promise<boolean>;
  register: (payload: RegisterUserPayload) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    if (!authService.isAuthenticated()) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const me = await authService.getCurrentUser();
      setUser(me);
    } catch {
      await authService.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    refreshUser();
  }, [refreshUser]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.login(credentials);
      const me = await authService.getCurrentUser();
      setUser(me);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginWithGoogle = useCallback(async (credential: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.loginWithGoogle({ credential });
      const me = await authService.getCurrentUser();
      setUser(me);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-in failed");
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (payload: RegisterUserPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.register(payload);
      await authService.login({ email: payload.email, password: payload.password });
      const me = await authService.getCurrentUser();
      setUser(me);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      isLoading,
      error,
      isAuthenticated: Boolean(user),
      login,
      loginWithGoogle,
      register,
      logout,
      refreshUser,
      clearError,
    }),
    [clearError, error, isLoading, login, loginWithGoogle, logout, refreshUser, register, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthStore(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthStore must be used within AuthProvider");
  }
  return context;
}
