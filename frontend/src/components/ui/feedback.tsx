import { useEffect, type ReactNode } from "react";
import { AlertTriangle, Inbox, X } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

export function Spinner({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-sm text-muted" role="status">
      <span className="size-5 animate-spin rounded-full border-2 border-primary-200 border-t-primary-700" aria-hidden="true" />
      {label}
    </div>
  );
}

export function SkeletonList({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="surface-card flex gap-4 p-5">
          <div className="size-12 animate-pulse rounded-full bg-slate-200" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-1/3 animate-pulse rounded bg-slate-200" />
            <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
            <div className="h-3 w-2/3 animate-pulse rounded bg-slate-100" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="surface-card flex flex-col items-center gap-3 p-10 text-center">
      <span className="rounded-2xl bg-primary-50 p-3 text-primary-600" aria-hidden="true">
        {icon ?? <Inbox className="size-6" />}
      </span>
      <h2 className="text-base font-semibold text-primary-800">{title}</h2>
      {description ? <p className="max-w-md text-sm text-muted">{description}</p> : null}
      {action}
    </div>
  );
}

export function ErrorState({ message, retryLabel, onRetry }: { message: string; retryLabel: string; onRetry?: () => void }) {
  return (
    <div className="surface-card flex flex-col items-center gap-3 border-red-200 p-8 text-center" role="alert">
      <span className="rounded-2xl bg-red-50 p-3 text-red-600" aria-hidden="true">
        <AlertTriangle className="size-6" />
      </span>
      <p className="text-sm text-red-700">{message}</p>
      {onRetry ? (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          {retryLabel}
        </Button>
      ) : null}
    </div>
  );
}

export function Alert({ tone = "info", children }: { tone?: "info" | "success" | "error"; children: ReactNode }) {
  const tones = {
    info: "border-primary-100 bg-primary-50 text-primary-800",
    success: "border-accent-200 bg-accent-50 text-accent-700",
    error: "border-red-200 bg-red-50 text-red-700",
  } as const;
  return <div className={cn("rounded-xl border px-4 py-3 text-sm", tones[tone])}>{children}</div>;
}

export function Modal({
  open,
  onClose,
  title,
  children,
  closeLabel,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  closeLabel: string;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-primary-900/50 p-0 sm:items-center sm:p-6">
      <button type="button" aria-label={closeLabel} className="absolute inset-0 cursor-default" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative z-10 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white p-6 shadow-xl sm:rounded-2xl"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold text-primary-800">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={closeLabel}
            className="rounded-lg p-1.5 text-muted hover:bg-slate-100"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
        </div>
        {children}
        {footer ? <div className="mt-6 flex justify-end gap-2">{footer}</div> : null}
      </div>
    </div>
  );
}
