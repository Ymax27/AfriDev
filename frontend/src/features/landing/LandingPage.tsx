import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Compass, Globe2, Layers, ShieldCheck, Sparkles } from "lucide-react";

import { Button } from "@/components/ui";
import { projectsApi } from "@/services/api";

export default function LandingPage() {
  const { t } = useTranslation();
  const { data } = useQuery({
    queryKey: ["projects", "landing"],
    queryFn: () => projectsApi.list({ page_size: 6, sort: "popular" }),
  });

  const pillars = [
    { icon: Layers, title: t("landing.pillarShowTitle"), text: t("landing.pillarShowText") },
    { icon: Compass, title: t("landing.pillarSolveTitle"), text: t("landing.pillarSolveText") },
    { icon: ShieldCheck, title: t("landing.pillarProveTitle"), text: t("landing.pillarProveText") },
  ];

  const steps = [
    { title: t("landing.step1Title"), text: t("landing.step1Text") },
    { title: t("landing.step2Title"), text: t("landing.step2Text") },
    { title: t("landing.step3Title"), text: t("landing.step3Text") },
    { title: t("landing.step4Title"), text: t("landing.step4Text") },
  ];

  return (
    <div>
      <section className="relative overflow-hidden bg-primary-700 text-white">
        <div className="absolute inset-0 opacity-20" aria-hidden="true">
          <div className="absolute -right-20 top-10 size-80 rounded-full bg-accent-500 blur-3xl" />
          <div className="absolute -left-10 bottom-0 size-72 rounded-full bg-highlight-500 blur-3xl" />
        </div>
        <div className="relative mx-auto grid w-full max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:py-24">
          <div>
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium">
              <Sparkles className="size-3.5" aria-hidden="true" /> {t("landing.eyebrow")}
            </p>
            <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
              {t("landing.heroTitle")}
            </h1>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-primary-100 sm:text-lg">
              {t("landing.heroSubtitle")}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/login">
                <Button size="lg" variant="highlight">{t("landing.ctaPrimary")}</Button>
              </Link>
              <Link to="/field-reports">
                <Button size="lg" variant="secondary" className="border-white/30 bg-transparent text-white hover:bg-white/10">
                  {t("landing.ctaSecondary")} <ArrowRight className="size-4" aria-hidden="true" />
                </Button>
              </Link>
            </div>
            <dl className="mt-10 grid max-w-lg grid-cols-2 gap-4 sm:grid-cols-4">
              {[
                { label: t("landing.statsDevelopers"), value: "60+" },
                { label: t("landing.statsProjects"), value: "40" },
                { label: t("landing.statsReports"), value: "15" },
                { label: t("landing.statsCountries"), value: "8" },
              ].map((stat) => (
                <div key={stat.label} className="rounded-xl border border-white/15 bg-white/5 p-3">
                  <dt className="text-xs text-primary-100">{stat.label}</dt>
                  <dd className="text-lg font-semibold">{stat.value}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="rounded-2xl border border-white/15 bg-white/10 p-5 backdrop-blur">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Globe2 className="size-4" aria-hidden="true" /> {t("discover.title")}
            </h2>
            <ul className="space-y-2">
              {(data?.items ?? []).slice(0, 5).map((project) => (
                <li key={project.id}>
                  <Link
                    to={`/projects/${project.id}`}
                    className="flex items-center justify-between gap-3 rounded-xl bg-primary-800/60 px-3 py-2.5 transition-colors hover:bg-primary-800"
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium">{project.name}</span>
                      <span className="block truncate text-xs text-primary-200">
                        {project.country?.code ? `${project.country.flag_emoji ?? ""} ${project.country.code}` : "Africa"} ·{" "}
                        {project.technologies[0] ?? project.category}
                      </span>
                    </span>
                    <ArrowRight className="size-4 shrink-0 text-primary-200" aria-hidden="true" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid gap-4 md:grid-cols-3">
          {pillars.map(({ icon: Icon, title, text }) => (
            <article key={title} className="surface-card p-6">
              <span className="inline-flex rounded-xl bg-accent-50 p-2.5 text-accent-600" aria-hidden="true">
                <Icon className="size-5" />
              </span>
              <h2 className="mt-4 text-lg font-semibold text-primary-800">{title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto w-full max-w-6xl px-4 py-14 sm:px-6">
          <h2 className="text-2xl font-bold text-primary-800">{t("landing.howTitle")}</h2>
          <p className="mt-1 text-sm text-muted">{t("landing.howSubtitle")}</p>
          <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, index) => (
              <li key={step.title} className="surface-card p-5">
                <span className="grid size-8 place-items-center rounded-full bg-primary-700 text-sm font-semibold text-white">
                  {index + 1}
                </span>
                <h3 className="mt-3 text-sm font-semibold text-primary-800">{step.title}</h3>
                <p className="mt-1.5 text-sm text-muted">{step.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 py-14 sm:px-6">
        <div className="surface-card flex flex-col items-start gap-4 bg-gradient-to-br from-primary-700 to-primary-900 p-8 text-white sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold">{t("landing.finalTitle")}</h2>
            <p className="mt-1 text-sm text-primary-100">{t("landing.finalText")}</p>
            <ul className="mt-3 flex flex-wrap gap-3 text-xs text-primary-100">
              {[t("landing.pillarShowTitle"), t("landing.pillarSolveTitle"), t("landing.pillarProveTitle")].map((item) => (
                <li key={item} className="inline-flex items-center gap-1">
                  <CheckCircle2 className="size-3.5" aria-hidden="true" /> {item}
                </li>
              ))}
            </ul>
          </div>
          <Link to="/field-reports">
            <Button variant="highlight">{t("landing.discoverCta")}</Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
