import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, ShieldAlert, Trash2 } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Badge, Button, Card, EmptyState, ErrorState, Input, SkeletonList, Tabs } from "@/components/ui";
import { adminApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { formatDate } from "@/lib/utils";

const REPORT_STATUS_TONE: Record<string, "highlight" | "accent" | "neutral"> = {
  pending: "highlight",
  resolved: "accent",
  dismissed: "neutral",
};

export default function AdminPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"overview" | "users" | "reports" | "demo">("overview");
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const debounced = useDebouncedValue(search);

  const overview = useQuery({ queryKey: ["admin", "overview"], queryFn: adminApi.overview });
  const users = useQuery({
    queryKey: ["admin", "users", debounced],
    queryFn: () => adminApi.users(debounced || undefined),
    enabled: tab === "users",
  });
  const reports = useQuery({ queryKey: ["admin", "reports"], queryFn: adminApi.reports, enabled: tab === "reports" });

  const recalculate = useMutation({
    mutationFn: adminApi.recalculate,
    onSuccess: (result) => {
      setNotice(t("admin.recalculated", { count: result.users_recalculated }));
      void queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
  });

  const purge = useMutation({
    mutationFn: adminApi.purgeDemo,
    onSuccess: (result) => {
      setNotice(t("admin.purgeDone", { users: result.users_removed ?? result.users ?? 0 }));
      void queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
  });

  const suspend = useMutation({
    mutationFn: (id: string) => adminApi.suspend(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  });
  const reactivate = useMutation({
    mutationFn: (id: string) => adminApi.reactivate(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  });
  const resolveReport = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "resolved" | "dismissed" }) => adminApi.resolveReport(id, status),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin", "reports"] }),
  });

  if (!user?.is_admin) {
    return <ErrorState message={t("admin.accessDenied")} retryLabel={t("common.retry")} />;
  }

  const stats = overview.data;

  return (
    <div>
      <PageHeader
        title={t("admin.title")}
        description={t("admin.subtitle")}
        action={
          <Button variant="secondary" size="sm" onClick={() => recalculate.mutate()} loading={recalculate.isPending} icon={<RefreshCw className="size-4" aria-hidden="true" />}>
            {t("admin.recalculate")}
          </Button>
        }
      />

      {notice ? <div className="mb-4"><Alert tone="success">{notice}</Alert></div> : null}

      <div className="mb-4">
        <Tabs
          active={tab}
          onChange={setTab}
          tabs={[
            { id: "overview", label: t("admin.overview") },
            { id: "users", label: t("admin.users") },
            { id: "reports", label: t("admin.reports") },
            { id: "demo", label: t("admin.demo") },
          ]}
        />
      </div>

      {tab === "overview" ? (
        overview.isLoading ? (
          <SkeletonList rows={3} />
        ) : overview.isError || !stats ? (
          <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void overview.refetch()} />
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
            {[
              { label: t("admin.totalUsers"), value: stats.users },
              { label: t("admin.activeUsers"), value: stats.active_users },
              { label: t("admin.demoUsers"), value: stats.demo_users },
              { label: t("admin.projects"), value: stats.projects },
              { label: t("admin.problems"), value: stats.problems },
              { label: t("admin.fieldReports"), value: stats.field_reports },
              { label: t("admin.missions"), value: stats.missions },
              { label: t("admin.apis"), value: stats.api_entries },
              { label: t("admin.openReports"), value: stats.open_reports },
              { label: t("admin.ledgerEntries"), value: stats.reputation_transactions },
              { label: t("admin.pointsAwarded"), value: stats.points_awarded },
            ].map((item) => (
              <div key={item.label} className="surface-card p-4">
                <p className="text-xs text-muted">{item.label}</p>
                <p className="mt-1 text-2xl font-semibold text-primary-800">{item.value}</p>
              </div>
            ))}
          </div>
        )
      ) : null}

      {tab === "users" ? (
        <>
          <div className="mb-4 max-w-sm">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t("admin.searchUsers")}
              aria-label={t("admin.searchUsers")}
            />
          </div>
          {users.isLoading ? (
            <SkeletonList rows={4} />
          ) : users.data && users.data.items.length > 0 ? (
            <Card className="overflow-x-auto p-0">
              <table className="w-full min-w-[560px] text-sm">
                <caption className="sr-only">{t("admin.users")}</caption>
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-muted">
                    <th className="px-4 py-3">{t("admin.users")}</th>
                    <th className="px-4 py-3">{t("leaderboard.country")}</th>
                    <th className="px-4 py-3">{t("admin.status")}</th>
                    <th className="px-4 py-3">{t("profile.reputation")}</th>
                    <th className="px-4 py-3 text-right">{t("admin.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {users.data.items.map((row) => {
                    const id = String(row.id);
                    const active = Boolean(row.is_active);
                    const country = row.country as { code?: string; flag_emoji?: string } | null | undefined;
                    return (
                      <tr key={id} className="border-b border-slate-50">
                        <td className="px-4 py-3">
                          <span className="block font-medium text-primary-800">{String(row.full_name ?? row.username)}</span>
                          <span className="block text-xs text-muted">@{String(row.username)}</span>
                        </td>
                        <td className="px-4 py-3 text-muted">{country?.code ?? "—"}</td>
                        <td className="px-4 py-3">
                          <Badge tone={active ? "accent" : "danger"}>{active ? t("admin.activeUsers") : t("admin.suspend")}</Badge>
                        </td>
                        <td className="px-4 py-3">{Number(row.reputation_points ?? 0)}</td>
                        <td className="px-4 py-3 text-right">
                          {active ? (
                            <Button size="sm" variant="secondary" onClick={() => suspend.mutate(id)}>{t("admin.suspend")}</Button>
                          ) : (
                            <Button size="sm" onClick={() => reactivate.mutate(id)}>{t("admin.reactivate")}</Button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          ) : (
            <EmptyState title={t("common.empty")} />
          )}
        </>
      ) : null}

      {tab === "reports" ? (
        reports.isLoading ? (
          <SkeletonList rows={3} />
        ) : reports.data && reports.data.length > 0 ? (
          <ul className="space-y-3">
            {reports.data.map((report) => {
              const id = String(report.id);
              const status = String(report.status);
              return (
                <li key={id}>
                  <Card className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <ShieldAlert className="size-4 text-highlight-500" aria-hidden="true" />
                        <p className="text-sm font-medium text-primary-800">
                          {String(report.reason ?? report.type ?? t("admin.reports"))}
                        </p>
                        <Badge tone={REPORT_STATUS_TONE[status] ?? "neutral"}>{status}</Badge>
                      </div>
                      {report.details ? <p className="mt-1 text-sm text-muted">{String(report.details)}</p> : null}
                      {report.created_at ? <p className="mt-1 text-xs text-muted">{formatDate(String(report.created_at))}</p> : null}
                    </div>
                    {status === "pending" ? (
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => resolveReport.mutate({ id, status: "resolved" })}>{t("admin.resolve")}</Button>
                        <Button size="sm" variant="secondary" onClick={() => resolveReport.mutate({ id, status: "dismissed" })}>{t("admin.dismiss")}</Button>
                      </div>
                    ) : null}
                  </Card>
                </li>
              );
            })}
          </ul>
        ) : (
          <EmptyState title={t("admin.noReports")} />
        )
      ) : null}

      {tab === "demo" ? (
        <Card className="space-y-3">
          <h2 className="text-sm font-semibold text-primary-800">{t("admin.demo")}</h2>
          <p className="text-sm text-muted">{t("admin.demoHint")}</p>
          <p className="text-sm text-muted">{t("admin.purgeConfirm")}</p>
          <Button
            variant="danger"
            onClick={() => {
              if (window.confirm(t("admin.purgeConfirm"))) purge.mutate();
            }}
            loading={purge.isPending}
            icon={<Trash2 className="size-4" aria-hidden="true" />}
          >
            {t("admin.purge")}
          </Button>
        </Card>
      ) : null}
    </div>
  );
}
