import { useEffect, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Mail, ShieldCheck } from "lucide-react";

import { Logo } from "@/components/layout/Logo";
import { Alert, Input } from "@/components/ui";
import { authApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

const ERROR_KEYS: Record<string, string> = {
  github_rejected: "auth.errorRejected",
  github_unavailable: "auth.errorUnavailable",
  invalid_state: "auth.errorInvalidState",
};

function GitHubMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M12 .5A11.5 11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.55v-2.1c-3.2.7-3.88-1.4-3.88-1.4-.52-1.34-1.28-1.7-1.28-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.2 1.77 1.2 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.3-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .96-.3 3.15 1.18a10.9 10.9 0 0 1 5.74 0c2.18-1.48 3.14-1.18 3.14-1.18.63 1.59.23 2.76.12 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.69 5.4-5.25 5.69.41.36.78 1.06.78 2.13v3.16c0 .3.2.66.8.55A11.5 11.5 0 0 0 23.5 12A11.5 11.5 0 0 0 12 .5Z" />
    </svg>
  );
}

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const { language } = useUiStore();
  const { user, loginDev, loginWithGithub } = useAuthStore();
  const { data: status } = useQuery({ queryKey: ["auth", "status"], queryFn: authApi.status });
  const [username, setUsername] = useState("");
  const [busy, setBusy] = useState<"github" | "dev" | "admin" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDemo, setShowDemo] = useState(false);

  const redirectTo = (location.state as { from?: string } | null)?.from ?? "/dashboard";

  useEffect(() => {
    document.documentElement.dataset.theme = "night";
    return () => {
      delete document.documentElement.dataset.theme;
    };
  }, []);

  useEffect(() => {
    if (user) navigate(redirectTo, { replace: true });
  }, [user, navigate, redirectTo]);

  const oauthError = params.get("error");

  const handleGithub = async () => {
    setBusy("github");
    setError(null);
    try {
      await loginWithGithub();
    } catch {
      setError(t("auth.errorUnavailable"));
      setBusy(null);
    }
  };

  const handleDev = async (asAdmin: boolean) => {
    setBusy(asAdmin ? "admin" : "dev");
    setError(null);
    try {
      await loginDev(username.trim() || undefined, asAdmin);
      navigate(redirectTo, { replace: true });
    } catch {
      setError(t("auth.errorGeneric"));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="relative isolate min-h-[calc(100vh-4rem)] overflow-hidden bg-[#0f0f12] px-4 py-14 sm:py-20">
      <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <div className="animate-glow absolute left-1/2 top-[-10%] size-[520px] -translate-x-1/2 rounded-full bg-[#6d28d9] opacity-35 blur-[150px]" />
        <div className="absolute bottom-0 right-1/4 size-[320px] rounded-full bg-[#db2777] opacity-20 blur-[130px]" />
      </div>

      <div className="mx-auto w-full max-w-[420px]">
        <div className="flex justify-center">
          <Logo light />
        </div>

        <h1 className="font-display mt-8 text-center text-[28px] font-extrabold leading-tight tracking-[-0.03em] text-white sm:text-[32px]">
          {t("auth.heroTitle")}
        </h1>
        <p className="mx-auto mt-3 max-w-[340px] text-center text-sm leading-relaxed text-[#a1a1aa]">
          {t("auth.heroSubtitle")}
        </p>

        {oauthError ? (
          <div className="mt-6">
            <Alert tone="error">{t(ERROR_KEYS[oauthError] ?? "auth.errorGeneric")}</Alert>
          </div>
        ) : null}
        {error ? (
          <div className="mt-6">
            <Alert tone="error">{error}</Alert>
          </div>
        ) : null}

        <div className="mt-8 space-y-3">
          <button
            type="button"
            onClick={() => void handleGithub()}
            disabled={busy !== null}
            className="inline-flex h-12 w-full items-center justify-center gap-2.5 rounded-xl bg-white text-[15px] font-semibold text-[#0f0f12] transition hover:bg-[#e8e8ec] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {busy === "github" ? (
              <span className="size-4 animate-spin rounded-full border-2 border-[#0f0f12] border-t-transparent" aria-hidden="true" />
            ) : (
              <GitHubMark className="size-5" />
            )}
            {t("auth.github")}
          </button>

          <button
            type="button"
            onClick={() => setShowDemo((open) => !open)}
            aria-expanded={showDemo}
            className="inline-flex h-12 w-full items-center justify-center gap-2.5 rounded-xl border border-[#2c2c35] bg-[#1c1c22] text-[15px] font-semibold text-white transition hover:border-[#3d3d49] hover:bg-[#24242b]"
          >
            <Mail className="size-5" aria-hidden="true" />
            {t("auth.devTitle")}
          </button>
        </div>

        {status && !status.github_oauth_enabled ? (
          <p className="mt-3 text-center text-[11px] leading-relaxed text-[#6f6f7d]">
            {language === "fr"
              ? "GitHub OAuth n'est pas configuré ici : utilisez la connexion de démonstration."
              : "GitHub OAuth is not configured here: use the demo sign-in."}
          </p>
        ) : null}

        {showDemo ? (
          <div className="mt-4 rounded-xl border border-[#26262e] bg-[#141419] p-4">
            <p className="text-xs leading-relaxed text-[#8f8f9c]">{t("auth.devSubtitle")}</p>
            <label className="mt-3 block text-xs font-medium text-[#c9c9d2]" htmlFor="login-username">
              {t("auth.username")} <span className="font-normal text-[#6f6f7d]">({t("common.optional")})</span>
            </label>
            <Input
              id="login-username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder={t("auth.usernamePlaceholder")}
              autoComplete="username"
              className="mt-1.5"
            />
            <button
              type="button"
              onClick={() => void handleDev(false)}
              disabled={busy !== null}
              className="mt-3 inline-flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-white text-sm font-semibold text-[#0f0f12] transition hover:bg-[#e8e8ec] disabled:opacity-70"
            >
              {busy === "dev" ? (
                <span className="size-4 animate-spin rounded-full border-2 border-[#0f0f12] border-t-transparent" aria-hidden="true" />
              ) : null}
              {t("auth.login")}
            </button>
            <button
              type="button"
              onClick={() => void handleDev(true)}
              disabled={busy !== null}
              className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-[#8f8f9c] transition hover:text-white disabled:opacity-70"
            >
              <ShieldCheck className="size-3.5" aria-hidden="true" />
              {t("auth.loginAdmin")}
            </button>
            <p className="mt-2 text-center text-[11px] text-[#6f6f7d]">{t("auth.usernameHelp")}</p>
          </div>
        ) : null}

        <p className="mt-6 text-center text-[11px] leading-relaxed text-[#6f6f7d]">{t("landing2.terms")}</p>

        <p className="mt-6 text-center text-sm text-[#a1a1aa]">
          {t("landing2.already")}{" "}
          <button
            type="button"
            onClick={() => setShowDemo(true)}
            className="inline-flex items-center gap-1 font-medium text-white underline underline-offset-4 hover:text-[#c4b5fd]"
          >
            {t("nav.login")}
            <ArrowRight className="size-3.5" aria-hidden="true" />
          </button>
        </p>
      </div>
    </div>
  );
}
