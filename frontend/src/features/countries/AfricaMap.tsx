import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import type { Country } from "@/types/api";

import { AFRICA_PATHS, AFRICA_VIEWBOX } from "./africa-map-data";

export function AfricaMap({
  countries,
  activity,
}: {
  countries: Country[];
  activity: Record<string, number>;
}) {
  const { t } = useTranslation();
  const known = new Map(countries.map((country) => [country.code, country]));
  const max = Math.max(1, ...Object.values(activity));

  const tone = (code: string) => {
    const value = activity[code] ?? 0;
    if (!value) return "fill-slate-100";
    const ratio = value / max;
    if (ratio > 0.66) return "fill-accent-500";
    if (ratio > 0.33) return "fill-accent-400";
    if (ratio > 0.1) return "fill-accent-300";
    return "fill-accent-200";
  };

  return (
    <figure className="surface-card p-4">
      <svg viewBox={AFRICA_VIEWBOX} role="img" aria-label={t("countries.mapLabel")} className="mx-auto h-auto w-full max-w-xl">
        <g className="stroke-white stroke-[0.6]">
          {AFRICA_PATHS.map((shape) => {
            const country = known.get(shape.code);
            if (!country) {
              return (
                <path key={`${shape.code}-${shape.name}`} d={shape.d} className="fill-slate-100">
                  <title>{shape.name}</title>
                </path>
              );
            }
            return (
              <Link key={shape.code} to={`/countries/${shape.code}`} aria-label={shape.name}>
                <path d={shape.d} className={`${tone(shape.code)} transition-colors hover:fill-primary-500`}>
                  <title>{`${shape.name} · ${activity[shape.code] ?? 0} ${t("countries.projects")}`}</title>
                </path>
              </Link>
            );
          })}
        </g>
      </svg>

      <figcaption className="mt-2 flex flex-wrap items-center justify-center gap-3 text-xs text-muted">
        <span className="inline-flex items-center gap-1">
          <span className="size-3 rounded-sm bg-slate-100" aria-hidden="true" /> {t("countries.mapNone")}
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="size-3 rounded-sm bg-accent-300" aria-hidden="true" /> {t("countries.mapSome")}
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="size-3 rounded-sm bg-accent-500" aria-hidden="true" /> {t("countries.mapMost")}
        </span>
        <span className="text-[11px]">{t("countries.mapSource")}</span>
      </figcaption>
    </figure>
  );
}
