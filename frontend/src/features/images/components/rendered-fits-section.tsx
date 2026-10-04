import { useEffect, useState } from "react";
import type {
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import { BrandLoader } from "@/components/brand-loader";
import { ExtendedSourceMarkers } from "@/features/images/components/extended-source-markers";
import { FitsImageViewer } from "@/features/images/components/fits-image-viewer";
import { SourceMarkers } from "@/features/images/components/source-markers";
import { formatQueryError } from "@/features/images/format-query-error";

export function RenderedFitsSection({
  isPending,
  isError,
  error,
  rendered,
  label,
  pointSources,
  extendedSources,
  gaiaPointIds,
  gaiaExtendedIds,
  selectedId,
  selectedExtendedId,
  onSelectSource,
}: Readonly<{
  isPending: boolean;
  isError: boolean;
  error: unknown;
  rendered: unknown;
  label: string;
  pointSources: PointSourceSchema[];
  extendedSources: ExtendedSourceSchema[];
  gaiaPointIds: ReadonlySet<number>;
  gaiaExtendedIds: ReadonlySet<number>;
  selectedId?: number;
  selectedExtendedId?: number;
  onSelectSource?: (source: PointSourceSchema | ExtendedSourceSchema) => void;
}>) {
  const objectUrl = useObjectUrl(isBlob(rendered) ? rendered : undefined);
  if (isPending) {
    return (
      <div
        data-testid="render-loading"
        className="flex h-full w-full items-center justify-center"
      >
        <BrandLoader
          className="rounded-lg bg-background px-4 py-3 text-foreground shadow-lg ring-1 ring-border dark:bg-card"
          label="Renderizando imagen…"
        />
      </div>
    );
  }
  if (isError) {
    return (
      <p
        data-testid="render-error"
        className="flex h-full items-center justify-center p-8 text-sm text-destructive"
      >
        Error al renderizar: {formatQueryError(error)}
      </p>
    );
  }
  if (objectUrl) {
    return (
      <FitsImageViewer
        imageUrl={objectUrl}
        label={label}
        className="h-full rounded-none border-0"
      >
        <ExtendedSourceMarkers
          sources={extendedSources}
          selectedId={selectedExtendedId}
          gaiaMatchedIds={gaiaExtendedIds}
          onSelect={onSelectSource}
        />
        <SourceMarkers
          sources={pointSources}
          selectedId={selectedId}
          gaiaMatchedIds={gaiaPointIds}
          onSelect={onSelectSource}
        />
      </FitsImageViewer>
    );
  }
  return (
    <p className="flex h-full items-center justify-center p-8 text-sm text-muted-foreground">
      No hay imagen disponible.
    </p>
  );
}

function isBlob(value: unknown): value is Blob {
  // Node's fetch Blob and jsdom's Blob fail `instanceof` across each other.
  return Object.prototype.toString.call(value) === "[object Blob]";
}

function useObjectUrl(blob: Blob | undefined): string | undefined {
  const [url, setUrl] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!blob) {
      setUrl(undefined);
      return;
    }
    const next = URL.createObjectURL(blob);
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [blob]);

  return url;
}
