import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  BadgeCheck,
  BookOpen,
  Building2,
  Compass,
  Flame,
  Globe2,
  Layers,
  MapPin,
  MessagesSquare,
  Plug,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import { projectsApi } from "@/services/api";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "feed", icon: Flame },
  { key: "problems", icon: BookOpen },
  { key: "reports", icon: MapPin },
  { key: "countries", icon: Building2 },
  { key: "missions", icon: Target },
  { key: "apis", icon: Plug },
] as const;

const STACKS = [
  "React",
  "TypeScript",
  "Python",
  "Node.js",
  "Go",
  "Flutter",
  "Rust",
  "Django",
  "Laravel",
  "PostgreSQL",
  "Supabase",
  "AWS",
];

export default function LandingPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("feed");
  const { data } = useQuery({
    queryKey: ["projects", "landing"],
    queryFn: () => projectsApi.list({ page_size: 6, sort: "popular" }),
  });

  const projects = data?.items ?? [];
  const stats = [
    { label: t("landing.statsDevelopers"), value: "61", icon: Globe2 },
    { label: t("landing.statsProjects"), value: "40", icon: Layers },
    { label: t("landing.statsReports"), value: "15", icon: MapPin },
    { label: t("landing.statsCountries"), value: "8", icon: Compass },
  ];

  const features = [
    { title: t("landing2.feature1Title"), text: t("landing2.feature1Text"), icon: TrendingUp },
    { title: t("landing2.feature2Title"), text: t("landing2.feature2Text"), icon: ShieldCheck },
    { title: t("landing2.feature3Title"), text: t("landing2.feature3Text"), icon: MessagesSquare },
  ];

  const steps = [
    { title: t("landing.step1Title"), text: t("landing.step1Text") },
    { title: t("landing.step2Title"), text: t("landing.step2Text") },
    { title: t("landing.step3Title"), text: t("landing.step3Text") },
    { title: t("landing.step4Title"), text: t("landing.step4Text") },
  ];

  return (
    <div className="overflow-x-hidden">
      {/* ---------------------------------------------------------------- Hero */}
      <section className="relative isolate">
        <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
          <div className="animate-glow absolute -right-40 top-[5%] size-[520px] rounded-full bg-[#6d28d9] opacity-[0.18] blur-[150px]" />
          <div className="animate-glow absolute right-10 top-52 size-[260px] rounded-full bg-[#db2777] opacity-[0.10] blur-[120px]" />
          <div className="absolute -left-40 top-10 size-[340px] rounded-full bg-[#312e81] opacity-[0.16] blur-[140px]" />
        </div>

        <div className="mx-auto grid w-full max-w-[1120px] items-center gap-14 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
          <div className="animate-rise">
            <span className="inline-flex items-center gap-2 rounded-full border border-[#2c2c35] bg-[#17171d] px-3 py-1 text-xs font-medium text-[#c9c9d2]">
              <Sparkles className="size-3.5 text-[#c4b5fd]" aria-hidden="true" />
              {t("landing2.badge")}
            </span>

            <h1 className="font-display mt-6 max-w-[600px] text-balance text-[32px] font-extrabold leading-[1.08] tracking-[-0.03em] sm:text-[42px] lg:text-[48px]">
              {t("landing2.heroLine1")}
              <br />
              <span className="bg-gradient-to-r from-white via-[#d8ccff] to-[#f0abfc] bg-clip-text text-transparent">
                {t("landing2.heroLine2")}
              </span>
            </h1>

            <p className="mt-6 max-w-[520px] text-[16px] leading-relaxed text-[#a1a1aa]">
              {t("landing.heroSubtitle")}
            </p>

            <div className="mt-9 flex max-w-[420px] flex-col gap-3">
              <Link
                to="/login"
                className="btn-light h-12 text-[15px]"
              >
                <BadgeCheck className="size-4" aria-hidden="true" />
                {t("landing.ctaPrimary")}
              </Link>
              <Link
                to="/field-reports"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-xl border border-[#2c2c35] bg-[#1c1c22] text-[15px] font-semibold text-white transition hover:border-[#3d3d49] hover:bg-[#24242b]"
              >
                {t("landing.ctaSecondary")}
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </div>

            <p className="mt-5 max-w-[420px] text-[11px] leading-relaxed text-[#6f6f7d]">
              {t("landing2.terms")}
            </p>
            <p className="mt-3 text-sm text-[#a1a1aa]">
              {t("landing2.already")}{" "}
              <Link to="/login" className="font-medium text-white underline underline-offset-4 hover:text-[#c4b5fd]">
                {t("nav.login")}
              </Link>
            </p>
          </div>

          {/* Feed preview */}
          <div className="animate-rise relative [animation-delay:120ms]">
            <div className="animate-float">
              <div className="night-card relative overflow-hidden rounded-[20px] p-3 shadow-[0_40px_120px_-40px_rgba(124,58,237,0.65)]">
                <div className="flex items-center gap-2 px-2 pb-3 pt-1">
                  <span className="size-2.5 rounded-full bg-[#f87171]" />
                  <span className="size-2.5 rounded-full bg-[#fbbf24]" />
                  <span className="size-2.5 rounded-full bg-[#34d399]" />
                  <span className="ml-2 text-[11px] font-medium text-[#6f6f7d]">afridev.hub / feed</span>
                </div>
                <div className="space-y-2.5">
                  {(projects.length > 0 ? projects.slice(0, 3) : [null, null, null]).map((project, index) => (
                    <div
                      key={project?.id ?? index}
                      className="rounded-xl border border-[#26262e] bg-[#191920] p-3 transition hover:border-[#3d3d49]"
                    >
                      <div className="flex items-center gap-2">
                        <span className="grid size-6 place-items-center rounded-md bg-gradient-to-br from-[#8b5cf6] to-[#4c1d95] text-[9px] font-bold text-white">
                          {(project?.name ?? "AD").slice(0, 2).toUpperCase()}
                        </span>
                        <span className="truncate text-[11px] text-[#8f8f9c]">
                          {project ? `@${project.creator.username}` : "@community"}
                        </span>
                        {project?.ownership_status === "verified" ? (
                          <BadgeCheck className="size-3.5 text-[#8b5cf6]" aria-hidden="true" />
                        ) : null}
                        <span className="ml-auto text-[10px] text-[#5d5d69]">
                          {project?.country?.code ?? "AF"}
                        </span>
                      </div>
                      <p className="mt-2 line-clamp-2 text-[13px] font-semibold leading-snug text-white">
                        {project?.name ?? t("landing2.previewProject")}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {(project?.technologies.slice(0, 2) ?? ["React", "API"]).map((tech) => (
                          <span
                            key={tech}
                            className="rounded-full border border-[#2c2c35] px-2 py-0.5 text-[10px] text-[#a1a1aa]"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 rounded-xl border border-dashed border-[#2c2c35] px-3 py-2 text-center text-[10px] text-[#6f6f7d]">
                  {t("landing2.previewHint")}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mx-auto w-full max-w-[1120px] px-4 pb-6 sm:px-6">
          <div className="flex flex-wrap items-center gap-3 text-xs text-[#6f6f7d]">
            <span className="inline-flex items-center gap-2">
              <span className="flex -space-x-2">
                {["A", "K", "N", "B"].map((letter, index) => (
                  <span
                    key={letter}
                    className={cn(
                      "grid size-6 place-items-center rounded-full border border-[#0f0f12] text-[9px] font-bold text-white",
                      ["bg-[#7c3aed]", "bg-[#0891b2]", "bg-[#db2777]", "bg-[#059669]"][index],
                    )}
                  >
                    {letter}
                  </span>
                ))}
              </span>
              {t("landing2.trust")}
            </span>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------- Stats */}
      <section className="mx-auto w-full max-w-[1120px] px-4 py-16 sm:px-6">
        <p className="text-center text-xs uppercase tracking-[0.18em] text-[#5d5d69]">{t("landing2.statsLabel")}</p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(({ label, value, icon: Icon }) => (
            <div
              key={label}
              className="rounded-2xl border border-[#26262e] bg-[#141419] p-6 text-center transition hover:border-[#3d3d49]"
            >
              <Icon className="mx-auto size-5 text-[#8b5cf6]" aria-hidden="true" />
              <p className="font-display mt-3 text-[28px] font-bold leading-none">{value}</p>
              <p className="mt-2 text-[13px] text-[#a1a1aa]">{label}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {STACKS.map((stack) => (
            <div
              key={stack}
              className="flex h-14 items-center justify-center rounded-xl border border-[#232329] bg-[#121217] text-sm font-medium text-[#8f8f9c] transition hover:border-[#3d3d49] hover:text-white"
            >
              {stack}
            </div>
          ))}
        </div>
      </section>

      {/* ----------------------------------------------------------- App tabs */}
      <section className="relative mx-auto w-full max-w-[1120px] px-4 py-20 sm:px-6">
        <h2 className="font-display mx-auto max-w-2xl text-center text-[30px] font-extrabold tracking-[-0.03em] sm:text-[40px]">
          {t("landing2.appTitle")}
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-center text-[15px] leading-relaxed text-[#a1a1aa]">
          {t("landing2.appSubtitle")}
        </p>

        <div className="mt-9 flex flex-wrap items-center justify-center gap-2">
          {TABS.map(({ key, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={cn(
                "inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition",
                tab === key
                  ? "border-[#8b5cf6] bg-[#1d1630] text-white"
                  : "border-[#26262e] bg-[#141419] text-[#a1a1aa] hover:border-[#3d3d49] hover:text-white",
              )}
              aria-pressed={tab === key}
            >
              <Icon className="size-4" aria-hidden="true" />
              {t(`landing2.tab_${key}`)}
            </button>
          ))}
        </div>

        <div className="relative mt-10 overflow-hidden rounded-[24px] border border-[#2c2c35] bg-gradient-to-b from-[#1a1425] via-[#121217] to-[#0f0f12] p-3 sm:p-5">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-[#7c3aed] opacity-20 blur-3xl" aria-hidden="true" />
          <div className="relative rounded-[16px] border border-[#2a2a33] bg-[#0f0f12] p-4 sm:p-6">
            <div className="grid gap-4 md:grid-cols-[190px_1fr_220px]">
              <div className="hidden space-y-1.5 md:block">
                {[
                  { label: t("landing2.sideHome"), active: true },
                  { label: t("landing2.sideFeed") },
                  { label: t("landing2.sideProblems") },
                  { label: t("landing2.sideReports") },
                  { label: t("landing2.sideCountries") },
                  { label: t("landing2.sideMissions") },
                ].map((item) => (
                  <div
                    key={item.label}
                    className={cn(
                      "flex items-center gap-2 rounded-lg px-2.5 py-2 text-[12px]",
                      item.active ? "bg-[#1d1d25] text-white" : "text-[#8f8f9c]",
                    )}
                  >
                    <span className="size-1.5 rounded-full bg-current opacity-60" />
                    {item.label}
                  </div>
                ))}
              </div>

              <div className="space-y-2.5">
                {(projects.length > 0 ? projects.slice(0, 3) : [null, null, null]).map((project, index) => (
                  <div key={project?.id ?? index} className="rounded-xl border border-[#26262e] bg-[#15151a] p-3.5">
                    <div className="flex items-center gap-2 text-[11px] text-[#8f8f9c]">
                      <span className="size-5 rounded-full bg-gradient-to-br from-[#8b5cf6] to-[#4c1d95]" />
                      {project ? `@${project.creator.username}` : "@community"}
                      <span className="ml-auto">{project?.country?.flag_emoji ?? "🌍"}</span>
                    </div>
                    <p className="mt-2 text-[13px] font-semibold leading-snug text-white">
                      {project?.name ?? t("landing2.previewProject")}
                    </p>
                    <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-[#8f8f9c]">
                      {project?.description ?? t("landing2.previewText")}
                    </p>
                  </div>
                ))}
              </div>

              <div className="hidden space-y-3 md:block">
                <div className="rounded-xl border border-[#26262e] bg-[#15151a] p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#5d5d69]">
                    {t("landing2.trending")}
                  </p>
                  <ul className="mt-2 space-y-2 text-[11px] text-[#a1a1aa]">
                    <li>• Mobile money sandbox</li>
                    <li>• KYC sans friction</li>
                    <li>• APIs de cartographie</li>
                  </ul>
                </div>
                <div className="rounded-xl border border-[#26262e] bg-[#15151a] p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#5d5d69]">
                    {t("landing2.suggested")}
                  </p>
                  <div className="mt-2 flex items-center gap-2 text-[11px] text-[#a1a1aa]">
                    <span className="size-6 rounded-full bg-[#312e81]" />
                    @amina-dev
                  </div>
                  <div className="mt-2 flex items-center gap-2 text-[11px] text-[#a1a1aa]">
                    <span className="size-6 rounded-full bg-[#831843]" />
                    @kwame
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------- Features */}
      <section className="border-y border-[#1c1c22] bg-[#0c0c10]">
        <div className="mx-auto grid w-full max-w-[1120px] gap-10 px-4 py-16 sm:px-6 md:grid-cols-3">
          {features.map(({ title, text, icon: Icon }) => (
            <div key={title}>
              <span className="grid size-10 place-items-center rounded-xl border border-[#2c2c35] bg-[#15151a]" aria-hidden="true">
                <Icon className="size-5 text-[#c4b5fd]" />
              </span>
              <h3 className="font-display mt-4 text-[17px] font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#8f8f9c]">{text}</p>
            </div>
          ))}
        </div>
        <div className="pb-16 text-center">
          <Link to="/login" className="btn-light h-12 px-6 text-[15px]">
            {t("landing2.getStarted")}
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </div>
      </section>

      {/* ------------------------------------------------------------- Steps */}
      <section className="mx-auto w-full max-w-[1120px] px-4 py-20 sm:px-6">
        <h2 className="font-display text-[28px] font-extrabold tracking-[-0.03em] sm:text-[34px]">
          {t("landing.howTitle")}
        </h2>
        <p className="mt-2 text-sm text-[#8f8f9c]">{t("landing.howSubtitle")}</p>
        <ol className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, index) => (
            <li key={step.title} className="relative rounded-2xl border border-[#26262e] bg-[#141419] p-5">
              <span className="grid size-8 place-items-center rounded-full bg-gradient-to-br from-[#8b5cf6] to-[#6d28d9] text-xs font-bold text-white">
                {index + 1}
              </span>
              <h3 className="mt-3 text-sm font-semibold text-white">{step.title}</h3>
              <p className="mt-1.5 text-[13px] leading-relaxed text-[#8f8f9c]">{step.text}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* --------------------------------------------------------------- CTA */}
      <section className="mx-auto w-full max-w-[1120px] px-4 pb-24 sm:px-6">
        <div className="relative overflow-hidden rounded-[24px] border border-[#2c2c35] bg-gradient-to-br from-[#1b1230] via-[#141019] to-[#0f0f12] px-6 py-14 text-center sm:px-12">
          <div className="pointer-events-none absolute -left-20 top-0 size-72 rounded-full bg-[#7c3aed] opacity-30 blur-[110px]" aria-hidden="true" />
          <div className="pointer-events-none absolute -right-10 bottom-0 size-72 rounded-full bg-[#db2777] opacity-20 blur-[110px]" aria-hidden="true" />
          <h2 className="font-display relative mx-auto max-w-xl text-[26px] font-extrabold tracking-[-0.02em] sm:text-[34px]">
            {t("landing.finalTitle")}
          </h2>
          <p className="relative mx-auto mt-3 max-w-lg text-sm leading-relaxed text-[#a1a1aa]">
            {t("landing.finalText")}
          </p>
          <Link to="/login" className="btn-light relative mt-8 h-12 px-6 text-[15px]">
            {t("landing2.ctaButton")}
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </div>
      </section>
    </div>
  );
}
