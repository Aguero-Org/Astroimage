import { useEffect, useState } from "react";
import type {
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import { Skeleton } from "@/components/ui/skeleton";
import { ExtendedSourceMarkers } from "@/features/images/components/extended-source-markers";
import { FitsImageViewer } from "@/features/images/components/fits-image-viewer";
import { SourceMarkers } from "@/features/images/components/source-markers";
import { formatQueryError } from "@/features/images/format-query-error";

const SKELETON_TOOLS = [0, 1, 2, 3];

export type SourceOverlays = {
  pointSources: PointSourceSchema[];
  extendedSources: ExtendedSourceSchema[];
  gaiaPointIds: ReadonlySet<number>;
  gaiaExtendedIds: ReadonlySet<number>;
  selectedPointId?: number;
  selectedExtendedId?: number;
  onSelect?: (source: PointSourceSchema | ExtendedSourceSchema) => void;
};

function RenderSkeleton() {
  return (
    <output
      data-testid="render-loading"
      aria-label="Renderizando imagen…"
      className="block relative h-full w-full overflow-hidden bg-black"
    >
      <span className="sr-only">Renderizando imagen…</span>
      <Skeleton
        className="absolute inset-0 rounded-none bg-white/5"
        aria-hidden
      />
      <div
        className="absolute top-16 right-3 flex gap-1 rounded-lg border border-sidebar-border bg-sidebar p-1 shadow-sm sm:top-20 sm:right-8"
        aria-hidden
      >
        {SKELETON_TOOLS.map((tool) => (
          <Skeleton key={tool} className="size-9 rounded-md" />
        ))}
      </div>
      <Skeleton
        className="absolute right-3 bottom-3 h-28 w-40 rounded-md bg-white/10 sm:right-8 sm:bottom-8"
        aria-hidden
      />
    </output>
  );
}

export function RenderedFitsSection({
  isPending,
  isError,
  error,
  rendered,
  imageUrl,
  label,
  sources,
}: Readonly<{
  isPending: boolean;
  isError: boolean;
  error: unknown;
  rendered: unknown;
  imageUrl: string | undefined;
  label: string;
  sources: SourceOverlays;
}>) {
  if (isPending) {
    return <RenderSkeleton />;
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
  if (isBlob(rendered) && imageUrl === undefined) {
    return <RenderSkeleton />;
  }
  if (imageUrl) {
    return (
      <FitsImageViewer
        imageUrl={imageUrl}
        label={label}
        className="h-full rounded-none border-0"
      >
        <ExtendedSourceMarkers
          sources={sources.extendedSources}
          selectedId={sources.selectedExtendedId}
          gaiaMatchedIds={sources.gaiaExtendedIds}
          onSelect={sources.onSelect}
        />
        <SourceMarkers
          sources={sources.pointSources}
          selectedId={sources.selectedPointId}
          gaiaMatchedIds={sources.gaiaPointIds}
          onSelect={sources.onSelect}
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

export function useRenderedObjectUrl(rendered: unknown): string | undefined {
  return useObjectUrl(isBlob(rendered) ? rendered : undefined);
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
