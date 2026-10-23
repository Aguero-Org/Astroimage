import { createFileRoute } from "@tanstack/react-router";
import { useEffect } from "react";
import type {
  DetectSourcesParams,
  RenderFitsImageParams,
} from "@/api/generated/model";
import { type Dispatch, type SetStateAction, useEffect, useState } from "react";
import { useGetImageInfo } from "@/api/generated/hub/hub";
import {
  useRenderFitsHistogram,
  useRenderFitsImage,
} from "@/api/generated/render/render";
import { useGetSimbadReferences } from "@/api/generated/simbad/simbad";
import {
  useDetectSources,
  useGetBestPreset,
} from "@/api/generated/sources/sources";
import { HelpHint } from "@/components/ui/help-hint";
import { ScientificWorkspace } from "@/features/catalogs/components/scientific-workspace";
import { simbadObjectsInView } from "@/features/catalogs/simbad-references";
import {
  useBestPreset,
  useImageHistogram,
  useImageInfo,
  useImageRender,
  useSourceDetection,
} from "@/features/images/api";
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
import {
  RenderedFitsSection,
  useRenderedObjectUrl,
} from "@/features/images/components/rendered-fits-section";
import { SourceDetectionForm } from "@/features/images/components/source-detection-form";
import { SourceSelection } from "@/features/images/components/source-selection";
import { formatQueryError } from "@/features/images/format-query-error";
import { imageDisplayTitle } from "@/features/images/image-title";
import {
  type ImageWorkspaceUi,
  resolveWorkspaceHdu,
} from "@/features/images/image-workspace";
import { rememberLastImageRecord } from "@/features/images/last-record";
import { useImageWorkspace } from "@/features/images/use-image-workspace";
import type { SourceFocusPulse } from "@/features/images/source-focus-pulse";
import { followOnQueriesEnabled } from "@/features/images/workspace-queries";
import { useDocumentTitle } from "@/hooks/use-document-title";

const DEFAULT_DOCUMENT_TITLE = "Astroimage 🌌";

function joinedTitle(pageTitle: string, catalogName: string): string {
  if (catalogName.length === 0 || catalogName === pageTitle) {
    return pageTitle;
  }
  return `${pageTitle} · ${catalogName}`;
}

function sourceId(
  source: ImageWorkspaceUi["selectedSource"],
  objectType: "point" | "extended",
): number | undefined {
  if (source?.object_type !== objectType) {
    return undefined;
  }
  return source.source_id;
}

export const Route = createFileRoute("/image/$recordId/{-$slug}")({
  component: ImageDetailPage,
});

function ImageDetailPage() {
  const { recordId, slug } = Route.useParams();
  return <ImageWorkspacePage key={recordId} recordId={recordId} slug={slug} />;
}

function ImageWorkspacePage({
  recordId,
  slug,
}: Readonly<{
  recordId: string;
  slug: string | undefined;
}>) {
  useEffect(() => {
    rememberLastImageRecord(recordId, slug);
  }, [recordId, slug]);

  const [workspace, dispatch] = useImageWorkspace();
  const [workspace, setWorkspace] = useState<ImageWorkspaceUi>(
    DEFAULT_IMAGE_WORKSPACE,
  );
  const [focusPulse, setFocusPulse] = useState<SourceFocusPulse | null>(null);
  const { inspectorOpen, selectedSource, renderParams, detectionParams } =
    workspace;
  const infoQuery = useImageInfo(recordId);
  const imageInfo = infoQuery.data;
  const imageHdus = imageInfo?.hdus.images ?? [];
  const hdu = resolveWorkspaceHdu(
    workspace.hdu,
    imageHdus,
    imageInfo?.hdus.selected ?? null,
  );
  const renderQueryParams: RenderFitsImageParams = {
    ...renderParams,
    hdu: hdu ?? undefined,
  };
  const renderQuery = useImageRender(recordId, renderQueryParams);
  const sourcesQueryParams: DetectSourcesParams = {
    ...detectionParams,
    hdu: hdu ?? undefined,
  };
  const followOnsEnabled = followOnQueriesEnabled(renderQuery);
  const sourcesQuery = useSourceDetection(
    recordId,
    sourcesQueryParams,
    followOnsEnabled,
  );
  const histogramQuery = useImageHistogram(
  const renderQueryParams = withHdu(hdu, renderParams);
  const renderQuery = useRenderFitsImage(recordId, renderQueryParams, {
    query: { placeholderData: keepPreviousData },
  });
  const sourcesQueryParams = withHdu(hdu, detectionParams);
  const followOnsEnabled = followOnQueriesEnabled(renderQuery);
  const sourcesQuery = useDetectSources(recordId, sourcesQueryParams, {
    query: { enabled: followOnsEnabled },
  });
  const histogramParams = withHdu(hdu, { bins: 64 });
  const histogramQuery = useRenderFitsHistogram(recordId, histogramParams, {
    query: { enabled: followOnsEnabled },
  });
  const bestPresetQuery = useGetBestPreset(
    recordId,
    { bins: 64, hdu: hdu ?? undefined },
    followOnsEnabled,
  );
  // Measuring the PSF is expensive, so this only runs when the inspector asks
  // for it instead of on every visit to the image.
  const bestPresetQuery = useBestPreset(recordId, hdu);
  const detected = sourcesQuery.data;
  const detectionSummary = detected?.summary;
  const gaia = useGaiaCrossMatch(
    recordId,
    sourcesQueryParams,
    detectionSummary !== undefined,
  );
  const simbadParams = hdu === null ? undefined : { hdu };
  const simbadQuery = useGetSimbadReferences(recordId, simbadParams, {
    query: { enabled: gaia.summary !== undefined, staleTime: 5 * 60 * 1000 },
  });
  const simbadData =
    simbadQuery.data?.status === 200 ? simbadQuery.data.data : undefined;
  const simbadPointIds = new Set<number>();
  const simbadExtendedIds = new Set<number>();
  for (const obj of simbadData?.objects ?? []) {
    const match = obj.image_match;
    if (!match?.matched) {
      continue;
    }
    if (String(match.object_type) === "point") {
      simbadPointIds.add(match.source_id);
    } else if (String(match.object_type) === "extended") {
      simbadExtendedIds.add(match.source_id);
    }
  }
  const sourceName = imageInfo?.source_name;
  const pageTitle = imageDisplayTitle(sourceName, slug);
  const catalogName = imageInfo?.display_name?.trim() ?? "";
  const titleWithDescription = joinedTitle(pageTitle, catalogName);

  useDocumentTitle(
    `${titleWithDescription} - Astroimage`,
    DEFAULT_DOCUMENT_TITLE,
  );
  const pointSources = detected?.point_sources ?? [];
  const extendedSources = detected?.extended_sources ?? [];
  const visibleSimbadObjects = simbadObjectsInView(
    simbadData?.objects ?? [],
    new Set(pointSources.map((source) => source.source_id)),
    new Set(extendedSources.map((source) => source.source_id)),
  );
  const selectedPointId = sourceId(selectedSource, "point");
  const selectedExtendedId = sourceId(selectedSource, "extended");
  const rendered = renderQuery.data;
  const preview = useRenderedObjectUrl(rendered);

  const scientificParams = hdu === null ? undefined : { hdu };

  return (
    <main className="relative h-svh w-full overflow-hidden bg-black">
      <ScientificWorkspace
        recordId={recordId}
        enabled={gaia.summary !== undefined}
        params={scientificParams}
        preview={preview}
        hdu={hdu}
        selectedSource={
          selectedSource
            ? {
                source_id: selectedSource.source_id,
                object_type: selectedSource.object_type as "point" | "extended",
              }
            : null
        }
        simbadObjects={visibleSimbadObjects}
        simbadResult={simbadData}
        simbadIsError={simbadQuery.isError}
        simbadErrorMessage={
          simbadQuery.error instanceof Error
            ? simbadQuery.error.message
            : "error desconocido"
        }
        simbadIsLoading={
          gaia.summary !== undefined &&
          simbadData === undefined &&
          !simbadQuery.isError
        }
        simbadIsFetching={simbadQuery.isFetching}
        onSimbadRetry={() => {
          void simbadQuery.refetch();
        }}
        onFocusSource={(sourceId, objectType) => {
          setFocusPulse((current: SourceFocusPulse | null) => ({
            sourceId,
            objectType,
            nonce: (current?.nonce ?? 0) + 1,
          }));
          setWorkspace((current) => {
            if (objectType === "point") {
              const src = pointSources.find((s) => s.source_id === sourceId);
              return src
                ? { ...current, selectedSource: src, inspectorOpen: true }
                : current;
            }
            const src = extendedSources.find((s) => s.source_id === sourceId);
            return src
              ? { ...current, selectedSource: src, inspectorOpen: true }
              : current;
          });
        }}
        image={
          <>
            <RenderedFitsSection
              isPending={renderQuery.isPending}
              isError={renderQuery.isError}
              error={renderQuery.error}
              rendered={rendered}
              imageUrl={preview}
              label={titleWithDescription}
              sources={{
                pointSources,
                extendedSources,
                gaiaPointIds: gaiaMatchedIds(gaia.matches, "point"),
                gaiaExtendedIds: gaiaMatchedIds(gaia.matches, "extended"),
                selectedPointId,
                selectedExtendedId,
                onSelect: (source) =>
                  dispatch({ type: "select-source", source }),
              pointSources={pointSources}
              extendedSources={extendedSources}
              gaiaPointIds={gaiaMatchedIds(gaia.matches, "point")}
              gaiaExtendedIds={gaiaMatchedIds(gaia.matches, "extended")}
              simbadPointIds={simbadPointIds}
              simbadExtendedIds={simbadExtendedIds}
              selectedId={selectedPointId}
              selectedExtendedId={selectedExtendedId}
              focusPulse={focusPulse}
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
              onOpenChange={(open) =>
                dispatch({ type: "set-inspector-open", open })
              }
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
                  onChange={(nextHdu) =>
                    dispatch({ type: "set-hdu", hdu: nextHdu })
                  }
                />
              }
              view={
                <>
                  <PixelHistogram
                    histogram={histogramQuery.data}
                    isPending={histogramQuery.isPending}
                    isError={histogramQuery.isError}
                    pmin={renderParams.pmin}
                    pmax={renderParams.pmax}
                    showPercentiles={renderParams.limits === "percentiles"}
                  />
                  <RenderViewForm
                    isPending={renderQuery.isFetching}
                    onSubmit={(params) =>
                      dispatch({ type: "set-render-params", params })
                    }
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
                      data: bestPresetQuery.data,
                      request: () =>
                        bestPresetQuery.refetch().then((result) => result.data),
                    }}
                    onSubmit={(params) =>
                      dispatch({ type: "set-detection-params", params })
                    }
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
                        Las puntuales son estrellas o picos nítidos; las
                        extendidas son nebulosas o galaxias y se marcan con
                        recuadros.
                      </HelpHint>
                    </p>
                  ) : null}
                  <GaiaCrossMatch
                    isFetching={gaia.isFetching}
                    isError={gaia.isError}
                    summary={gaia.summary}
                  />
                </>
              }
              archive={
                <ImageArchive
                  info={imageInfo}
                  isPending={infoQuery.isPending}
                />
              }
            />
          </>
        }
      />
    </main>
  );
}
