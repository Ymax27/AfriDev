import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, MapPin } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Badge, Card, ErrorState, SkeletonList } from "@/components/ui";
import { AfricaMap } from "@/features/countries/AfricaMap";
import { useCountries } from "@/hooks/useCountries";
import { countriesApi, leaderboardApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";

export default function CountriesPage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const countries = useCountries();
  const activity = useQuery({ queryKey: ["leaderboard", "countries", "week"], queryFn: () => leaderboardApi.countries("week") });
  const activityByCode = Object.fromEntries(
    (activity.data ?? []).map((item) => [item.country.code, item.week_points]),
  );

  return (
    <div>
      <PageHeader title={t("countries.title")} description={t("countries.subtitle")} />

      {countries.data && countries.data.length > 0 ? (
        <div className="mb-5">
          <AfricaMap countries={countries.data} activity={activityByCode} />
        </div>
      ) : null}

      {countries.isLoading ? (
        <SkeletonList rows={3} />
      ) : countries.isError ? (
        <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void countries.refetch()} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {(countries.data ?? []).map((country) => (
            <CountryCard key={country.code} code={country.code} label={language === "fr" ? country.name_fr : country.name} flag={country.flag_emoji} region={country.region} />
          ))}
        </div>
      )}
    </div>
  );
}

function CountryCard({ code, label, flag, region }: { code: string; label: string; flag?: string | null; region?: string | null }) {
  const { t } = useTranslation();
  const hub = useQuery({ queryKey: ["country", code], queryFn: () => countriesApi.hub(code) });

  return (
    <Card className="flex h-full flex-col gap-3">
      <div className="flex items-center gap-2">
        <span className="text-2xl" aria-hidden="true">{flag ?? "🌍"}</span>
        <div>
          <h2 className="text-base font-semibold text-primary-800">
            <Link to={`/countries/${code}`} className="hover:underline">{label}</Link>
          </h2>
          <p className="inline-flex items-center gap-1 text-xs text-muted">
            <MapPin className="size-3" aria-hidden="true" /> {region ?? code}
          </p>
        </div>
        <Badge tone="primary" className="ml-auto">{code}</Badge>
      </div>

      {hub.isLoading ? (
        <div className="space-y-2" aria-hidden="true">
          <div className="h-3 w-2/3 animate-pulse rounded bg-slate-200" />
          <div className="h-3 w-1/2 animate-pulse rounded bg-slate-100" />
        </div>
      ) : hub.data ? (
        <dl className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-xl bg-slate-50 p-2">
            <dt className="text-[10px] uppercase text-muted">{t("countries.developers")}</dt>
            <dd className="text-sm font-semibold text-primary-800">{hub.data.stats.developers}</dd>
          </div>
          <div className="rounded-xl bg-slate-50 p-2">
            <dt className="text-[10px] uppercase text-muted">{t("countries.projects")}</dt>
            <dd className="text-sm font-semibold text-primary-800">{hub.data.stats.projects}</dd>
          </div>
          <div className="rounded-xl bg-slate-50 p-2">
            <dt className="text-[10px] uppercase text-muted">{t("countries.reports")}</dt>
            <dd className="text-sm font-semibold text-primary-800">{hub.data.stats.field_reports}</dd>
          </div>
        </dl>
      ) : (
        <p className="text-xs text-muted">{t("countries.noData")}</p>
      )}

      <Link to={`/countries/${code}`} className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-primary-700 hover:underline">
        {t("common.viewAll")} <ArrowRight className="size-3.5" aria-hidden="true" />
      </Link>
    </Card>
  );
}
