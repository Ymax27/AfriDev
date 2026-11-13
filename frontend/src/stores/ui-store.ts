import { create } from "zustand";
import { persist } from "zustand/middleware";

type Language = "fr" | "en";

interface UiState {
  language: Language;
  lightweightMode: boolean;
  sidebarOpen: boolean;
  setLanguage: (language: Language) => void;
  setLightweightMode: (enabled: boolean) => void;
  toggleSidebar: () => void;
  closeSidebar: () => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      language: "fr",
      lightweightMode: false,
      sidebarOpen: false,
      setLanguage: (language) => set({ language }),
      setLightweightMode: (lightweightMode) => set({ lightweightMode }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      closeSidebar: () => set({ sidebarOpen: false }),
    }),
    {
      name: "afridev-ui",
      partialize: (state) => ({ language: state.language, lightweightMode: state.lightweightMode }),
    },
  ),
);
