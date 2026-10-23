import type { PointSourceSchema } from "@/api/generated/model";
import { cn } from "@/lib/utils";
import { SimbadMatchBadge } from "./simbad-match-badge";

function markerRing(
  selected: boolean,
  gaiaMatch: boolean,
  simbadMatch: boolean,
): string {
  if (selected) {
    return "ring-accent";
  }
  if (simbadMatch) {
    return "ring-simbad";
  }
  if (gaiaMatch) {
    return "ring-gaia";
  }
  return "ring-background";
}

type SourceMarkerProps = {
  source: PointSourceSchema;
  selected?: boolean;
  gaiaMatch?: boolean;
  simbadMatch?: boolean;
  pulseKey?: number;
  onSelect?: (source: PointSourceSchema) => void;
};

export function SourceMarker({
  source,
  selected = false,
  gaiaMatch = false,
  simbadMatch = false,
  pulseKey,
  onSelect,
}: Readonly<SourceMarkerProps>) {
  const snrLabel = source.snr.toFixed(1);
  const label = `Fuente ${source.rank}, SNR ${snrLabel}${simbadMatch ? ", SIMBAD" : ""}`;

  return (
    <button
      key={pulseKey}
      type="button"
      data-testid="source-marker"
      aria-label={label}
      aria-pressed={selected}
      data-gaia-match={gaiaMatch ? "true" : "false"}
      data-simbad-match={simbadMatch ? "true" : "false"}
      title={label}
      className={cn(
        "pointer-events-auto relative block size-4 cursor-pointer rounded-full border-2 shadow-sm ring-2",
        simbadMatch
          ? "border-simbad bg-simbad/40"
          : gaiaMatch
            ? "border-gaia bg-gaia/40"
            : "border-primary bg-primary/30",
        markerRing(selected, gaiaMatch, simbadMatch),
        pulseKey !== undefined && "source-focus-pulse",
      )}
      onClick={() => {
        onSelect?.(source);
      }}
    >
      {simbadMatch ? (
        <SimbadMatchBadge className="-top-1.5 -right-1.5" />
      ) : null}
    </button>
  );
}
