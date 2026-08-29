import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { authApi } from "../api/client";
import type { TokenPayload } from "../types";

interface AuthState {
  userId: number | null;
  roles: string[];
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

// dekodira JWT payload bez verifikacije (samo za čitanje uloga na klijentu)
function decodeToken(token: string): TokenPayload | null {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [userId, setUserId] = useState<number | null>(null);
  const [roles, setRoles] = useState<string[]>([]);

  // pri učitavanju aplikacije, pročitaj token iz localStorage
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      const payload = decodeToken(token);
      if (payload) {
        setUserId(Number(payload.sub));
        setRoles(payload.roles);
      }
    }
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await authApi.post("/auth/login", { email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const payload = decodeToken(data.access_token);
    if (payload) {
      setUserId(Number(payload.sub));
      setRoles(payload.roles);
    }
  };

  const logout = () => {
    const refreshToken = localStorage.getItem("refresh_token");
    // best-effort logout na serveru (blacklist refresh token)
    if (refreshToken) {
      authApi.post("/auth/logout", { refresh_token: refreshToken }).catch(() => {});
    }
    localStorage.clear();
    setUserId(null);
    setRoles([]);
  };

  const hasRole = (...checkRoles: string[]) =>
    checkRoles.some((r) => roles.includes(r));

  return (
    <AuthContext.Provider
      value={{
        userId,
        roles,
        isAuthenticated: userId !== null,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// hook za korišćenje u komponentama
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth mora biti unutar AuthProvider");
  return ctx;
}