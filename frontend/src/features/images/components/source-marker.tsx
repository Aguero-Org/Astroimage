type MarkerSource = {
  xcentroid: number;
  ycentroid: number;
  snr: number;
  rank: number;
  object_type?: string;
};

type SourceMarkerProps = {
  source: MarkerSource;
};

export function SourceMarker({ source }: SourceMarkerProps) {
  const snrLabel = source.snr.toFixed(1);
  const isExtended = source.object_type === "extended";
  const typeLabel = isExtended ? "Extendida" : "Fuente";
  const label = `${typeLabel} ${source.rank}, SNR ${snrLabel}`;

  if (isExtended) {
    return (
      <span
        role="img"
        aria-label={label}
        title={label}
        className="pointer-events-auto block size-4 rotate-45 border-2 border-amber-500 bg-amber-400/30 shadow-sm ring-2 ring-background"
      />
    );
  }

  return (
    <span
      role="img"
      aria-label={label}
      title={label}
      className="pointer-events-auto block size-4 rounded-full border-2 border-primary bg-primary/30 shadow-sm ring-2 ring-background"
    />
  );
}
