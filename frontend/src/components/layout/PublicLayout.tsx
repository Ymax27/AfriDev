import { Link, NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { Logo } from "@/components/layout/Logo";
import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";

const PUBLIC_LINKS = [
  { to: "/knowledge", key: "nav.knowledge" },
  { to: "/field-reports", key: "landing.statsReports" },
  { to: "/countries", key: "nav.countries" },
  { to: "/leaderboard", key: "nav.leaderboard" },
  { to: "/missions", key: "nav.missions" },
  { to: "/api-directory", key: "nav.apis" },
] as const;

export function PublicLayout() {
  const { t } = useTranslation();
  const { user } = useAuthStore();

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Logo />
          <nav className="hidden items-center gap-1 md:flex" aria-label="primary">
            {PUBLIC_LINKS.map(({ to, key }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "rounded-lg px-3 py-2 text-sm font-medium",
                    isActive ? "bg-primary-50 text-primary-700" : "text-muted hover:text-primary-700",
                  )
                }
              >
                {t(key)}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            {user ? (
              <Link to="/dashboard">
                <Button size="sm">{t("nav.dashboard")}</Button>
              </Link>
            ) : (
              <Link to="/login">
                <Button size="sm">{t("nav.login")}</Button>
              </Link>
            )}
          </div>
        </div>
      </header>

      <main id="main-content" className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-4">
          <div>
            <Logo />
            <p className="mt-3 text-sm text-muted">{t("footer.slogan")}</p>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-primary-800">{t("footer.community")}</h2>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              <li><Link to="/knowledge" className="hover:text-primary-700">{t("nav.knowledge")}</Link></li>
              <li><Link to="/field-reports" className="hover:text-primary-700">{t("landing.statsReports")}</Link></li>
              <li><Link to="/countries" className="hover:text-primary-700">{t("nav.countries")}</Link></li>
            </ul>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-primary-800">{t("footer.product")}</h2>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              <li><Link to="/leaderboard" className="hover:text-primary-700">{t("nav.leaderboard")}</Link></li>
              <li><Link to="/missions" className="hover:text-primary-700">{t("nav.missions")}</Link></li>
              <li><Link to="/api-directory" className="hover:text-primary-700">{t("nav.apis")}</Link></li>
            </ul>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-primary-800">{t("footer.resources")}</h2>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              <li><a href="/api/v1/health" className="hover:text-primary-700">{t("footer.api")}</a></li>
              <li><a href="/docs" className="hover:text-primary-700">{t("footer.docs")}</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-slate-100 px-4 py-4 text-center text-xs text-muted">
          © {new Date().getFullYear()} AfriDev Hub — {t("footer.rights")}
        </div>
      </footer>
    </div>
  );
}
