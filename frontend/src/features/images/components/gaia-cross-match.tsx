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
import { HelpHint } from "@/components/ui/help-hint";
import { Skeleton } from "@/components/ui/skeleton";
import { okData } from "@/lib/api-response";

type GaiaCrossMatchProps = {
  isFetching: boolean;
  isError: boolean;
  summary: GaiaVerificationResponse["summary"];
};

export function useGaiaCrossMatch(
  recordId: string,
  params: VerifySourcesGaiaParams,
  enabled: boolean,
) {
  const verifyQuery = useVerifySourcesGaia(recordId, params, {
    query: {
      enabled,
      select: (response) =>
        response.status === 200 ? response.data : undefined,
    },
  });
  const verifyBody = verifyQuery.data;
  const pendingJobId = isGaiaJob(verifyBody) ? verifyBody.job_id : undefined;
  const jobQuery = useGetSourcesGaiaJob(recordId, pendingJobId ?? "", {
    query: {
      enabled: pendingJobId !== undefined,
      select: (response) =>
        response.status === 200 ? response.data : undefined,
      refetchInterval: (query) =>
        isGaiaJob(okData(query.state.data)) ? 2000 : false,
    },
  });
  const jobBody = jobQuery.data;
  const result = gaiaVerificationResult(jobBody, verifyBody);
  return {
    matches: result?.matches ?? [],
    summary: result?.summary,
    isFetching: verifyQuery.isFetching || jobQuery.isFetching,
    isError: verifyQuery.isError || jobQuery.isError,
  };
}

export function GaiaCrossMatch({
  isFetching,
  isError,
  summary,
}: Readonly<GaiaCrossMatchProps>) {
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
      {!!isError && (
        <p data-testid="gaia-error" className="text-sm text-destructive">
          No se pudo cruzar con Gaia.
        </p>
      )}
      {!!summary && (
        <p data-testid="gaia-summary" className="text-sm text-muted-foreground">
          Puntuales {summary.point?.matched ?? 0}/{summary.point?.count ?? 0}.
          Extendidas {summary.extended?.matched ?? 0}/
          {summary.extended?.count ?? 0}.
        </p>
      )}
      {!summary && !isError && isFetching && (
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

function gaiaVerificationResult(
  jobBody: GaiaBody,
  verifyBody: GaiaBody,
): GaiaVerificationResponse | undefined {
  if (isGaiaVerification(jobBody)) {
    return jobBody;
  }
  if (isGaiaVerification(verifyBody)) {
    return verifyBody;
  }
  return undefined;
}

function isGaiaJob(value: GaiaBody): value is GaiaJobStatusSchema {
  return (
    value !== undefined &&
    "job_id" in value &&
    !("match_radius_arcsec" in value)
  );
}

function isGaiaVerification(
  value: GaiaBody,
): value is GaiaVerificationResponse {
  return value !== undefined && "match_radius_arcsec" in value;
}
