import type { PointSourceSchema } from "@/api/generated/model";
import { cn } from "@/lib/utils";

function markerRing(selected: boolean, gaiaMatch: boolean): string {
  if (selected) {
    return "ring-accent";
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
  onSelect?: (source: PointSourceSchema) => void;
};

export function SourceMarker({
  source,
  selected = false,
  gaiaMatch = false,
  onSelect,
}: Readonly<SourceMarkerProps>) {
  const snrLabel = source.snr.toFixed(1);
  const label = `Fuente ${source.rank}, SNR ${snrLabel}`;

  return (
    <button
      type="button"
      data-testid="source-marker"
      aria-label={label}
      aria-pressed={selected}
      data-gaia-match={gaiaMatch ? "true" : "false"}
      title={label}
      className={cn(
        "pointer-events-auto block size-4 cursor-pointer rounded-full border-2 shadow-sm ring-2",
        gaiaMatch ? "border-gaia bg-gaia/40" : "border-primary bg-primary/30",
        markerRing(selected, gaiaMatch),
      )}
      onClick={() => {
        onSelect?.(source);
      }}
    />
  );
}
