import { createFileRoute, notFound } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { getGetImageInfoQueryOptions } from "@/api/generated/hub/hub";
import type {
  DetectSourcesParams,
  RenderFitsImageParams,
} from "@/api/generated/model";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { ScientificWorkspace } from "@/features/catalogs/components/scientific-workspace";
import { simbadObjectsInView } from "@/features/catalogs/simbad-references";
import { useSimbadReferences } from "@/features/catalogs/use-simbad-references";
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
import type { SourceFocusPulse } from "@/features/images/source-focus-pulse";
import { useImageWorkspace } from "@/features/images/use-image-workspace";
import { followOnQueriesEnabled } from "@/features/images/workspace-queries";
import { useDocumentTitle } from "@/hooks/use-document-title";
import { ApiError } from "@/lib/api-client";

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
  loader: async ({ context, params }) => {
    try {
      return await context.queryClient.ensureQueryData(
        getGetImageInfoQueryOptions(params.recordId),
      );
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        throw notFound();
      }
      throw error;
    }
  },
  component: ImageDetailPage,
  pendingComponent: ImageDetailPending,
  errorComponent: ImageDetailError,
  notFoundComponent: ImageDetailNotFound,
});

function ImageDetailPending() {
  return (
    <main className="flex min-h-svh items-center justify-center bg-background p-6">
      <p className="text-sm text-muted-foreground">Cargando imagen...</p>
    </main>
  );
}

function ImageDetailError({
  reset,
}: Readonly<{ error: unknown; reset: () => void }>) {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 bg-background p-6 text-center">
      <h1 className="text-xl font-semibold">No se pudo cargar la imagen.</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        Ocurrió un problema al recuperar los datos del visor.
      </p>
      <Button type="button" onClick={reset}>
        Reintentar
      </Button>
    </main>
  );
}

function ImageDetailNotFound() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 bg-background p-6 text-center">
      <h1 className="text-xl font-semibold">Imagen no encontrada</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        El registro solicitado no existe o fue eliminado.
      </p>
      <a href="/" className="text-sm text-primary underline">
        Volver al inicio
      </a>
    </main>
  );
}

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
    recordId,
    { bins: 64, hdu: hdu ?? undefined },
    followOnsEnabled,
  );
  const bestPresetQuery = useBestPreset(recordId, hdu);
  const detected = sourcesQuery.data;
  const detectionSummary = detected?.summary;
  const gaia = useGaiaCrossMatch(
    recordId,
    sourcesQueryParams,
    detectionSummary !== undefined,
  );
  const simbad = useSimbadReferences({
    recordId,
    hdu,
    enabled: gaia.summary !== undefined,
  });
  const simbadPointIds = new Set<number>();
  const simbadExtendedIds = new Set<number>();
  for (const obj of simbad.objects) {
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
  const visibleSimbadObjects = useMemo(
    () =>
      simbadObjectsInView(
        simbad.objects,
        new Set(pointSources.map((source) => source.source_id)),
        new Set(extendedSources.map((source) => source.source_id)),
      ),
    [simbad.objects, pointSources, extendedSources],
  );
  const visibleSimbad = { ...simbad, objects: visibleSimbadObjects };
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
        selectedSource={
          selectedSource
            ? {
                source_id: selectedSource.source_id,
                object_type: selectedSource.object_type as "point" | "extended",
              }
            : null
        }
        simbad={visibleSimbad}
        onFocusSource={(sourceId, objectType) => {
          setFocusPulse((current) => ({
            sourceId,
            objectType,
            nonce: (current?.nonce ?? 0) + 1,
          }));
          const source =
            objectType === "point"
              ? pointSources.find((item) => item.source_id === sourceId)
              : extendedSources.find((item) => item.source_id === sourceId);
          if (source) {
            dispatch({ type: "select-source", source });
          }
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
              focusPulse={focusPulse}
              sources={{
                pointSources,
                extendedSources,
                gaiaPointIds: gaiaMatchedIds(gaia.matches, "point"),
                gaiaExtendedIds: gaiaMatchedIds(gaia.matches, "extended"),
                simbadPointIds,
                simbadExtendedIds,
                selectedPointId,
                selectedExtendedId,
                onSelect: (source) =>
                  dispatch({ type: "select-source", source }),
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
