import { useEffect, useState } from "react";
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

type GaiaCrossMatchProps = {
  recordId: string;
  params: VerifySourcesGaiaParams;
  onMatches: (matches: GaiaMatchSchema[]) => void;
};

export function GaiaCrossMatch({
  recordId,
  params,
  onMatches,
}: Readonly<GaiaCrossMatchProps>) {
  const [armed, setArmed] = useState(false);
  const verifyQuery = useVerifySourcesGaia(recordId, params, {
    query: { enabled: armed },
  });
  const verifyBody =
    verifyQuery.data?.status === 200 ? verifyQuery.data.data : undefined;
  const pendingJobId = isGaiaJob(verifyBody) ? verifyBody.job_id : undefined;
  const jobQuery = useGetSourcesGaiaJob(recordId, pendingJobId ?? "", {
    query: {
      enabled: pendingJobId !== undefined,
      refetchInterval: (query) => {
        const body =
          query.state.data?.status === 200 ? query.state.data.data : undefined;
        return isGaiaJob(body) ? 2000 : false;
      },
    },
  });
  const jobBody =
    jobQuery.data?.status === 200 ? jobQuery.data.data : undefined;
  const result = gaiaVerificationResult(jobBody, verifyBody);

  useEffect(() => {
    onMatches(result?.matches ?? []);
  }, [onMatches, result]);

  return (
    <div data-testid="gaia-cross-match" className="mt-3 flex flex-col gap-2">
      <div className="flex items-center gap-1">
        <Button
          type="button"
          variant="outline"
          data-testid="gaia-cross-match-submit"
          disabled={verifyQuery.isFetching || jobQuery.isFetching}
          onClick={() => {
            setArmed(true);
          }}
        >
          {verifyQuery.isFetching || jobQuery.isFetching
            ? "Cruzando…"
            : "Cruzar con Gaia"}
        </Button>
        <HelpHint label="Cruce con Gaia" testId="help-gaia" glossaryId="gaia">
          Compara las detecciones de esta imagen con el catálogo Gaia.
        </HelpHint>
      </div>
      {verifyQuery.isError || jobQuery.isError ? (
        <p data-testid="gaia-error" className="text-sm text-destructive">
          No se pudo cruzar con Gaia.
        </p>
      ) : null}
      {result?.summary ? (
        <p data-testid="gaia-summary" className="text-sm text-muted-foreground">
          Puntuales {result.summary.point?.matched ?? 0}/
          {result.summary.point?.count ?? 0}. Extendidas{" "}
          {result.summary.extended?.matched ?? 0}/
          {result.summary.extended?.count ?? 0}.
        </p>
      ) : null}
    </div>
  );
}

export function gaiaMatchedIds(
  matches: readonly GaiaMatchSchema[],
  objectType: "point" | "extended",
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
  objectType: "point" | "extended",
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
