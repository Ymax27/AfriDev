import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { Trophy } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Avatar, Badge, Card, CountrySelector, EmptyState, ErrorState, ReputationBadge, Select, SkeletonList, Tabs } from "@/components/ui";
import { useCountries } from "@/hooks/useCountries";
import { leaderboardApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

type Tab = "developers" | "projects" | "countries";

export default function LeaderboardPage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { user } = useAuthStore();
  const { data: countries } = useCountries();
  const [tab, setTab] = useState<Tab>("developers");
  const [period, setPeriod] = useState("all");
  const [country, setCountry] = useState("");

  const developers = useQuery({
    queryKey: ["leaderboard", "developers", period, country],
    queryFn: () => leaderboardApi.developers(period, country || undefined),
    enabled: tab === "developers",
  });
  const projects = useQuery({ queryKey: ["leaderboard", "projects"], queryFn: leaderboardApi.projects, enabled: tab === "projects" });
  const countryRanks = useQuery({ queryKey: ["leaderboard", "countries"], queryFn: leaderboardApi.countries, enabled: tab === "countries" });

  return (
    <div>
      <PageHeader title={t("leaderboard.title")} description={t("leaderboard.subtitle")} />

      <div className="mb-4">
        <Tabs
          active={tab}
          onChange={setTab}
          tabs={[
            { id: "developers", label: t("leaderboard.developers") },
            { id: "projects", label: t("leaderboard.projects") },
            { id: "countries", label: t("leaderboard.countries") },
          ]}
        />
      </div>

      {tab === "developers" ? (
        <>
          <div className="mb-4 flex flex-col gap-3 sm:flex-row">
            <label className="sm:w-44">
              <span className="mb-1 block text-xs font-medium text-muted">{t("leaderboard.period")}</span>
              <Select value={period} onChange={(event) => setPeriod(event.target.value)}>
                <option value="all">{t("leaderboard.all")}</option>
                <option value="week">{t("leaderboard.week")}</option>
                <option value="month">{t("leaderboard.month")}</option>
              </Select>
            </label>
            <label className="sm:w-56">
              <span className="mb-1 block text-xs font-medium text-muted">{t("leaderboard.country")}</span>
              <CountrySelector
                countries={countries ?? []}
                value={country}
                onChange={setCountry}
                includeAll
                allLabel={t("common.all")}
                language={language}
              />
            </label>
          </div>

          {developers.isLoading ? (
            <SkeletonList rows={5} />
          ) : developers.isError ? (
            <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void developers.refetch()} />
          ) : developers.data && developers.data.items.length > 0 ? (
            <Card className="overflow-x-auto p-0">
              <table className="w-full min-w-[560px] text-sm">
                <caption className="sr-only">{t("leaderboard.developers")}</caption>
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-muted">
                    <th className="px-4 py-3">{t("leaderboard.rank")}</th>
                    <th className="px-4 py-3">{t("leaderboard.developer")}</th>
                    <th className="px-4 py-3">{t("leaderboard.country")}</th>
                    <th className="px-4 py-3">{t("leaderboard.level")}</th>
                    <th className="px-4 py-3 text-right">{t("leaderboard.points")}</th>
                    <th className="px-4 py-3 text-right">{t("leaderboard.periodPoints")}</th>
                  </tr>
                </thead>
                <tbody>
                  {developers.data.items.map((developer) => (
                    <tr key={developer.user_id} className={developer.username === user?.username ? "bg-primary-50/60" : undefined}>
                      <td className="px-4 py-3 font-semibold text-primary-800">
                        <span className="inline-flex items-center gap-1">
                          {developer.rank <= 3 ? <Trophy className="size-3.5 text-highlight-500" aria-hidden="true" /> : null}
                          {developer.rank}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Link to={`/profile/${developer.username}`} className="flex items-center gap-2 hover:underline">
                          <Avatar name={developer.full_name ?? developer.username} src={developer.avatar_url} size={30} />
                          <span>
                            <span className="block font-medium text-primary-800">{developer.full_name ?? developer.username}</span>
                            <span className="block text-xs text-muted">@{developer.username}</span>
                          </span>
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-muted">
                        {developer.country ? `${developer.country.flag_emoji ?? ""} ${language === "fr" ? developer.country.name_fr : developer.country.name}` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <ReputationBadge level={developer.level} points={developer.reputation_points} label={t(`levels.${developer.level}`)} />
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-primary-800">{developer.reputation_points}</td>
                      <td className="px-4 py-3 text-right text-accent-600">+{developer.period_points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          ) : (
            <EmptyState title={t("leaderboard.empty")} />
          )}
        </>
      ) : null}

      {tab === "projects" ? (
        projects.isLoading ? (
          <SkeletonList rows={5} />
        ) : projects.data && projects.data.length > 0 ? (
          <Card className="overflow-x-auto p-0">
            <table className="w-full min-w-[620px] text-sm">
              <caption className="sr-only">{t("leaderboard.projects")}</caption>
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-muted">
                  <th className="px-4 py-3">{t("leaderboard.rank")}</th>
                  <th className="px-4 py-3">{t("leaderboard.projects")}</th>
                  <th className="px-4 py-3 text-right">{t("leaderboard.likes")}</th>
                  <th className="px-4 py-3 text-right">{t("leaderboard.contributors")}</th>
                  <th className="px-4 py-3 text-right">{t("leaderboard.feedback")}</th>
                  <th className="px-4 py-3 text-right">{t("leaderboard.visits")}</th>
                  <th className="px-4 py-3 text-right">{t("leaderboard.score")}</th>
                </tr>
              </thead>
              <tbody>
                {projects.data.map((project) => (
                  <tr key={project.project_id}>
                    <td className="px-4 py-3 font-semibold text-primary-800">{project.rank}</td>
                    <td className="px-4 py-3">
                      <Link to={`/projects/${project.project_id}`} className="font-medium text-primary-800 hover:underline">{project.name}</Link>
                      <span className="block text-xs text-muted">@{project.creator_username}</span>
                    </td>
                    <td className="px-4 py-3 text-right">{project.likes}</td>
                    <td className="px-4 py-3 text-right">{project.accepted_contributors}</td>
                    <td className="px-4 py-3 text-right">{project.useful_feedback}</td>
                    <td className="px-4 py-3 text-right">{project.visits}</td>
                    <td className="px-4 py-3 text-right font-semibold text-accent-600">{project.score.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="border-t border-slate-100 px-4 py-3 text-xs text-muted">{t("leaderboard.formulaNote")}</p>
          </Card>
        ) : (
          <EmptyState title={t("leaderboard.empty")} />
        )
      ) : null}

      {tab === "countries" ? (
        countryRanks.isLoading ? (
          <SkeletonList rows={5} />
        ) : countryRanks.data && countryRanks.data.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {countryRanks.data.map((countryRank) => (
              <Card key={countryRank.country.code} className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-xl bg-primary-50 text-sm font-bold text-primary-700">
                  {countryRank.rank}
                </span>
                <div className="min-w-0 flex-1">
                  <Link to={`/countries/${countryRank.country.code}`} className="truncate text-sm font-semibold text-primary-800 hover:underline">
                    {countryRank.country.flag_emoji ?? ""} {language === "fr" ? countryRank.country.name_fr : countryRank.country.name}
                  </Link>
                  <p className="text-xs text-muted">
                    {countryRank.active_developers} {t("leaderboard.activeDevelopers")}
                  </p>
                </div>
                <Badge tone="accent">{countryRank.average_points.toFixed(1)}</Badge>
              </Card>
            ))}
            <p className="text-xs text-muted sm:col-span-2 xl:col-span-3">{t("leaderboard.cupNote")}</p>
          </div>
        ) : (
          <EmptyState title={t("leaderboard.empty")} />
        )
      ) : null}
    </div>
  );
}
