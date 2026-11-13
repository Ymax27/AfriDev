import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Plus } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge, Button, Card, CountrySelector, EmptyState, ErrorState, Pagination, SearchBar, SkeletonList, TechnologyTag } from "@/components/ui";
import { useCountries } from "@/hooks/useCountries";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { knowledgeApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { formatDate, truncate } from "@/lib/utils";

export default function KnowledgePage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { user } = useAuthStore();
  const { data: countries } = useCountries();
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");
  const [page, setPage] = useState(1);
  const debounced = useDebouncedValue(query);

  const problems = useQuery({
    queryKey: ["knowledge", { q: debounced, country, page }],
    queryFn: () => knowledgeApi.list({ q: debounced || undefined, country: country || undefined, page, page_size: 10 }),
  });

  return (
    <div>
      <PageHeader
        title={t("knowledge.title")}
        description={t("knowledge.subtitle")}
        action={
          user ? (
            <Link to="/knowledge/new">
              <Button icon={<Plus className="size-4" aria-hidden="true" />}>{t("knowledge.ask")}</Button>
            </Link>
          ) : null
        }
      />

      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <SearchBar
            label={t("common.search")}
            value={query}
            onChange={(value) => {
              setQuery(value);
              setPage(1);
            }}
            placeholder={t("knowledge.searchPlaceholder")}
          />
        </div>
        <div className="sm:w-56">
          <CountrySelector
            countries={countries ?? []}
            value={country}
            onChange={(code) => {
              setCountry(code);
              setPage(1);
            }}
            includeAll
            allLabel={t("common.all")}
            language={language}
          />
        </div>
      </div>

      {problems.isLoading ? (
        <SkeletonList rows={4} />
      ) : problems.isError ? (
        <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void problems.refetch()} />
      ) : problems.data && problems.data.items.length > 0 ? (
        <>
          <ul className="space-y-3">
            {problems.data.items.map((problem) => (
              <li key={problem.id}>
                <Card className="transition-colors hover:border-primary-200">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <h2 className="text-base font-semibold text-primary-800">
                        <Link to={`/knowledge/${problem.id}`} className="hover:underline">{problem.title}</Link>
                      </h2>
                      <p className="mt-1 text-sm text-muted">{truncate(problem.description, 180)}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
                        <span>@{problem.author.username}</span>
                        {problem.country ? <span>{problem.country.flag_emoji ?? ""} {problem.country.code}</span> : null}
                        <span>{formatDate(problem.created_at, language)}</span>
                        <TechnologyTag>{problem.category}</TechnologyTag>
                        {problem.technology ? <TechnologyTag>{problem.technology}</TechnologyTag> : null}
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {problem.has_accepted_solution ? (
                        <Badge tone="accent"><CheckCircle2 className="size-3" aria-hidden="true" /> {t("knowledge.accepted")}</Badge>
                      ) : null}
                      <Badge tone="primary">{problem.solution_count} {t("knowledge.solutions")}</Badge>
                    </div>
                  </div>
                </Card>
              </li>
            ))}
          </ul>
          <Pagination
            page={problems.data.page}
            pageSize={problems.data.page_size}
            total={problems.data.total}
            onChange={setPage}
            labels={{ previous: t("common.previous"), next: t("common.next"), page: t("common.page") }}
          />
        </>
      ) : (
        <EmptyState
          title={t("knowledge.empty")}
          description={t("knowledge.emptyHelp")}
          action={user ? <Link to="/knowledge/new"><Button size="sm">{t("knowledge.ask")}</Button></Link> : undefined}
        />
      )}
    </div>
  );
}
