import { keepPreviousData } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useGetImageInfo } from "@/api/generated/hub/hub";
import type {
  ExtendedSourceSchema,
  GaiaMatchSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import {
  useRenderFitsHistogram,
  useRenderFitsImage,
} from "@/api/generated/render/render";
import { useDetectSources } from "@/api/generated/sources/sources";
import { HelpHint } from "@/components/ui/help-hint";
import { Skeleton } from "@/components/ui/skeleton";
import { ExtendedSourceMarkers } from "@/features/images/components/extended-source-markers";
import { FitsImageViewer } from "@/features/images/components/fits-image-viewer";
import {
  GaiaCrossMatch,
  gaiaMatchedIds,
  gaiaMatchFor,
} from "@/features/images/components/gaia-cross-match";
import { HduSelector } from "@/features/images/components/hdu-selector";
import { ImageArchive } from "@/features/images/components/image-archive";
import { ImageInspector } from "@/features/images/components/image-inspector";
import { PixelHistogram } from "@/features/images/components/pixel-histogram";
import { RenderViewForm } from "@/features/images/components/render-view-form";
import { SourceDetectionForm } from "@/features/images/components/source-detection-form";
import { SourceMarkers } from "@/features/images/components/source-markers";
import { SourceSelection } from "@/features/images/components/source-selection";
import {
  DEFAULT_IMAGE_WORKSPACE,
  type ImageWorkspaceUi,
} from "@/features/images/image-workspace";
import { rememberLastImageRecord } from "@/features/images/last-record";
import { followOnQueriesEnabled } from "@/features/images/workspace-queries";

const DEFAULT_DOCUMENT_TITLE = "Astroimage 🌌";

export const Route = createFileRoute("/image/$recordId/{-$slug}")({
  component: ImageDetailPage,
});

function ImageDetailPage() {
  const { recordId, slug } = Route.useParams();

  useEffect(() => {
    rememberLastImageRecord(recordId, slug);
  }, [recordId, slug]);

  const [workspace, setWorkspace] = useState<ImageWorkspaceUi>(
    DEFAULT_IMAGE_WORKSPACE,
  );
  const [gaiaMatches, setGaiaMatches] = useState<GaiaMatchSchema[]>([]);
  const { hdu, inspectorOpen, selectedSource, renderParams, detectionParams } =
    workspace;
  const renderQueryParams =
    hdu === null ? renderParams : { ...renderParams, hdu };
  const renderQuery = useRenderFitsImage(recordId, renderQueryParams, {
    query: { placeholderData: keepPreviousData },
  });
  const infoQuery = useGetImageInfo(recordId);
  const sourcesQueryParams =
    hdu === null ? detectionParams : { ...detectionParams, hdu };
  const followOnsEnabled = followOnQueriesEnabled(renderQuery);
  const sourcesQuery = useDetectSources(recordId, sourcesQueryParams, {
    query: { enabled: followOnsEnabled },
  });
  const histogramParams = hdu === null ? { bins: 64 } : { bins: 64, hdu };
  const histogramQuery = useRenderFitsHistogram(recordId, histogramParams, {
    query: { enabled: followOnsEnabled },
  });
  const imageInfo =
    infoQuery.data?.status === 200 ? infoQuery.data.data : undefined;
  const imageHdus = imageInfo?.hdus.images ?? [];

  useEffect(() => {
    const images = imageInfo?.hdus.images ?? [];
    if (images.length <= 1) {
      setWorkspace((current) => ({ ...current, hdu: null }));
      return;
    }
    setWorkspace((current) => {
      if (
        current.hdu !== null &&
        images.some((plane) => plane.index === current.hdu)
      ) {
        return current;
      }
      return {
        ...current,
        hdu: imageInfo?.hdus.selected ?? images[0]?.index ?? null,
      };
    });
  }, [imageInfo]);
  const sourceName = imageInfo?.source_name;
  const pageTitle = sourceName ?? slug ?? "Imagen";

  useEffect(() => {
    document.title = `${pageTitle} - Astroimage`;
    return () => {
      document.title = DEFAULT_DOCUMENT_TITLE;
    };
  }, [pageTitle]);
  const pointSources =
    sourcesQuery.data?.status === 200
      ? (sourcesQuery.data.data.point_sources ?? [])
      : [];
  const extendedSources =
    sourcesQuery.data?.status === 200
      ? (sourcesQuery.data.data.extended_sources ?? [])
      : [];
  const detectionSummary =
    sourcesQuery.data?.status === 200
      ? sourcesQuery.data.data.summary
      : undefined;
  const selectedPointId =
    selectedSource?.object_type === "point"
      ? selectedSource.source_id
      : undefined;
  const selectedExtendedId =
    selectedSource?.object_type === "extended"
      ? selectedSource.source_id
      : undefined;

  const blob =
    renderQuery.data?.status === 200
      ? (renderQuery.data.data as Blob)
      : undefined;
  const objectUrl = useObjectUrl(blob);

  useEffect(() => {
    if (recordId || detectionParams || hdu !== undefined) {
      setWorkspace((current) => ({ ...current, selectedSource: null }));
    }
  }, [recordId, detectionParams, hdu]);

  return (
    <main className="relative h-svh w-full overflow-hidden bg-black">
      <RenderedFitsSection
        isPending={renderQuery.isPending}
        isError={renderQuery.isError}
        error={renderQuery.error}
        objectUrl={objectUrl}
        label={sourceName ?? `Render FITS ${recordId}`}
        pointSources={pointSources}
        extendedSources={extendedSources}
        gaiaPointIds={gaiaMatchedIds(gaiaMatches, "point")}
        gaiaExtendedIds={gaiaMatchedIds(gaiaMatches, "extended")}
        selectedId={selectedPointId}
        selectedExtendedId={selectedExtendedId}
        onSelectSource={(source) => {
          setWorkspace((current) => ({
            ...current,
            selectedSource: source,
            inspectorOpen: true,
          }));
        }}
      />

      <ImageInspector
        title={
          <h1
            data-testid="image-detail-title"
            className="min-w-0 truncate text-2xl font-semibold text-white drop-shadow-[0_1px_8px_rgba(0,0,0,0.8)]"
          >
            {sourceName ?? recordId}
          </h1>
        }
        open={inspectorOpen}
        onOpenChange={(open) => {
          setWorkspace((current) => ({ ...current, inspectorOpen: open }));
        }}
        selectionOpen={selectedSource !== null}
        selection={
          <SourceSelection
            source={selectedSource}
            gaiaMatch={
              selectedSource?.object_type
                ? gaiaMatchFor(
                    gaiaMatches,
                    selectedSource.source_id,
                    selectedSource.object_type,
                  )
                : undefined
            }
          />
        }
        workspace={
          <HduSelector
            images={imageHdus}
            value={hdu}
            onChange={(nextHdu) => {
              setWorkspace((current) => ({ ...current, hdu: nextHdu }));
            }}
          />
        }
        view={
          <>
            <PixelHistogram
              histogram={
                histogramQuery.data?.status === 200
                  ? histogramQuery.data.data
                  : undefined
              }
              isPending={histogramQuery.isPending}
              isError={histogramQuery.isError}
              pmin={renderParams.pmin}
              pmax={renderParams.pmax}
              showPercentiles={renderParams.limits === "percentiles"}
            />
            <RenderViewForm
              isPending={renderQuery.isFetching}
              onSubmit={(params) => {
                setWorkspace((current) => ({
                  ...current,
                  renderParams: params,
                }));
              }}
            />
          </>
        }
        sources={
          <>
            <p className="mb-3 text-xs text-muted-foreground">
              Ajusta los parámetros y lanza el análisis. Los puntos y las
              estructuras extendidas se marcan sobre la imagen.
            </p>
            <SourceDetectionForm
              isPending={sourcesQuery.isFetching}
              onSubmit={(params) => {
                setWorkspace((current) => ({
                  ...current,
                  detectionParams: params,
                }));
              }}
            />
            {sourcesQuery.isError ? (
              <p
                data-testid="detect-error"
                className="mt-2 text-sm text-destructive"
              >
                Error al detectar fuentes:{" "}
                {formatQueryError(sourcesQuery.error)}
              </p>
            ) : null}
            {detectionSummary ? (
              <p
                data-testid="detect-summary"
                className="mt-2 flex items-center gap-1 text-sm text-muted-foreground"
              >
                {detectionSummary.point_count} puntuales,{" "}
                {detectionSummary.extended_count} extendidas
                <HelpHint
                  label="resumen de fuentes"
                  testId="help-detect-summary"
                  glossaryId="fuente-extendida"
                >
                  Las puntuales son estrellas o picos nítidos; las extendidas
                  son nebulosas o galaxias y se marcan con recuadros.
                </HelpHint>
              </p>
            ) : null}
            <GaiaCrossMatch
              recordId={recordId}
              params={sourcesQueryParams}
              onMatches={setGaiaMatches}
            />
          </>
        }
        archive={
          <ImageArchive info={imageInfo} isPending={infoQuery.isPending} />
        }
      />
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
  objectUrl: string | undefined;
  label: string;
  pointSources: PointSourceSchema[];
  extendedSources: ExtendedSourceSchema[];
  gaiaPointIds: ReadonlySet<number>;
  gaiaExtendedIds: ReadonlySet<number>;
  selectedId?: number;
  selectedExtendedId?: number;
  onSelectSource?: (source: PointSourceSchema | ExtendedSourceSchema) => void;
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
