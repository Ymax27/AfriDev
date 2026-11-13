import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BookOpen, PlusCircle, Sparkles, Target, TrendingUp } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Avatar, Button, Card, EmptyState, ErrorState, ReputationBadge, SkeletonList } from "@/components/ui";
import { ProjectCard } from "@/features/projects/components/ProjectCard";
import { contributionsApi, projectsApi, reputationApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { formatDate } from "@/lib/utils";

const STATUS_TONE: Record<string, string> = {
  pending: "text-highlight-600 bg-highlight-50",
  accepted: "text-accent-700 bg-accent-50",
  rejected: "text-red-700 bg-red-50",
  withdrawn: "text-slate-600 bg-slate-100",
};

export default function DashboardPage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { user } = useAuthStore();

  const reputation = useQuery({ queryKey: ["reputation", "me"], queryFn: reputationApi.me });
  const myProjects = useQuery({
    queryKey: ["projects", "mine", user?.username],
    queryFn: () => projectsApi.list({ creator: user?.username, page_size: 6 }),
    enabled: Boolean(user?.username),
  });
  const contributions = useQuery({ queryKey: ["contributions", "me"], queryFn: contributionsApi.mine });
  const recommendations = useQuery({
    queryKey: ["projects", "recommendations"],
    queryFn: () => projectsApi.discover({ page_size: 3 }),
  });

  const summary = reputation.data;
  const level = summary?.level ?? user?.level ?? "newcomer";

  return (
    <div>
      <PageHeader
        title={t("dashboard.greeting", { name: user?.full_name ?? user?.username ?? "" })}
        description={t("dashboard.subtitle")}
        action={
          <div className="flex flex-wrap gap-2">
            <Link to="/projects/new">
              <Button icon={<PlusCircle className="size-4" aria-hidden="true" />}>{t("dashboard.newProject")}</Button>
            </Link>
            <Link to="/knowledge/new">
              <Button variant="secondary" icon={<BookOpen className="size-4" aria-hidden="true" />}>
                {t("dashboard.newProblem")}
              </Button>
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="bg-gradient-to-br from-primary-700 to-primary-900 text-white">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-primary-200">{t("dashboard.reputation")}</p>
              <p className="mt-1 text-4xl font-bold">{summary?.reputation_points ?? user?.reputation_points ?? 0}</p>
              <p className="mt-1 text-sm text-primary-100">{t("dashboard.level")} : {t(`levels.${level}`)}</p>
            </div>
            <TrendingUp className="size-8 text-accent-300" aria-hidden="true" />
          </div>
          <div className="mt-4">
            {summary?.next_level ? (
              <>
                <p className="text-xs text-primary-100">
                  {t("dashboard.nextLevel", { level: t(`levels.${summary.next_level}`) })} ·{" "}
                  {t("dashboard.pointsToNext", { points: summary.points_to_next_level })}
                </p>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/20">
                  <div
                    className="h-full rounded-full bg-accent-400"
                    style={{
                      width: `${Math.min(100, Math.round((summary.reputation_points / (summary.reputation_points + summary.points_to_next_level || 1)) * 100))}%`,
                    }}
                  />
                </div>
              </>
            ) : (
              <p className="text-xs text-primary-100">{t("dashboard.maxLevel")}</p>
            )}
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <Link to="/leaderboard">
              <Button size="sm" variant="highlight">{t("nav.leaderboard")}</Button>
            </Link>
            <Link to={`/profile/${user?.username ?? ""}`}>
              <Button size="sm" variant="secondary" className="border-white/30 bg-transparent text-white hover:bg-white/10">
                {t("nav.profile")}
              </Button>
            </Link>
          </div>
        </Card>

        <Card>
          <h2 className="mb-3 text-sm font-semibold text-primary-800">{t("dashboard.recentActivity")}</h2>
          {reputation.isLoading ? (
            <SkeletonList rows={3} />
          ) : reputation.isError ? (
            <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void reputation.refetch()} />
          ) : summary && summary.recent_transactions.length > 0 ? (
            <ul className="divide-y divide-slate-100">
              {summary.recent_transactions.slice(0, 6).map((transaction) => (
                <li key={transaction.id} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-primary-800">{transaction.action_type.replaceAll("_", " ")}</p>
                    <p className="text-xs text-muted">{formatDate(transaction.created_at, language)}</p>
                  </div>
                  <span className={transaction.points >= 0 ? "text-sm font-semibold text-accent-600" : "text-sm font-semibold text-red-600"}>
                    {transaction.points > 0 ? "+" : ""}{transaction.points}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-muted">{t("dashboard.noActivity")}</p>
          )}
        </Card>
      </div>

      <section className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-primary-800">{t("dashboard.myProjects")}</h2>
          <Link to={`/profile/${user?.username ?? ""}`} className="text-sm text-primary-700 hover:underline">
            {t("common.viewAll")}
          </Link>
        </div>
        {myProjects.isLoading ? (
          <SkeletonList rows={2} />
        ) : myProjects.data && myProjects.data.items.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {myProjects.data.items.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        ) : (
          <EmptyState
            title={t("dashboard.noProjects")}
            action={
              <Link to="/projects/new">
                <Button size="sm">{t("dashboard.newProject")}</Button>
              </Link>
            }
          />
        )}
      </section>

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-primary-800">{t("dashboard.contributions")}</h2>
          {contributions.isLoading ? (
            <SkeletonList rows={2} />
          ) : contributions.data && contributions.data.items.length > 0 ? (
            <ul className="space-y-2">
              {contributions.data.items.slice(0, 5).map((contribution) => (
                <li key={contribution.id} className="flex items-start justify-between gap-3 rounded-xl border border-slate-100 p-3">
                  <div className="min-w-0">
                    <Link to={`/projects/${contribution.project_id}`} className="text-sm font-medium text-primary-700 hover:underline">
                      {contribution.domain}
                    </Link>
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted">{contribution.message}</p>
                  </div>
                  <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_TONE[contribution.status] ?? ""}`}>
                    {t(`status.${contribution.status}`, { defaultValue: contribution.status })}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-muted">{t("dashboard.noContributions")}</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-primary-800">
            <Sparkles className="size-4 text-highlight-500" aria-hidden="true" /> {t("dashboard.recommendations")}
          </h2>
          {recommendations.isLoading ? (
            <SkeletonList rows={2} />
          ) : recommendations.data && recommendations.data.items.length > 0 ? (
            <ul className="space-y-2">
              {recommendations.data.items.map((project) => (
                <li key={project.id}>
                  <Link to={`/projects/${project.id}`} className="flex items-center gap-3 rounded-xl border border-slate-100 p-3 hover:bg-slate-50">
                    <Avatar name={project.name} src={project.cover_image_url} size={34} />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium text-primary-800">{project.name}</span>
                      <span className="block truncate text-xs text-muted">{project.technologies.slice(0, 3).join(" · ")}</span>
                    </span>
                    <ArrowRight className="size-4 shrink-0 text-muted" aria-hidden="true" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-muted">{t("dashboard.noRecommendations")}</p>
          )}
        </Card>
      </div>

      <div className="mt-8 flex flex-wrap gap-3">
        <Link to="/missions">
          <Button variant="secondary" icon={<Target className="size-4" aria-hidden="true" />}>{t("nav.missions")}</Button>
        </Link>
        <Link to={`/profile/${user?.username ?? ""}`}>
          <Button variant="ghost"><ReputationBadge level={level} points={summary?.reputation_points ?? user?.reputation_points ?? 0} label={t(`levels.${level}`)} /></Button>
        </Link>
      </div>
    </div>
  );
}
