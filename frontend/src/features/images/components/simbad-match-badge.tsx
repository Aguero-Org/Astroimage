import { cn } from "@/lib/utils";

type SimbadMatchBadgeProps = {
  className?: string;
};

export function SimbadMatchBadge({
  className,
}: Readonly<SimbadMatchBadgeProps>) {
  return (
    <span
      data-testid="simbad-match-badge"
      aria-hidden="true"
      title="Coincide con SIMBAD"
      className={cn(
        "pointer-events-none absolute grid size-3.5 place-items-center rounded-full border border-background bg-simbad text-[8px] font-bold leading-none text-primary-foreground shadow-sm",
        className,
      )}
    >
      S
    </span>
  );
}
