import { create } from "zustand";

import { authApi } from "@/services/api";
import type { User } from "@/types/api";

type AuthStatus = "idle" | "loading" | "authenticated" | "anonymous";

interface AuthState {
  user: User | null;
  status: AuthStatus;
  error: string | null;
  hydrate: () => Promise<void>;
  loginDev: (username?: string, asAdmin?: boolean) => Promise<User>;
  loginWithGithub: () => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: "idle",
  error: null,

  hydrate: async () => {
    set({ status: "loading", error: null });
    try {
      const user = await authApi.me();
      set({ user, status: "authenticated" });
    } catch {
      set({ user: null, status: "anonymous" });
    }
  },

  loginDev: async (username, asAdmin = false) => {
    set({ error: null });
    const user = await authApi.devLogin(username, asAdmin);
    set({ user, status: "authenticated" });
    return user;
  },

  loginWithGithub: async () => {
    const { authorization_url } = await authApi.githubUrl();
    window.location.assign(authorization_url);
  },

  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      set({ user: null, status: "anonymous" });
    }
  },

  setUser: (user) => set({ user, status: user ? "authenticated" : "anonymous" }),
}));
