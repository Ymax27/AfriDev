import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";

export function Logo({ compact = false, light = false }: { compact?: boolean; light?: boolean }) {
  return (
    <Link to="/" className="inline-flex items-center gap-2" aria-label="AfriDev Hub">
      <span className="grid size-9 place-items-center rounded-xl bg-primary-700 text-sm font-bold text-white">
        AD
      </span>
      {!compact ? (
        <span className={cn("flex flex-col leading-none", light ? "text-white" : "text-primary-800")}>
          <span className="text-sm font-semibold">AfriDev Hub</span>
          <span className={cn("text-[10px] font-medium tracking-wide", light ? "text-primary-100" : "text-muted")}>
            Show. Solve. Prove.
          </span>
        </span>
      ) : null}
    </Link>
  );
}
