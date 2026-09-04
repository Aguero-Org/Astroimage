import type { PointSourceSchema } from "@/api/generated/model";

type SourceMarkerProps = {
  source: PointSourceSchema;
};

export function SourceMarker({ source }: SourceMarkerProps) {
  const snrLabel = source.snr.toFixed(1);
  const label = `Fuente ${source.rank}, SNR ${snrLabel}`;

  return (
    <span
      role="img"
      aria-label={label}
      title={label}
      className="pointer-events-auto block size-4 rounded-full border-2 border-primary bg-primary/30 shadow-sm ring-2 ring-background"
    />
  );
}
