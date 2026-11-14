import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Ban, CalendarDays, Code2, Flag, Globe, MapPin, Pencil } from "lucide-react";

import { ReportDialog } from "@/components/ReportDialog";
import { Avatar, Badge, Button, Card, EmptyState, ErrorState, ReputationBadge, SkeletonList, TechnologyTag } from "@/components/ui";
import { moderationApi, projectsApi, usersApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { formatDate } from "@/lib/utils";

export default function ProfilePage() {
  const { username = "" } = useParams();
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { user } = useAuthStore();
  const [reportOpen, setReportOpen] = useState(false);

  const profile = useQuery({ queryKey: ["profile", username], queryFn: () => usersApi.profile(username) });
  const block = useMutation({
    mutationFn: () => moderationApi.block(username, "blocked from profile"),
    onSuccess: () => window.alert(t("profile.blocked")),
  });
  const projects = useQuery({
    queryKey: ["profile", username, "projects"],
    queryFn: () => projectsApi.list({ creator: username, page_size: 12 }),
  });

  if (profile.isLoading) return <SkeletonList rows={4} />;
  if (profile.isError || !profile.data) {
    return <ErrorState message={t("errors.notFound")} retryLabel={t("common.retry")} onRetry={() => void profile.refetch()} />;
  }

  const data = profile.data;
  const isMe = user?.username === data.username;
  const userProjects = projects.data?.items ?? [];

  return (
    <div>
      <header className="surface-card mb-5 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <Avatar name={data.full_name ?? data.username} src={data.avatar_url} size={72} />
            <div>
              <h1 className="text-2xl font-bold text-primary-800">{data.full_name ?? data.username}</h1>
              <p className="text-sm text-muted">@{data.username}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <ReputationBadge level={data.level} points={data.reputation_points} label={t(`levels.${data.level}`)} />
                {data.country ? (
                  <Badge tone="neutral">
                    <MapPin className="size-3" aria-hidden="true" /> {data.country.flag_emoji ?? ""} {language === "fr" ? data.country.name_fr : data.country.name}
                  </Badge>
                ) : null}
                {data.city ? <span className="text-xs text-muted">{data.city}</span> : null}
              </div>
            </div>
          </div>
          {isMe ? (
            <Link to="/settings" className="inline-flex items-center gap-1 rounded-xl border border-slate-300 px-3 py-2 text-sm font-medium text-primary-700 hover:bg-slate-50">
              <Pencil className="size-4" aria-hidden="true" /> {t("profile.edit")}
            </Link>
          ) : user ? (
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" size="sm" onClick={() => setReportOpen(true)} icon={<Flag className="size-4" aria-hidden="true" />}>
                {t("common.report")}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  if (window.confirm(t("profile.blockConfirm", { username: data.username }))) block.mutate();
                }}
                loading={block.isPending}
                icon={<Ban className="size-4" aria-hidden="true" />}
              >
                {t("profile.block")}
              </Button>
            </div>
          ) : null}
        </div>

        {data.bio ? <p className="mt-4 max-w-2xl whitespace-pre-line text-sm text-muted">{data.bio}</p> : null}

        <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted">
          <span className="inline-flex items-center gap-1">
            <CalendarDays className="size-3.5" aria-hidden="true" /> {t("profile.joined")} {formatDate(data.created_at, language)}
          </span>
          {data.website_url ? (
            <a href={data.website_url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-primary-700 hover:underline">
              <Globe className="size-3.5" aria-hidden="true" /> {data.website_url.replace(/^https?:\/\//, "")}
            </a>
          ) : null}
          {data.github_url ? (
            <a href={data.github_url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-primary-700 hover:underline">
              <Code2 className="size-3.5" aria-hidden="true" /> {data.github_login ?? "GitHub"}
            </a>
          ) : null}
        </div>

        {data.titles.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {data.titles.map((title) => (
              <Badge key={title} tone="highlight">
                {t(`titles.${title}`, { defaultValue: title })}
              </Badge>
            ))}
          </div>
        ) : null}

        {data.skills.length > 0 ? (
          <div className="mt-4">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">{t("profile.skills")}</h2>
            <div className="flex flex-wrap gap-1.5">
              {data.skills.map((skill) => (
                <TechnologyTag key={skill.id}>{skill.name}</TechnologyTag>
              ))}
            </div>
          </div>
        ) : null}
      </header>

      <dl className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {[
          { label: t("profile.projects"), value: data.projects_count },
          { label: t("profile.verifiedProjects"), value: data.verified_projects_count },
          { label: t("profile.solutions"), value: data.accepted_solutions_count },
          { label: t("profile.mergedContributions"), value: data.merged_contributions_count },
          { label: t("profile.reports"), value: data.field_reports_count },
          { label: t("profile.reputation"), value: data.reputation_points },
        ].map((stat) => (
          <div key={stat.label} className="surface-card p-4">
            <dt className="text-xs text-muted">{stat.label}</dt>
            <dd className="mt-1 text-2xl font-semibold text-primary-800">{stat.value}</dd>
          </div>
        ))}
      </dl>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-primary-800">{t("profile.projects")}</h2>
        {userProjects.length > 0 ? (
          <ul className="grid gap-3 md:grid-cols-2">
            {userProjects.map((project) => (
              <li key={project.id}>
                <Card>
                  <Link to={`/projects/${project.id}`} className="text-base font-semibold text-primary-800 hover:underline">
                    {project.name}
                  </Link>
                  <p className="mt-1 line-clamp-2 text-sm text-muted">{project.description}</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {project.technologies.slice(0, 3).map((technology) => (
                      <TechnologyTag key={technology}>{technology}</TechnologyTag>
                    ))}
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title={t("profile.emptyProjects")} />
        )}
      </section>

      <ReportDialog open={reportOpen} onClose={() => setReportOpen(false)} targetType="user" targetId={data.id} />
    </div>
  );
}
