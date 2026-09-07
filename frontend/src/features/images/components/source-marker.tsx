import type { PointSourceSchema } from "@/api/generated/model";
import { cn } from "@/lib/utils";

type SourceMarkerProps = {
  source: PointSourceSchema;
  selected?: boolean;
  onSelect?: (source: PointSourceSchema) => void;
};

export function SourceMarker({
  source,
  selected = false,
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
      title={label}
      className={cn(
        "pointer-events-auto block size-4 cursor-pointer rounded-full border-2 bg-primary/30 shadow-sm ring-2",
        selected
          ? "border-accent ring-accent"
          : "border-primary ring-background",
      )}
      onClick={() => {
        onSelect?.(source);
      }}
    />
  );
}
