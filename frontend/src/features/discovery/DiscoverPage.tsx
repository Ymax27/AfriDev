import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RotateCcw } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button, CountrySelector, EmptyState, ErrorState, Select, SkeletonList } from "@/components/ui";
import { ProjectCard } from "@/features/projects/components/ProjectCard";
import { useCountries } from "@/hooks/useCountries";
import { projectsApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";

const MODES = ["showcase", "feedback", "open_to_contributors"] as const;

export default function DiscoverPage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState("");
  const [country, setCountry] = useState("");
  const [technology, setTechnology] = useState("");
  const [sort, setSort] = useState("recent");
  const { data: countries } = useCountries();

  const params = {
    page_size: 12,
    mode: mode || undefined,
    country: country || undefined,
    technology: technology || undefined,
    sort,
  };

  const feed = useQuery({
    queryKey: ["projects", "discover", params],
    queryFn: () => projectsApi.discover(params),
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["projects"] });
  };

  const like = useMutation({ mutationFn: (id: string) => projectsApi.like(id), onSuccess: invalidate });
  const pass = useMutation({ mutationFn: (id: string) => projectsApi.pass(id), onSuccess: invalidate });

  const resetFeed = async () => {
    setMode("");
    setCountry("");
    setTechnology("");
    setSort("recent");
    void queryClient.invalidateQueries({ queryKey: ["projects", "discover"] });
  };

  const technologies = Array.from(new Set(feed.data?.items.flatMap((project) => project.technologies) ?? [])).sort();

  return (
    <div>
      <PageHeader title={t("discover.title")} description={t("discover.subtitle")} />

      <div className="mb-5 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="text-sm">
          <span className="mb-1 block text-xs font-medium text-muted">{t("discover.modeFilter")}</span>
          <Select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="">{t("common.all")}</option>
            {MODES.map((item) => (
              <option key={item} value={item}>{t(`modes.${item}.title`)}</option>
            ))}
          </Select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs font-medium text-muted">{t("discover.countryFilter")}</span>
          <CountrySelector
            countries={countries ?? []}
            value={country}
            onChange={setCountry}
            includeAll
            allLabel={t("common.all")}
            language={language}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs font-medium text-muted">{t("discover.technologyFilter")}</span>
          <Select value={technology} onChange={(event) => setTechnology(event.target.value)}>
            <option value="">{t("common.all")}</option>
            {technologies.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </Select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs font-medium text-muted">{t("discover.sortRecent")}</span>
          <Select value={sort} onChange={(event) => setSort(event.target.value)}>
            <option value="recent">{t("discover.sortRecent")}</option>
            <option value="popular">{t("discover.sortPopular")}</option>
            <option value="oldest">{t("discover.sortOldest")}</option>
          </Select>
        </label>
      </div>

      {feed.isLoading ? (
        <SkeletonList rows={3} />
      ) : feed.isError ? (
        <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void feed.refetch()} />
      ) : feed.data && feed.data.items.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {feed.data.items.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              showActions
              pending={like.isPending || pass.isPending}
              onLike={() => like.mutate(project.id)}
              onPass={() => pass.mutate(project.id)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title={t("discover.empty")}
          description={t("discover.emptyHelp")}
          action={
            <Button variant="secondary" onClick={() => void resetFeed()} icon={<RotateCcw className="size-4" aria-hidden="true" />}>
              {t("discover.resetFeed")}
            </Button>
          }
        />
      )}
    </div>
  );
}
