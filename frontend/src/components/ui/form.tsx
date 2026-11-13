import { forwardRef, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";
import type { Country } from "@/types/api";

const FIELD_BASE =
  "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-ink placeholder:text-slate-400 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-100 disabled:bg-slate-50";

export function Label({ htmlFor, children, hint }: { htmlFor?: string; children: ReactNode; hint?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-primary-800">
      {children}
      {hint ? <span className="ml-1 font-normal text-muted">({hint})</span> : null}
    </label>
  );
}

interface FieldProps {
  label?: string;
  hint?: string;
  error?: string;
  htmlFor?: string;
  children: ReactNode;
  className?: string;
}

export function Field({ label, hint, error, htmlFor, children, className }: FieldProps) {
  return (
    <div className={cn("w-full", className)}>
      {label ? <Label htmlFor={htmlFor} hint={hint}>{label}</Label> : null}
      {children}
      {error ? <p className="mt-1 text-xs text-red-600">{error}</p> : null}
    </div>
  );
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => <input ref={ref} className={cn(FIELD_BASE, className)} {...props} />,
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, rows = 4, ...props }, ref) => (
    <textarea ref={ref} rows={rows} className={cn(FIELD_BASE, "resize-y", className)} {...props} />
  ),
);
Textarea.displayName = "Textarea";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select ref={ref} className={cn(FIELD_BASE, "appearance-none pr-8", className)} {...props}>
      {children}
    </select>
  ),
);
Select.displayName = "Select";

interface CountrySelectorProps {
  countries: Country[];
  value?: string;
  onChange: (code: string) => void;
  id?: string;
  includeAll?: boolean;
  allLabel?: string;
  language?: string;
  className?: string;
}

export function CountrySelector({
  countries,
  value,
  onChange,
  id,
  includeAll = false,
  allLabel = "Tous",
  language = "fr",
  className,
}: CountrySelectorProps) {
  return (
    <Select
      id={id}
      value={value ?? ""}
      onChange={(event) => onChange(event.target.value)}
      className={className}
      aria-label="country"
    >
      {includeAll ? <option value="">{allLabel}</option> : <option value="">—</option>}
      {countries.map((country) => (
        <option key={country.code} value={country.code}>
          {language === "fr" ? country.name_fr : country.name}
        </option>
      ))}
    </Select>
  );
}
