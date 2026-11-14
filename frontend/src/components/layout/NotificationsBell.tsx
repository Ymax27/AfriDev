import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";

import { cn, relativeTime } from "@/lib/utils";
import { notificationsApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";

export function NotificationsBell() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list(),
    refetchInterval: 60_000,
  });

  const readAll = useMutation({
    mutationFn: notificationsApi.readAll,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const unread = notifications.data?.unread_count ?? 0;

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label={t("notifications.title")}
        className="relative rounded-xl border border-slate-300 bg-white p-2 text-primary-700 hover:bg-primary-50"
      >
        <Bell className="size-4" aria-hidden="true" />
        {unread > 0 ? (
          <span className="absolute -right-1.5 -top-1.5 grid min-w-5 place-items-center rounded-full bg-highlight-500 px-1 text-[10px] font-bold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        ) : null}
      </button>

      {open ? (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h2 className="text-sm font-semibold text-primary-800">{t("notifications.title")}</h2>
            {unread > 0 ? (
              <button
                type="button"
                onClick={() => readAll.mutate()}
                className="text-xs font-medium text-primary-700 hover:underline"
              >
                {t("notifications.markAll")}
              </button>
            ) : null}
          </div>

          {notifications.isLoading ? (
            <p className="px-4 py-6 text-center text-sm text-muted">{t("common.loading")}</p>
          ) : notifications.data && notifications.data.items.length > 0 ? (
            <ul className="max-h-96 divide-y divide-slate-100 overflow-y-auto">
              {notifications.data.items.map((item) => {
                const content = (
                  <span className={cn("block px-4 py-3 hover:bg-slate-50", !item.is_read && "bg-primary-50/50")}>
                    <span className="block text-sm font-medium text-primary-800">{item.title}</span>
                    {item.body ? <span className="mt-0.5 block text-xs text-muted">{item.body}</span> : null}
                    <span className="mt-1 block text-[11px] text-muted">{relativeTime(item.created_at, language)}</span>
                  </span>
                );
                return (
                  <li key={item.id}>
                    {item.link ? (
                      <Link to={item.link} onClick={() => setOpen(false)}>
                        {content}
                      </Link>
                    ) : (
                      content
                    )}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="px-4 py-8 text-center text-sm text-muted">{t("notifications.empty")}</p>
          )}
        </div>
      ) : null}
    </div>
  );
}
