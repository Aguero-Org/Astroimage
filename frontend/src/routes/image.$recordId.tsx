import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useGetImageInfo } from "@/api/generated/hub/hub";
import type {
  DetectSourcesParams,
  PointSourceSchema,
} from "@/api/generated/model";
import { useRenderFitsImage } from "@/api/generated/render/render";
import { useDetectSources } from "@/api/generated/sources/sources";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
    <main className="flex min-h-svh justify-center p-6">
      <Card className="w-full max-w-6xl">
        <CardHeader>
          <CardTitle className="text-2xl">{sourceName ?? recordId}</CardTitle>
        </CardHeader>

        <CardContent className="flex flex-col gap-6">
          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-medium">Imagen renderizada</h2>
            <RenderedFitsSection
              isPending={renderQuery.isPending}
              isError={renderQuery.isError}
              error={renderQuery.error}
              objectUrl={objectUrl}
              label={sourceName ?? `Render FITS ${recordId}`}
              pointSources={pointSources}
            />
          </section>
          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-medium">Detección de fuentes</h2>
            <p className="text-sm text-muted-foreground">
              Ajusta los parámetros y lanza el análisis. Los puntos detectados
              se marcan sobre la imagen.
            </p>
            <SourceDetectionForm
              isPending={sourcesQuery.isFetching}
              onSubmit={setDetectionParams}
            />
            {sourcesQuery.isError ? (
              <p className="text-sm text-destructive">
                Error al detectar fuentes:{" "}
                {formatQueryError(sourcesQuery.error)}
              </p>
            ) : null}
            {detectionSummary ? (
              <p className="text-sm text-muted-foreground">
                {detectionSummary.point_count} puntuales,{" "}
                {detectionSummary.extended_count} extendidas
              </p>
            ) : null}
          </section>
        </CardContent>
      </Card>
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
      <div className="flex flex-col gap-2">
        <Skeleton className="h-[min(70vh,40rem)] w-full rounded-xl" />
        <p className="text-sm text-muted-foreground">Renderizando imagen…</p>
      </div>
    );
  }
  if (isError) {
    return (
      <p className="text-sm text-destructive">
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
      />
    );
  }
  return (
    <p className="text-sm text-muted-foreground">No hay imagen disponible.</p>
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
