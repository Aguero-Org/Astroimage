import { keepPreviousData } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
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
  DEFAULT_IMAGE_WORKSPACE,
  type ImageWorkspaceUi,
  resolveWorkspaceHdu,
} from "@/features/images/image-workspace";
import { rememberLastImageRecord } from "@/features/images/last-record";
import type { SourceFocusPulse } from "@/features/images/source-focus-pulse";
import { followOnQueriesEnabled } from "@/features/images/workspace-queries";

const DEFAULT_DOCUMENT_TITLE = "Astroimage 🌌";

function responseData<R extends { status: number; data: unknown }>(
  data: R | undefined,
): Extract<R, { status: 200 }>["data"] | undefined {
  if (data?.status !== 200) {
    return undefined;
  }
  return data.data as Extract<R, { status: 200 }>["data"];
}

function withHdu<T extends object>(
  hdu: number | null,
  params: T,
): T | (T & { hdu: number }) {
  if (hdu === null) {
    return params;
  }
  return { ...params, hdu };
}

function joinedTitle(pageTitle: string, catalogName: string): string {
  if (catalogName.length === 0 || catalogName === pageTitle) {
    return pageTitle;
  }
  return `${pageTitle} · ${catalogName}`;
}

function alignHduScope(
  hduScope: { recordId: string; hdu: number | null },
  recordId: string,
  hdu: number | null,
  selectedSource: ImageWorkspaceUi["selectedSource"],
  setHduScope: (scope: { recordId: string; hdu: number | null }) => void,
  setWorkspace: Dispatch<SetStateAction<ImageWorkspaceUi>>,
): void {
  if (hduScope.recordId !== recordId) {
    setHduScope({ recordId, hdu: null });
    setWorkspace((current) => {
      if (current.hdu === null && current.selectedSource === null) {
        return current;
      }
      return { ...current, hdu: null, selectedSource: null };
    });
    return;
  }
  if (hduScope.hdu === hdu || selectedSource === null) {
    if (hduScope.hdu !== hdu) {
      setHduScope({ recordId, hdu });
    }
    return;
  }
  setHduScope({ recordId, hdu });
  setWorkspace((current) =>
    current.selectedSource === null
      ? current
      : { ...current, selectedSource: null },
  );
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

  useEffect(() => {
    rememberLastImageRecord(recordId, slug);
  }, [recordId, slug]);

  const [workspace, setWorkspace] = useState<ImageWorkspaceUi>(
    DEFAULT_IMAGE_WORKSPACE,
  );
  const [focusPulse, setFocusPulse] = useState<SourceFocusPulse | null>(null);
  const { inspectorOpen, selectedSource, renderParams, detectionParams } =
    workspace;
  const infoQuery = useGetImageInfo(recordId);
  const imageInfo = responseData(infoQuery.data);
  const imageHdus = imageInfo?.hdus.images ?? [];
  const hdu = resolveWorkspaceHdu(
    workspace.hdu,
    imageHdus,
    imageInfo?.hdus.selected ?? null,
  );
  const [hduScope, setHduScope] = useState({ recordId, hdu });
  alignHduScope(
    hduScope,
    recordId,
    hdu,
    selectedSource,
    setHduScope,
    setWorkspace,
  );
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
    hdu === null ? undefined : { hdu },
    { query: { enabled: false } },
  );
  const detected = responseData(sourcesQuery.data);
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

  useEffect(() => {
    document.title = `${titleWithDescription} - Astroimage`;
    return () => {
      document.title = DEFAULT_DOCUMENT_TITLE;
    };
  }, [titleWithDescription]);
  const pointSources = detected?.point_sources ?? [];
  const extendedSources = detected?.extended_sources ?? [];
  const visibleSimbadObjects = simbadObjectsInView(
    simbadData?.objects ?? [],
    new Set(pointSources.map((source) => source.source_id)),
    new Set(extendedSources.map((source) => source.source_id)),
  );
  const selectedPointId = sourceId(selectedSource, "point");
  const selectedExtendedId = sourceId(selectedSource, "extended");
  const rendered = responseData(renderQuery.data);
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
              label={titleWithDescription}
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
              onOpenChange={(open) => {
                setWorkspace((current) => ({
                  ...current,
                  inspectorOpen: open,
                }));
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
                    histogram={responseData(histogramQuery.data)}
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
                      data: responseData(bestPresetQuery.data),
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
