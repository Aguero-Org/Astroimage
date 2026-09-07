import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useGetImageInfo } from "@/api/generated/hub/hub";
import type {
  DetectSourcesParams,
  PointSourceSchema,
} from "@/api/generated/model";
import { useRenderFitsImage } from "@/api/generated/render/render";
import { useDetectSources } from "@/api/generated/sources/sources";
import { Skeleton } from "@/components/ui/skeleton";
import { FitsImageViewer } from "@/features/images/components/fits-image-viewer";
import { SourceDetectionForm } from "@/features/images/components/source-detection-form";
import { DEFAULT_SOURCE_DETECTION_PARAMS } from "@/features/images/source-detection";

export const Route = createFileRoute("/image/$recordId")({
  component: ImageDetailPage,
});

function ImageDetailPage() {
  const { recordId } = Route.useParams();

  const renderQuery = useRenderFitsImage(recordId);
  const infoQuery = useGetImageInfo(recordId);
  const [detectionParams, setDetectionParams] = useState<DetectSourcesParams>(
    DEFAULT_SOURCE_DETECTION_PARAMS,
  );
  const sourcesQuery = useDetectSources(recordId, detectionParams);
  const sourceName =
    infoQuery.data?.status === 200
      ? infoQuery.data.data.source_name
      : undefined;
  const pointSources =
    sourcesQuery.data?.status === 200
      ? (sourcesQuery.data.data.point_sources ?? [])
      : [];
  const detectionSummary =
    sourcesQuery.data?.status === 200
      ? sourcesQuery.data.data.summary
      : undefined;

  const blob =
    renderQuery.data?.status === 200
      ? (renderQuery.data.data as Blob)
      : undefined;
  const objectUrl = useObjectUrl(blob);

  return (
    <main className="relative h-svh w-full overflow-hidden bg-black">
      <RenderedFitsSection
        isPending={renderQuery.isPending}
        isError={renderQuery.isError}
        error={renderQuery.error}
        objectUrl={objectUrl}
        label={sourceName ?? `Render FITS ${recordId}`}
        pointSources={pointSources}
      />

      <header className="pointer-events-none absolute top-16 left-4 z-20 max-w-[min(100%-2rem,28rem)] sm:left-8">
        <h1
          data-testid="image-detail-title"
          className="text-2xl font-semibold text-white drop-shadow-[0_1px_8px_rgba(0,0,0,0.8)]"
        >
          {sourceName ?? recordId}
        </h1>
      </header>

      <aside className="pointer-events-none absolute bottom-4 left-4 z-20 w-[min(100%-2rem,24rem)] sm:bottom-8 sm:left-8 sm:w-[28rem]">
        <div className="pointer-events-auto max-h-[min(50vh,28rem)] overflow-y-auto rounded-xl border border-white/15 bg-background/80 p-4 shadow-lg backdrop-blur-md">
          <h2 className="text-sm font-medium">Detección de fuentes</h2>
          <p className="mb-3 text-xs text-muted-foreground">
            Ajusta los parámetros y lanza el análisis. Los puntos se marcan
            sobre la imagen.
          </p>
          <SourceDetectionForm
            isPending={sourcesQuery.isFetching}
            onSubmit={setDetectionParams}
          />
          {sourcesQuery.isError ? (
            <p
              data-testid="detect-error"
              className="mt-2 text-sm text-destructive"
            >
              Error al detectar fuentes: {formatQueryError(sourcesQuery.error)}
            </p>
          ) : null}
          {detectionSummary ? (
            <p
              data-testid="detect-summary"
              className="mt-2 text-sm text-muted-foreground"
            >
              {detectionSummary.point_count} puntuales,{" "}
              {detectionSummary.extended_count} extendidas
            </p>
          ) : null}
        </div>
      </aside>
    </main>
  );
}

function RenderedFitsSection({
  isPending,
  isError,
  error,
  objectUrl,
  label,
  pointSources,
}: Readonly<{
  isPending: boolean;
  isError: boolean;
  error: unknown;
  objectUrl: string | undefined;
  label: string;
  pointSources: PointSourceSchema[];
}>) {
  if (isPending) {
    return (
      <div
        data-testid="render-loading"
        className="flex h-full w-full flex-col items-center justify-center gap-2"
      >
        <Skeleton className="h-full w-full rounded-none" />
        <p className="absolute text-sm text-muted-foreground">
          Renderizando imagen…
        </p>
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
        pointSources={pointSources}
        className="h-full rounded-none border-0"
      />
    );
  }
  return (
    <p className="flex h-full items-center justify-center p-8 text-sm text-muted-foreground">
      No hay imagen disponible.
    </p>
  );
}

function formatQueryError(error: unknown): string {
  return error instanceof Error ? error.message : "error desconocido";
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
