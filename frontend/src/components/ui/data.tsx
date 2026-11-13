import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

import { cn, initials } from "@/lib/utils";

type Tone = "primary" | "accent" | "highlight" | "neutral" | "danger";

const TONES: Record<Tone, string> = {
  primary: "bg-primary-50 text-primary-700 border-primary-100",
  accent: "bg-accent-50 text-accent-700 border-accent-200",
  highlight: "bg-highlight-50 text-highlight-600 border-highlight-100",
  neutral: "bg-slate-100 text-slate-700 border-slate-200",
  danger: "bg-red-50 text-red-700 border-red-200",
};

export function Badge({ children, tone = "neutral", className }: { children: ReactNode; tone?: Tone; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function DemoBadge({ show }: { show?: boolean }) {
  if (!show) return null;
  return <Badge tone="highlight">DEMO</Badge>;
}

export function Avatar({ name, src, size = 40 }: { name?: string | null; src?: string | null; size?: number }) {
  if (src) {
    return (
      <img
        src={src}
        alt={name ?? "avatar"}
        width={size}
        height={size}
        loading="lazy"
        className="rounded-full object-cover"
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <span
      aria-hidden="true"
      className="inline-flex items-center justify-center rounded-full bg-primary-100 font-semibold text-primary-700"
      style={{ width: size, height: size, fontSize: size * 0.36 }}
    >
      {initials(name)}
    </span>
  );
}

export function Card({ children, className, as: Tag = "div" }: { children: ReactNode; className?: string; as?: "div" | "section" | "article" }) {
  return <Tag className={cn("surface-card p-5", className)}>{children}</Tag>;
}

export function TechnologyTag({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-lg bg-primary-50 px-2 py-1 text-xs font-medium text-primary-700">{children}</span>
  );
}

const LEVEL_TONE: Record<string, Tone> = {
  newcomer: "neutral",
  contributor: "primary",
  confirmed: "accent",
  expert: "highlight",
};

export function ReputationBadge({ level, points, label }: { level: string; points: number; label?: string }) {
  return (
    <Badge tone={LEVEL_TONE[level] ?? "neutral"}>
      {label ?? level} · {points} pts
    </Badge>
  );
}

export function Tabs<T extends string>({
  tabs,
  active,
  onChange,
}: {
  tabs: Array<{ id: T; label: string; count?: number }>;
  active: T;
  onChange: (id: T) => void;
}) {
  return (
    <div role="tablist" className="flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          type="button"
          aria-selected={active === tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
            active === tab.id ? "bg-white text-primary-700 shadow-sm" : "text-muted hover:text-primary-700",
          )}
        >
          {tab.label}
          {typeof tab.count === "number" ? <span className="ml-1.5 text-xs text-muted">{tab.count}</span> : null}
        </button>
      ))}
    </div>
  );
}

export function SearchBar({
  value,
  onChange,
  placeholder,
  onSubmit,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onSubmit?: () => void;
  label: string;
}) {
  return (
    <form
      role="search"
      className="relative w-full"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit?.();
      }}
    >
      <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
      <input
        type="search"
        value={value}
        aria-label={label}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm placeholder:text-slate-400 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-100"
      />
    </form>
  );
}

export function Pagination({
  page,
  pageSize,
  total,
  onChange,
  labels,
}: {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
  labels: { previous: string; next: string; page: string };
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <nav className="mt-6 flex items-center justify-between gap-3 text-sm" aria-label="pagination">
      <button
        type="button"
        onClick={() => onChange(Math.max(1, page - 1))}
        disabled={page <= 1}
        className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 disabled:opacity-50"
      >
        <ChevronLeft className="size-4" aria-hidden="true" /> {labels.previous}
      </button>
      <span className="text-muted">
        {labels.page} {page} / {pages}
      </span>
      <button
        type="button"
        onClick={() => onChange(Math.min(pages, page + 1))}
        disabled={page >= pages}
        className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 disabled:opacity-50"
      >
        {labels.next} <ChevronRight className="size-4" aria-hidden="true" />
      </button>
    </nav>
  );
}
