import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { BadgeCheck, Clock } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge, Card, CountrySelector, EmptyState, ErrorState, Pagination, SearchBar, SkeletonList } from "@/components/ui";
import { useCountries } from "@/hooks/useCountries";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { fieldReportsApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";
import { formatDate, truncate } from "@/lib/utils";

const STATUS_TONE: Record<string, "accent" | "primary" | "highlight" | "neutral"> = {
  confirmed: "accent",
  published: "primary",
  needs_revalidation: "highlight",
  archived: "neutral",
};

const STATUS_KEYS: Record<string, string> = {
  confirmed: "fieldReports.statusConfirmed",
  published: "fieldReports.statusPublished",
  needs_revalidation: "fieldReports.statusNeedsRevalidation",
  archived: "fieldReports.statusArchived",
};

export default function FieldReportsPage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { data: countries } = useCountries();
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");
  const [page, setPage] = useState(1);
  const debounced = useDebouncedValue(query);

  const reports = useQuery({
    queryKey: ["field-reports", { q: debounced, country, page }],
    queryFn: () => fieldReportsApi.list({ q: debounced || undefined, country: country || undefined, page, page_size: 10 }),
  });

  return (
    <div>
      <PageHeader title={t("fieldReports.title")} description={t("fieldReports.subtitle")} />

      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <SearchBar
            label={t("common.search")}
            value={query}
            onChange={(value) => {
              setQuery(value);
              setPage(1);
            }}
            placeholder={t("fieldReports.searchPlaceholder")}
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

      {reports.isLoading ? (
        <SkeletonList rows={4} />
      ) : reports.isError ? (
        <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void reports.refetch()} />
      ) : reports.data && reports.data.items.length > 0 ? (
        <>
          <ul className="space-y-3">
            {reports.data.items.map((report) => (
              <li key={report.id}>
                <Card className="transition-colors hover:border-primary-200">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <h2 className="text-base font-semibold text-primary-800">
                        <Link to={`/field-reports/${report.id}`} className="hover:underline">{report.title}</Link>
                      </h2>
                      <p className="mt-1 text-sm text-muted">{truncate(report.problem_summary, 180)}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted">
                        {report.country ? (
                          <span>{report.country.flag_emoji ?? ""} {language === "fr" ? report.country.name_fr : report.country.name}</span>
                        ) : null}
                        <span className="inline-flex items-center gap-1">
                          <BadgeCheck className="size-3.5" aria-hidden="true" /> {report.confirmation_count} {t("fieldReports.confirmations")}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Clock className="size-3.5" aria-hidden="true" /> {t("fieldReports.lastValidated")} {formatDate(report.last_validated_at, language)}
                        </span>
                      </div>
                    </div>
                    <Badge tone={STATUS_TONE[report.status] ?? "neutral"}>
                      {t(STATUS_KEYS[report.status] ?? "fieldReports.statusPublished")}
                    </Badge>
                  </div>
                </Card>
              </li>
            ))}
          </ul>
          <Pagination
            page={reports.data.page}
            pageSize={reports.data.page_size}
            total={reports.data.total}
            onChange={setPage}
            labels={{ previous: t("common.previous"), next: t("common.next"), page: t("common.page") }}
          />
        </>
      ) : (
        <EmptyState title={t("fieldReports.empty")} />
      )}
    </div>
  );
}
