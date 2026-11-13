import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { CalendarClock, Gift } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge, Card, EmptyState, ErrorState, Pagination, SearchBar, Select, SkeletonList, TechnologyTag } from "@/components/ui";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { missionsApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";
import { formatDate, truncate } from "@/lib/utils";

const STATUS_TONE: Record<string, "accent" | "primary" | "highlight" | "neutral"> = {
  published: "accent",
  in_progress: "primary",
  submitted: "highlight",
  under_review: "highlight",
  approved: "accent",
  completed: "neutral",
};

export default function MissionsPage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const debounced = useDebouncedValue(query);

  const missions = useQuery({
    queryKey: ["missions", { q: debounced, status, page }],
    queryFn: () => missionsApi.list({ q: debounced || undefined, status: status || undefined, page, page_size: 9 }),
  });

  return (
    <div>
      <PageHeader title={t("missions.title")} description={t("missions.subtitle")} />

      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <SearchBar
            label={t("common.search")}
            value={query}
            onChange={(value) => {
              setQuery(value);
              setPage(1);
            }}
            placeholder={t("missions.searchPlaceholder")}
          />
        </div>
        <label className="sm:w-52">
          <Select
            aria-label={t("missions.statusPublished")}
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">{t("common.all")}</option>
            <option value="published">{t("missions.statusPublished")}</option>
            <option value="in_progress">{t("missions.statusInProgress")}</option>
            <option value="under_review">{t("missions.statusUnderReview")}</option>
            <option value="completed">{t("missions.statusCompleted")}</option>
          </Select>
        </label>
      </div>

      {missions.isLoading ? (
        <SkeletonList rows={4} />
      ) : missions.isError ? (
        <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void missions.refetch()} />
      ) : missions.data && missions.data.items.length > 0 ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {missions.data.items.map((mission) => (
              <Card key={mission.id} className="flex h-full flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="text-base font-semibold text-primary-800">
                    <Link to={`/missions/${mission.id}`} className="hover:underline">{mission.title}</Link>
                  </h2>
                  <Badge tone={STATUS_TONE[mission.status] ?? "neutral"}>
                    {t(`missions.status${mission.status.split("_").map((part) => part[0]?.toUpperCase() + part.slice(1)).join("")}`, { defaultValue: mission.status })}
                  </Badge>
                </div>
                <p className="text-sm text-muted">{truncate(mission.description, 150)}</p>
                <div className="flex flex-wrap gap-1.5">
                  {mission.required_skills.slice(0, 3).map((skill) => (
                    <TechnologyTag key={skill}>{skill}</TechnologyTag>
                  ))}
                </div>
                <dl className="mt-auto space-y-1 text-xs text-muted">
                  <div className="flex items-center gap-1">
                    <Gift className="size-3.5" aria-hidden="true" /> {t("missions.reward")} : {mission.reward_description ?? `${mission.reward_points} ${t("missions.points")}`}
                  </div>
                  <div className="flex items-center gap-1">
                    <CalendarClock className="size-3.5" aria-hidden="true" /> {t("missions.deadline")} : {formatDate(mission.deadline, language)}
                  </div>
                  <div>
                    {t("missions.sponsor")} : @{mission.sponsor.username} · {mission.submissions_count} {t("missions.submissions")}
                  </div>
                </dl>
                <Link to={`/missions/${mission.id}`} className="text-sm font-medium text-primary-700 hover:underline">
                  {t("project.viewProject")}
                </Link>
              </Card>
            ))}
          </div>
          <Pagination
            page={missions.data.page}
            pageSize={missions.data.page_size}
            total={missions.data.total}
            onChange={setPage}
            labels={{ previous: t("common.previous"), next: t("common.next"), page: t("common.page") }}
          />
        </>
      ) : (
        <EmptyState title={t("missions.empty")} />
      )}
    </div>
  );
}
