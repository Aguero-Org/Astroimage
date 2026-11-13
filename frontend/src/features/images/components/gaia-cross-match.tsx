import type {
  GaiaJobStatusSchema,
  GaiaMatchSchema,
  GaiaVerificationResponse,
  VerifySourcesGaiaParams,
} from "@/api/generated/model";
import {
  useGetSourcesGaiaJob,
  useVerifySourcesGaia,
} from "@/api/generated/sources/sources";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { Skeleton } from "@/components/ui/skeleton";
import { pendingJobId, polledJobResult } from "@/lib/polled-job";

type GaiaCrossMatchProps = {
  isFetching: boolean;
  isError: boolean;
  summary: GaiaVerificationResponse["summary"];
  queried: boolean;
  error: string | null;
  completed: boolean;
  onRetry: () => void;
};

export function useGaiaCrossMatch(
  recordId: string,
  params: VerifySourcesGaiaParams,
  enabled: boolean,
) {
  const start = useVerifySourcesGaia(recordId, params, {
    query: {
      enabled,
    },
  });
  const jobId = pendingJobId(start.data, isGaiaJob);
  const job = useGetSourcesGaiaJob(recordId, jobId ?? "", {
    query: {
      enabled: jobId !== undefined,
      refetchInterval: (query) => (isGaiaJob(query.state.data) ? 2000 : false),
    },
  });
  const { result, isFetching, isError, refetch } = polledJobResult({
    start,
    job,
    isJob: isGaiaJob,
    isResult: isGaiaVerification,
  });
  return {
    matches: result?.matches ?? [],
    summary: result?.summary,
    queried: result?.queried ?? false,
    error: result?.error ?? null,
    completed: result !== undefined,
    isFetching,
    isError,
    refetch,
  };
}

export function GaiaCrossMatch({
  isFetching,
  isError,
  summary,
  queried,
  error,
  completed,
  onRetry,
}: Readonly<GaiaCrossMatchProps>) {
  const failed = !!(isError || error !== null);
  return (
    <div data-testid="gaia-cross-match" className="mt-3 flex flex-col gap-2">
      <div className="flex items-center gap-1">
        <span
          data-testid="gaia-status"
          className="text-sm text-muted-foreground"
        >
          {isFetching ? "Cruzando con Gaia…" : "Cruce con Gaia"}
        </span>
        <HelpHint label="Cruce con Gaia" testId="help-gaia" glossaryId="gaia">
          Compara las detecciones de esta imagen con el catálogo Gaia.
        </HelpHint>
      </div>
      {failed && (
        <div className="flex flex-wrap items-center gap-2">
          <p data-testid="gaia-error" className="text-sm text-destructive">
            Gaia no respondió. Reintentá en unos minutos.
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRetry}
            disabled={isFetching}
          >
            Reintentar
          </Button>
        </div>
      )}
      {!failed && queried && !!summary && (
        <p data-testid="gaia-summary" className="text-sm text-muted-foreground">
          Puntuales {summary.point?.matched ?? 0}/{summary.point?.count ?? 0}.
          Extendidas {summary.extended?.matched ?? 0}/
          {summary.extended?.count ?? 0}.
        </p>
      )}
      {!failed && completed && !queried && !isFetching && (
        <p
          data-testid="gaia-unqueried"
          className="text-sm text-muted-foreground"
        >
          La imagen no tiene coordenadas celestes para cruzar con Gaia.
        </p>
      )}
      {!summary && !failed && isFetching && (
        <Skeleton data-testid="gaia-loading" className="h-5 w-44" aria-hidden />
      )}
    </div>
  );
}

type GaiaObjectKind = "point" | "extended";

export function gaiaMatchedIds(
  matches: readonly GaiaMatchSchema[],
  objectType: GaiaObjectKind,
): ReadonlySet<number> {
  return new Set(
    matches
      .filter((match) => match.object_type === objectType && match.gaia_match)
      .map((match) => match.source_id),
  );
}

export function gaiaMatchFor(
  matches: readonly GaiaMatchSchema[],
  sourceId: number,
  objectType: GaiaObjectKind,
): GaiaMatchSchema | undefined {
  return matches.find(
    (match) => match.source_id === sourceId && match.object_type === objectType,
  );
}

type GaiaBody = GaiaVerificationResponse | GaiaJobStatusSchema | undefined;

function isGaiaJob(value: GaiaBody): value is GaiaJobStatusSchema {
  return value?.status === "pending";
}

function isGaiaVerification(
  value: GaiaBody,
): value is GaiaVerificationResponse {
  return value?.status === "completed";
}
