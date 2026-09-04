import type { PointSourceSchema } from "@/api/generated/model";

type SourceMarkerProps = {
  source: PointSourceSchema;
};

export function SourceMarker({ source }: Readonly<SourceMarkerProps>) {
  const snrLabel = source.snr.toFixed(1);
  const label = `Fuente ${source.rank}, SNR ${snrLabel}`;

  return (
    <img
      alt={label}
      title={label}
      src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
      className="pointer-events-auto block size-4 rounded-full border-2 border-primary bg-primary/30 shadow-sm ring-2 ring-background"
    />
  );
}
