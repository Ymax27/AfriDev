import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Trophy } from "lucide-react";

import { Avatar, Badge, Card, EmptyState, ErrorState, ReputationBadge, SkeletonList } from "@/components/ui";
import { countriesApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";

export default function CountryHubPage() {
  const { code = "" } = useParams();
  const { t } = useTranslation();
  const { language } = useUiStore();
  const hub = useQuery({ queryKey: ["country", code], queryFn: () => countriesApi.hub(code) });

  if (hub.isLoading) return <SkeletonList rows={4} />;
  if (hub.isError || !hub.data) {
    return <ErrorState message={t("errors.notFound")} retryLabel={t("common.retry")} onRetry={() => void hub.refetch()} />;
  }

  const { country, stats } = hub.data;
  const name = language === "fr" ? country.name_fr : country.name;

  return (
    <div>
      <Link to="/countries" className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-primary-700">
        <ArrowLeft className="size-4" aria-hidden="true" /> {t("countries.backToCountries")}
      </Link>

      <header className="surface-card mb-5 flex flex-wrap items-center justify-between gap-4 p-6">
        <div className="flex items-center gap-4">
          <span className="text-4xl" aria-hidden="true">{country.flag_emoji ?? "🌍"}</span>
          <div>
            <h1 className="text-2xl font-bold text-primary-800">{name}</h1>
            <p className="text-sm text-muted">{country.region ?? country.code} · {code}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ReputationBadge level="contributor" points={stats.reputation_points} label={t("countries.points")} />
        </div>
      </header>

      <dl className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: t("countries.developers"), value: stats.developers },
          { label: t("countries.projects"), value: stats.projects },
          { label: t("countries.reports"), value: stats.field_reports },
          { label: t("countries.contributions"), value: stats.accepted_contributions },
        ].map((item) => (
          <div key={item.label} className="surface-card p-4">
            <dt className="text-xs text-muted">{item.label}</dt>
            <dd className="mt-1 text-2xl font-semibold text-primary-800">{item.value}</dd>
          </div>
        ))}
      </dl>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-primary-800">
            <Trophy className="size-4 text-highlight-500" aria-hidden="true" /> {t("countries.topDevelopers")}
          </h2>
          {hub.data.top_developers.length > 0 ? (
            <ul className="space-y-2">
              {hub.data.top_developers.map((developer, index) => (
                <li key={developer.username} className="flex items-center gap-3 rounded-xl border border-slate-100 p-2.5">
                  <span className="w-5 text-center text-xs font-semibold text-muted">{index + 1}</span>
                  <Avatar name={developer.full_name ?? developer.username} src={developer.avatar_url} size={32} />
                  <div className="min-w-0 flex-1">
                    <Link to={`/profile/${developer.username}`} className="block truncate text-sm font-medium text-primary-800 hover:underline">
                      {developer.full_name ?? developer.username}
                    </Link>
                    <p className="text-xs text-muted">@{developer.username}</p>
                  </div>
                  <Badge tone="primary">{developer.reputation_points} pts</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-muted">{t("countries.noData")}</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 text-sm font-semibold text-primary-800">{t("countries.recentProjects")}</h2>
          {hub.data.recent_projects.length > 0 ? (
            <ul className="space-y-2">
              {hub.data.recent_projects.map((project) => (
                <li key={project.id}>
                  <Link to={`/projects/${project.id}`} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 p-2.5 hover:bg-slate-50">
                    <span className="truncate text-sm font-medium text-primary-800">{project.name}</span>
                    <Badge tone="neutral">{t(`modes.${project.mode}.title`, { defaultValue: project.mode })}</Badge>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-muted">{t("countries.noData")}</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 text-sm font-semibold text-primary-800">{t("countries.recentReports")}</h2>
          {hub.data.recent_field_reports.length > 0 ? (
            <ul className="space-y-2">
              {hub.data.recent_field_reports.map((report) => (
                <li key={report.id}>
                  <Link to={`/field-reports/${report.id}`} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 p-2.5 hover:bg-slate-50">
                    <span className="truncate text-sm font-medium text-primary-800">{report.title}</span>
                    <Badge tone={report.status === "confirmed" ? "accent" : "primary"}>{report.status.replaceAll("_", " ")}</Badge>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-muted">{t("countries.noData")}</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 text-sm font-semibold text-primary-800">{t("countries.openMissions")}</h2>
          {hub.data.open_missions.length > 0 ? (
            <ul className="space-y-2">
              {hub.data.open_missions.map((mission) => (
                <li key={mission.id}>
                  <Link to={`/missions/${mission.id}`} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 p-2.5 hover:bg-slate-50">
                    <span className="truncate text-sm font-medium text-primary-800">{mission.title}</span>
                    <Badge tone="highlight">{mission.reward_points} pts</Badge>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title={t("countries.noData")} />
          )}
        </Card>
      </div>
    </div>
  );
}
