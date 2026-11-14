import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";

export function Logo({ compact = false, light = false }: { compact?: boolean; light?: boolean }) {
  return (
    <Link to="/" className="inline-flex items-center gap-2.5" aria-label="AfriDev Hub">
      <span className="relative grid size-9 place-items-center overflow-hidden rounded-[10px] bg-gradient-to-br from-[#8b5cf6] via-[#7c3aed] to-[#4c1d95] text-[11px] font-extrabold tracking-tight text-white shadow-[0_0_0_1px_rgba(255,255,255,0.08)_inset]">
        AD
      </span>
      {!compact ? (
        <span className={cn("flex items-baseline leading-none", light ? "text-white" : "text-primary-800")}>
          <span className="font-display text-[17px] font-extrabold tracking-tight">afridev</span>
          <span className={cn("font-display text-[17px] font-medium", light ? "text-[#9b9ba6]" : "text-muted")}>.hub</span>
        </span>
      ) : null}
    </Link>
  );
}
