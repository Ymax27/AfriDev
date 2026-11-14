import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowRight, Menu, X } from "lucide-react";

import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { Logo } from "@/components/layout/Logo";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";

const PUBLIC_LINKS = [
  { to: "/knowledge", key: "nav.knowledge" },
  { to: "/field-reports", key: "landing.statsReports" },
  { to: "/countries", key: "nav.countries" },
  { to: "/missions", key: "nav.missions" },
  { to: "/api-directory", key: "nav.apis" },
  { to: "/leaderboard", key: "nav.leaderboard" },
] as const;

/** Forces the dark marketing palette while this layout is mounted. */
function useNightTheme() {
  useEffect(() => {
    document.documentElement.dataset.theme = "night";
    return () => {
      delete document.documentElement.dataset.theme;
    };
  }, []);
}

export function PublicLayout() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const { pathname } = useLocation();
  const fullBleed = pathname === "/" || pathname === "/login";
  useNightTheme();

  return (
    <div className="flex min-h-screen flex-col bg-[#0f0f12] text-white">
      <header className="sticky top-0 z-40 border-b border-[#232329] bg-[#0f0f12]/85 backdrop-blur-md">
        <div className="mx-auto flex h-16 w-full max-w-[1120px] items-center gap-5 px-4 sm:px-6">
          <Logo light />

          <nav className="hidden items-center gap-1 md:flex" aria-label="primary">
            {PUBLIC_LINKS.map(({ to, key }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "rounded-lg px-3 py-2 text-[13px] font-medium transition-colors",
                    isActive ? "text-white" : "text-[#a1a1aa] hover:text-white",
                  )
                }
              >
                {t(key)}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <div className="hidden sm:block">
              <LanguageSwitcher />
            </div>
            {user ? (
              <Link to="/dashboard" className="btn-light">
                {t("nav.dashboard")}
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="hidden rounded-lg px-3 py-2 text-[13px] font-medium text-[#e4e4e7] transition hover:text-white sm:inline-flex"
                >
                  {t("nav.login")}
                </Link>
                <Link to="/login" className="btn-light">
                  {t("landing.ctaPrimary")}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </>
            )}
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-label={menuOpen ? t("nav.close") : t("nav.menu")}
              aria-expanded={menuOpen}
              className="grid size-10 place-items-center rounded-lg border border-[#2c2c35] text-white md:hidden"
            >
              {menuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
            </button>
          </div>
        </div>

        {menuOpen ? (
          <div className="border-t border-[#232329] bg-[#121216] px-4 py-3 md:hidden">
            <nav className="grid gap-1" aria-label="mobile">
              {PUBLIC_LINKS.map(({ to, key }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={() => setMenuOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      "rounded-lg px-3 py-2 text-sm font-medium",
                      isActive ? "bg-[#1b1b21] text-white" : "text-[#a1a1aa]",
                    )
                  }
                >
                  {t(key)}
                </NavLink>
              ))}
            </nav>
            <div className="mt-3 flex items-center justify-between border-t border-[#232329] pt-3">
              <LanguageSwitcher />
              {user ? (
                <Link to="/dashboard" className="btn-light" onClick={() => setMenuOpen(false)}>
                  {t("nav.dashboard")}
                </Link>
              ) : (
                <Link to="/login" className="btn-light" onClick={() => setMenuOpen(false)}>
                  {t("nav.login")}
                </Link>
              )}
            </div>
          </div>
        ) : null}
      </header>

      <main id="main-content" className="flex-1">
        {fullBleed ? (
          <Outlet />
        ) : (
          <div className="mx-auto w-full max-w-[1120px] px-4 py-8 sm:px-6 lg:py-10">
            <Outlet />
          </div>
        )}
      </main>

      <footer className="border-t border-[#232329] bg-[#0b0b0e]">
        <div className="mx-auto grid w-full max-w-[1120px] gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <Logo light />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-[#8f8f9c]">{t("footer.slogan")}</p>
          </div>
          <FooterColumn
            title={t("footer.community")}
            links={[
              { to: "/knowledge", label: t("nav.knowledge") },
              { to: "/field-reports", label: t("landing.statsReports") },
              { to: "/countries", label: t("nav.countries") },
            ]}
          />
          <FooterColumn
            title={t("footer.product")}
            links={[
              { to: "/leaderboard", label: t("nav.leaderboard") },
              { to: "/missions", label: t("nav.missions") },
              { to: "/api-directory", label: t("nav.apis") },
            ]}
          />
          <FooterColumn
            title={t("footer.resources")}
            links={[
              { href: "/api/v1/health", label: t("footer.api") },
              { href: "/docs", label: t("footer.docs") },
            ]}
          />
        </div>
        <div className="border-t border-[#1c1c22]">
          <div className="mx-auto flex w-full max-w-[1120px] flex-col items-center justify-between gap-2 px-4 py-5 text-xs text-[#6f6f7d] sm:flex-row sm:px-6">
            <span>© {new Date().getFullYear()} AfriDev Hub — {t("footer.rights")}</span>
            <span>{t("landing.footerTagline", { defaultValue: "Montrez. Résolvez. Prouvez." })}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: { to?: string; href?: string; label: string }[];
}) {
  return (
    <div>
      <h2 className="font-display text-[13px] font-semibold uppercase tracking-wider text-[#6f6f7d]">{title}</h2>
      <ul className="mt-4 space-y-2.5 text-sm">
        {links.map((link) => (
          <li key={link.label}>
            {link.to ? (
              <Link to={link.to} className="text-[#b4b4bf] transition hover:text-white">
                {link.label}
              </Link>
            ) : (
              <a href={link.href} className="text-[#b4b4bf] transition hover:text-white">
                {link.label}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
