import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, ExternalLink } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge, Card, CountrySelector, EmptyState, ErrorState, Pagination, SearchBar, Select, SkeletonList } from "@/components/ui";
import { useCountries } from "@/hooks/useCountries";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { apisDirectoryApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";
import { truncate } from "@/lib/utils";

const STATUS_TONE: Record<string, "accent" | "highlight" | "danger"> = {
  operational: "accent",
  degraded: "highlight",
  maintenance: "danger",
};

export default function ApiDirectoryPage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { data: countries } = useCountries();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [country, setCountry] = useState("");
  const [page, setPage] = useState(1);
  const debounced = useDebouncedValue(query);

  const categories = useQuery({ queryKey: ["apis", "categories"], queryFn: apisDirectoryApi.categories });
  const entries = useQuery({
    queryKey: ["apis", { q: debounced, category, country, page }],
    queryFn: () =>
      apisDirectoryApi.list({
        q: debounced || undefined,
        category: category || undefined,
        country: country || undefined,
        page,
        page_size: 12,
      }),
  });

  return (
    <div>
      <PageHeader title={t("apis.title")} description={t("apis.subtitle")} />

      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <SearchBar
            label={t("common.search")}
            value={query}
            onChange={(value) => {
              setQuery(value);
              setPage(1);
            }}
            placeholder={t("apis.searchPlaceholder")}
          />
        </div>
        <label className="sm:w-48">
          <Select
            aria-label={t("apis.category")}
            value={category}
            onChange={(event) => {
              setCategory(event.target.value);
              setPage(1);
            }}
          >
            <option value="">{t("common.all")}</option>
            {(categories.data ?? []).map((item) => (
              <option key={item.category} value={item.category}>
                {t(`apis.categories.${item.category}`, { defaultValue: item.category })} ({item.count})
              </option>
            ))}
          </Select>
        </label>
        <div className="sm:w-48">
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

      {entries.isLoading ? (
        <SkeletonList rows={4} />
      ) : entries.isError ? (
        <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void entries.refetch()} />
      ) : entries.data && entries.data.items.length > 0 ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {entries.data.items.map((entry) => (
              <Card key={entry.id} className="flex h-full flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-base font-semibold text-primary-800">
                      <Link to={`/api-directory/${entry.id}`} className="hover:underline">{entry.name}</Link>
                    </h2>
                    <p className="text-xs text-muted">{entry.provider_name}</p>
                  </div>
                  <Badge tone={STATUS_TONE[entry.api_status] ?? "neutral"}>
                    {t(`apis.${entry.api_status}`, { defaultValue: entry.api_status })}
                  </Badge>
                </div>
                <p className="text-sm text-muted">{truncate(entry.description, 140)}</p>
                <div className="flex flex-wrap gap-1.5 text-xs">
                  <Badge tone="primary">{t(`apis.categories.${entry.category}`, { defaultValue: entry.category })}</Badge>
                  {entry.countries.slice(0, 3).map((code) => (
                    <Badge key={code} tone="neutral">{code}</Badge>
                  ))}
                </div>
                <div className="mt-auto flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
                  <Link to={`/api-directory/${entry.id}`} className="inline-flex items-center gap-1 font-medium text-primary-700 hover:underline">
                    {t("common.viewAll")} <ArrowRight className="size-3.5" aria-hidden="true" />
                  </Link>
                  <a href={entry.documentation_url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-muted hover:text-primary-700">
                    <ExternalLink className="size-3.5" aria-hidden="true" /> {t("apis.docs")}
                  </a>
                </div>
              </Card>
            ))}
          </div>
          <Pagination
            page={entries.data.page}
            pageSize={entries.data.page_size}
            total={entries.data.total}
            onChange={setPage}
            labels={{ previous: t("common.previous"), next: t("common.next"), page: t("common.page") }}
          />
        </>
      ) : (
        <EmptyState title={t("apis.empty")} />
      )}
    </div>
  );
}
