import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import fr from "./locales/fr.json";

function initialLanguage(): "fr" | "en" {
  if (typeof window === "undefined") return "fr";
  try {
    const stored = window.localStorage.getItem("afridev-ui");
    if (stored) {
      const parsed = JSON.parse(stored) as { state?: { language?: string } };
      if (parsed.state?.language === "en") return "en";
    }
  } catch {
    return "fr";
  }
  return "fr";
}

void i18n.use(initReactI18next).init({
  resources: {
    fr: { translation: fr },
    en: { translation: en },
  },
  lng: initialLanguage(),
  fallbackLng: "fr",
  interpolation: { escapeValue: false },
  returnNull: false,
});

i18n.on("languageChanged", (language) => {
  if (typeof document !== "undefined") {
    document.documentElement.lang = language;
  }
});

export default i18n;
