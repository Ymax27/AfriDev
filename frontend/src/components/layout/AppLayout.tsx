import { useEffect } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Award,
  BookOpen,
  Building2,
  Compass,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Plug,
  Settings,
  Shield,
  Target,
  User,
  X,
} from "lucide-react";

import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { Logo } from "@/components/layout/Logo";
import { Avatar, ReputationBadge } from "@/components/ui";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

const NAV_ITEMS = [
  { to: "/dashboard", key: "nav.dashboard", icon: LayoutDashboard },
  { to: "/discover", key: "nav.discover", icon: Compass },
  { to: "/knowledge", key: "nav.knowledge", icon: BookOpen },
  { to: "/countries", key: "nav.countries", icon: Building2 },
  { to: "/leaderboard", key: "nav.leaderboard", icon: Award },
  { to: "/missions", key: "nav.missions", icon: Target },
  { to: "/api-directory", key: "nav.apis", icon: Plug },
  { to: "/messages", key: "nav.messages", icon: MessageSquare },
] as const;

export function AppLayout() {
  const { t } = useTranslation();
  const { user, logout } = useAuthStore();
  const { sidebarOpen, toggleSidebar, closeSidebar } = useUiStore();
  const location = useLocation();

  useEffect(() => {
    closeSidebar();
  }, [location.pathname, closeSidebar]);

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors",
      isActive ? "bg-primary-700 text-white" : "text-primary-800 hover:bg-primary-50",
    );

  return (
    <div className="min-h-screen bg-surface">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2"
      >
        {t("common.skipToContent", { defaultValue: "Aller au contenu" })}
      </a>

      <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur lg:hidden">
        <Logo />
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label={sidebarOpen ? t("nav.close") : t("nav.menu")}
          aria-expanded={sidebarOpen}
          className="rounded-lg border border-slate-300 p-2"
        >
          {sidebarOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </header>

      <div className="mx-auto flex w-full max-w-[1400px]">
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-40 w-72 shrink-0 overflow-y-auto border-r border-slate-200 bg-white p-4 transition-transform lg:sticky lg:top-0 lg:z-0 lg:h-screen lg:translate-x-0",
            sidebarOpen ? "translate-x-0" : "-translate-x-full",
          )}
          aria-label={t("nav.menu")}
        >
          <div className="mb-6 hidden lg:block">
            <Logo />
          </div>
          <div className="mb-4 flex items-center justify-between lg:hidden">
            <Logo />
            <button type="button" onClick={closeSidebar} aria-label={t("nav.close")} className="rounded-lg p-2">
              <X className="size-5" />
            </button>
          </div>

          {user ? (
            <div className="mb-6 rounded-xl bg-primary-50 p-3">
              <div className="flex items-center gap-3">
                <Avatar name={user.full_name ?? user.username} src={user.avatar_url} size={38} />
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-primary-800">{user.full_name ?? user.username}</p>
                  <p className="truncate text-xs text-muted">@{user.username}</p>
                </div>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <ReputationBadge level={user.level} points={user.reputation_points} label={t(`levels.${user.level}`)} />
              </div>
            </div>
          ) : null}

          <nav className="space-y-1" aria-label={t("nav.menu")}>
            {NAV_ITEMS.map(({ to, key, icon: Icon }) => (
              <NavLink key={to} to={to} className={linkClass} onClick={closeSidebar}>
                <Icon className="size-4" aria-hidden="true" />
                {t(key)}
              </NavLink>
            ))}
            {user ? (
              <NavLink to={`/profile/${user.username}`} className={linkClass} onClick={closeSidebar}>
                <User className="size-4" aria-hidden="true" />
                {t("nav.profile")}
              </NavLink>
            ) : null}
            <NavLink to="/settings" className={linkClass} onClick={closeSidebar}>
              <Settings className="size-4" aria-hidden="true" />
              {t("nav.settings")}
            </NavLink>
            {user?.is_admin ? (
              <NavLink to="/admin" className={linkClass} onClick={closeSidebar}>
                <Shield className="size-4" aria-hidden="true" />
                {t("nav.admin")}
              </NavLink>
            ) : null}
          </nav>

          <div className="mt-6 space-y-3 border-t border-slate-200 pt-4">
            <LanguageSwitcher />
            <button
              type="button"
              onClick={() => void logout()}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
            >
              <LogOut className="size-4" aria-hidden="true" />
              {t("nav.logout")}
            </button>
          </div>
        </aside>

        {sidebarOpen ? (
          <button
            type="button"
            aria-label={t("nav.close")}
            onClick={closeSidebar}
            className="fixed inset-0 z-30 bg-primary-900/40 lg:hidden"
          />
        ) : null}

        <main id="main-content" className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
