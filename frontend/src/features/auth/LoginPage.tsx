import { useEffect, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { Code2, ShieldCheck } from "lucide-react";

import { Alert, Button, Field, Input } from "@/components/ui";
import { authApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

const ERROR_KEYS: Record<string, string> = {
  github_rejected: "auth.errorRejected",
  github_unavailable: "auth.errorUnavailable",
  invalid_state: "auth.errorInvalidState",
};

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

  const redirectTo = (location.state as { from?: string } | null)?.from ?? "/dashboard";

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
    <div className="mx-auto grid w-full max-w-5xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-2 lg:py-20">
      <section className="hidden flex-col justify-center lg:flex">
        <h1 className="text-3xl font-bold leading-tight text-primary-800">{t("auth.heroTitle")}</h1>
        <p className="mt-3 text-base text-muted">{t("auth.heroSubtitle")}</p>
        <ul className="mt-6 space-y-2 text-sm text-primary-700">
          {[t("landing.pillarShowText"), t("landing.pillarSolveText"), t("landing.pillarProveText")].map((item) => (
            <li key={item} className="flex gap-2">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-accent-600" aria-hidden="true" />
              {item}
            </li>
          ))}
        </ul>
      </section>

      <section className="surface-card p-6 sm:p-8">
        <h2 className="text-xl font-semibold text-primary-800">{t("auth.title")}</h2>
        <p className="mt-1 text-sm text-muted">{t("auth.subtitle")}</p>

        {oauthError ? (
          <div className="mt-4">
            <Alert tone="error">{t(ERROR_KEYS[oauthError] ?? "auth.errorGeneric")}</Alert>
          </div>
        ) : null}
        {error ? (
          <div className="mt-4">
            <Alert tone="error">{error}</Alert>
          </div>
        ) : null}

        <div className="mt-6">
          <Button
            className="w-full"
            size="lg"
            onClick={() => void handleGithub()}
            loading={busy === "github"}
            icon={<Code2 className="size-4" aria-hidden="true" />}
          >
            {t("auth.github")}
          </Button>
          {status && !status.github_oauth_enabled ? (
            <p className="mt-2 text-center text-xs text-muted">
              {language === "fr"
                ? "GitHub OAuth n'est pas configuré : utilisez la connexion de démonstration."
                : "GitHub OAuth is not configured: use the demo sign-in."}
            </p>
          ) : null}
        </div>

        <div className="my-6 flex items-center gap-3 text-xs text-muted">
          <span className="h-px flex-1 bg-slate-200" /> {t("auth.or")} <span className="h-px flex-1 bg-slate-200" />
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
          <h3 className="text-sm font-semibold text-primary-800">{t("auth.devTitle")}</h3>
          <p className="mt-1 text-xs text-muted">{t("auth.devSubtitle")}</p>
          <div className="mt-3 space-y-3">
            <Field label={t("auth.username")} hint={t("common.optional")} htmlFor="login-username">
              <Input
                id="login-username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder={t("auth.usernamePlaceholder")}
                autoComplete="username"
              />
            </Field>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={() => void handleDev(false)} loading={busy === "dev"}>
                {t("auth.login")}
              </Button>
              <Button variant="ghost" onClick={() => void handleDev(true)} loading={busy === "admin"}>
                {t("auth.loginAdmin")}
              </Button>
            </div>
            <p className="text-xs text-muted">{t("auth.usernameHelp")}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
