import { useTranslation } from "react-i18next";
import { Languages } from "lucide-react";

import { useUiStore } from "@/stores/ui-store";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const { language, setLanguage } = useUiStore();

  const change = (next: "fr" | "en") => {
    setLanguage(next);
    void i18n.changeLanguage(next);
  };

  return (
    <div className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white p-0.5" role="group" aria-label={t("settings.language")}>
      <Languages className="ml-1.5 size-3.5 text-muted" aria-hidden="true" />
      {(["fr", "en"] as const).map((code) => (
        <button
          key={code}
          type="button"
          onClick={() => change(code)}
          aria-pressed={language === code}
          className={
            language === code
              ? "rounded-md bg-primary-700 px-2 py-0.5 text-xs font-semibold text-white"
              : "rounded-md px-2 py-0.5 text-xs font-medium text-muted hover:text-primary-700"
          }
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
