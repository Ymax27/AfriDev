import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowRight, Eye, Heart, Star, Users } from "lucide-react";

import { Avatar, Badge, DemoBadge, TechnologyTag } from "@/components/ui";
import { cn, truncate } from "@/lib/utils";
import type { Project } from "@/types/api";

const MODE_TONE = {
  showcase: "primary",
  feedback: "highlight",
  open_to_contributors: "accent",
} as const;

export function ProjectCard({
  project,
  onLike,
  onPass,
  showActions = false,
  pending = false,
}: {
  project: Project;
  onLike?: () => void;
  onPass?: () => void;
  showActions?: boolean;
  pending?: boolean;
}) {
  const { t } = useTranslation();

  return (
    <article className="surface-card flex h-full flex-col gap-4 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <Avatar name={project.name} src={project.cover_image_url} size={44} />
          <div className="min-w-0">
            <h2 className="truncate text-base font-semibold text-primary-800">
              <Link to={`/projects/${project.id}`} className="hover:underline">
                {project.name}
              </Link>
            </h2>
            <p className="mt-0.5 truncate text-xs text-muted">
              {t("project.publishedBy")} @{project.creator.username}
              {project.country ? ` · ${project.country.flag_emoji ?? ""} ${project.country.code}` : ""}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <Badge tone={MODE_TONE[project.collaboration_mode]}>
            {t(`modes.${project.collaboration_mode}.title`)}
          </Badge>
          <DemoBadge show={project.is_demo} />
        </div>
      </div>

      <p className="text-sm leading-relaxed text-muted">{truncate(project.description, 170)}</p>

      <div className="flex flex-wrap gap-1.5">
        {project.technologies.slice(0, 4).map((technology) => (
          <TechnologyTag key={technology}>{technology}</TechnologyTag>
        ))}
      </div>

      <div className="mt-auto flex flex-wrap items-center gap-4 text-xs text-muted">
        <span className="inline-flex items-center gap-1"><Heart className="size-3.5" aria-hidden="true" /> {project.likes_count}</span>
        <span className="inline-flex items-center gap-1"><Users className="size-3.5" aria-hidden="true" /> {project.contributions_count}</span>
        <span className="inline-flex items-center gap-1"><Eye className="size-3.5" aria-hidden="true" /> {project.view_count}</span>
        <span className="inline-flex items-center gap-1"><Star className="size-3.5" aria-hidden="true" /> {project.github_stars}</span>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
        <Link
          to={`/projects/${project.id}`}
          className="inline-flex items-center gap-1 text-sm font-medium text-primary-700 hover:underline"
        >
          {t("project.viewProject")} <ArrowRight className="size-3.5" aria-hidden="true" />
        </Link>
        {showActions ? (
          <div className="ml-auto flex gap-2">
            {onPass ? (
              <button
                type="button"
                onClick={onPass}
                disabled={pending}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-muted hover:bg-slate-50 disabled:opacity-50"
              >
                {t("project.pass")}
              </button>
            ) : null}
            {onLike ? (
              <button
                type="button"
                onClick={onLike}
                disabled={pending || project.liked_by_me}
                className={cn(
                  "inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-semibold",
                  project.liked_by_me
                    ? "bg-accent-50 text-accent-700"
                    : "bg-primary-700 text-white hover:bg-primary-800 disabled:opacity-50",
                )}
              >
                <Heart className="size-3.5" aria-hidden="true" />
                {project.liked_by_me ? t("project.liked") : t("project.like")}
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
    </article>
  );
}
