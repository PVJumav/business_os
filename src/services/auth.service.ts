import { api } from "./api";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterUserPayload {
  email: string;
  password: string;
  full_name: string;
  username?: string;
  role?: string;
}

export interface GoogleLoginPayload {
  credential: string;
}

export interface GithubLoginPayload {
  code: string;
  redirect_uri: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number | string;
  email: string;
  full_name: string;
  role: string;
  is_active?: boolean;
  roles?: string[];
  permissions?: string[];
}

export const authService = {
  async register(payload: RegisterUserPayload): Promise<User> {
    return api.post<User>("/api/auth/register", payload);
  },

  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const tokens = await api.post<AuthTokens>("/api/auth/login", credentials);
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", tokens.access_token);
    }
    return tokens;
  },

  async loginWithGoogle(payload: GoogleLoginPayload): Promise<AuthTokens> {
    const tokens = await api.post<AuthTokens>("/api/auth/google", payload);
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", tokens.access_token);
    }
    return tokens;
  },

  async loginWithGithub(payload: GithubLoginPayload): Promise<AuthTokens> {
    const tokens = await api.post<AuthTokens>("/api/auth/github", payload);
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", tokens.access_token);
    }
    return tokens;
  },

  async logout(): Promise<void> {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
  },

  async getCurrentUser(): Promise<User> {
    return api.get<User>("/api/auth/me");
  },

  isAuthenticated(): boolean {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem("access_token");
  },
};
