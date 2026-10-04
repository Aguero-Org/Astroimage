import { keepPreviousData } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useGetImageInfo } from "@/api/generated/hub/hub";
import {
  useRenderFitsHistogram,
  useRenderFitsImage,
} from "@/api/generated/render/render";
import {
  useDetectSources,
  useGetBestPreset,
} from "@/api/generated/sources/sources";
import { HelpHint } from "@/components/ui/help-hint";
import {
  GaiaCrossMatch,
  gaiaMatchedIds,
  gaiaMatchFor,
  useGaiaCrossMatch,
} from "@/features/images/components/gaia-cross-match";
import { HduSelector } from "@/features/images/components/hdu-selector";
import { ImageArchive } from "@/features/images/components/image-archive";
import { ImageInspector } from "@/features/images/components/image-inspector";
import { PixelHistogram } from "@/features/images/components/pixel-histogram";
import { RenderViewForm } from "@/features/images/components/render-view-form";
import { RenderedFitsSection } from "@/features/images/components/rendered-fits-section";
import { SourceDetectionForm } from "@/features/images/components/source-detection-form";
import { SourceSelection } from "@/features/images/components/source-selection";
import { formatQueryError } from "@/features/images/format-query-error";
import { imageDisplayTitle } from "@/features/images/image-title";
import {
  DEFAULT_IMAGE_WORKSPACE,
  type ImageWorkspaceUi,
  resolveWorkspaceHdu,
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
  const { inspectorOpen, selectedSource, renderParams, detectionParams } =
    workspace;
  const infoQuery = useGetImageInfo(recordId);
  const imageInfo =
    infoQuery.data?.status === 200 ? infoQuery.data.data : undefined;
  const imageHdus = imageInfo?.hdus.images ?? [];
  const hdu = resolveWorkspaceHdu(
    workspace.hdu,
    imageHdus,
    imageInfo?.hdus.selected ?? null,
  );
  const [hduScope, setHduScope] = useState({ recordId, hdu });
  if (hduScope.recordId !== recordId) {
    setHduScope({ recordId, hdu: null });
    setWorkspace((current) => {
      if (current.hdu === null && current.selectedSource === null) {
        return current;
      }
      return { ...current, hdu: null, selectedSource: null };
    });
  } else if (hduScope.hdu !== hdu) {
    setHduScope({ recordId, hdu });
    if (selectedSource !== null) {
      setWorkspace((current) =>
        current.selectedSource === null
          ? current
          : { ...current, selectedSource: null },
      );
    }
  }
  const renderQueryParams =
    hdu === null ? renderParams : { ...renderParams, hdu };
  const renderQuery = useRenderFitsImage(recordId, renderQueryParams, {
    query: { placeholderData: keepPreviousData },
  });
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
  // Measuring the PSF is expensive, so this only runs when the inspector asks
  // for it instead of on every visit to the image.
  const bestPresetQuery = useGetBestPreset(
    recordId,
    hdu === null ? undefined : { hdu },
    { query: { enabled: false } },
  );
  const gaia = useGaiaCrossMatch(recordId, sourcesQueryParams);
  const sourceName = imageInfo?.source_name;
  const pageTitle = imageDisplayTitle(sourceName, slug);
  const catalogName = imageInfo?.display_name?.trim() ?? "";
  const titleWithDescription =
    catalogName.length > 0 && catalogName !== pageTitle
      ? `${pageTitle} · ${catalogName}`
      : pageTitle;

  useEffect(() => {
    document.title = `${titleWithDescription} - Astroimage`;
    return () => {
      document.title = DEFAULT_DOCUMENT_TITLE;
    };
  }, [titleWithDescription]);
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

  const rendered =
    renderQuery.data?.status === 200 ? renderQuery.data.data : undefined;

  return (
    <main className="relative h-svh w-full overflow-hidden bg-black">
      <RenderedFitsSection
        isPending={renderQuery.isPending}
        isError={renderQuery.isError}
        error={renderQuery.error}
        rendered={rendered}
        label={titleWithDescription}
        pointSources={pointSources}
        extendedSources={extendedSources}
        gaiaPointIds={gaiaMatchedIds(gaia.matches, "point")}
        gaiaExtendedIds={gaiaMatchedIds(gaia.matches, "extended")}
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
            className="min-w-0 rounded-md bg-black/75 px-3 py-1 text-xl font-semibold leading-snug text-white"
          >
            {pageTitle}
            {catalogName.length > 0 && catalogName !== pageTitle && (
              <span className="font-medium text-white/80">
                {" "}
                · {catalogName}
              </span>
            )}
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
                    gaia.matches,
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
              setHduScope({ recordId, hdu: nextHdu });
              setWorkspace((current) => ({
                ...current,
                hdu: nextHdu,
                selectedSource: null,
              }));
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
              bestPreset={{
                isPending: bestPresetQuery.isFetching,
                isError: bestPresetQuery.isError,
                data:
                  bestPresetQuery.data?.status === 200
                    ? bestPresetQuery.data.data
                    : undefined,
                request: () => {
                  void bestPresetQuery.refetch();
                },
              }}
              onSubmit={(params) => {
                setWorkspace((current) => ({
                  ...current,
                  detectionParams: params,
                  selectedSource: null,
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
              isFetching={gaia.isFetching}
              isError={gaia.isError}
              summary={gaia.summary}
              onArm={gaia.arm}
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
