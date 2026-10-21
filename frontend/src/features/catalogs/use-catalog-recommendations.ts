import {
  useGetCatalogsJob,
  useRecommendCatalogs,
} from "@/api/generated/catalogs/catalogs";
import type {
  CatalogRecommendationResponse,
  RecommendCatalogsParams,
} from "@/api/generated/model";
import { okData } from "@/lib/api-response";
import {
  collectPublications,
  isCatalogJobStatus,
  isCatalogRecommendation,
} from "./catalog-recommendations";

const JOB_POLL_INTERVAL_MS = 2000;
const RESULT_STALE_TIME_MS = 5 * 60 * 1000;

type UseCatalogRecommendationsOptions = {
  recordId: string;
  params: RecommendCatalogsParams | undefined;
  enabled: boolean;
};

export function useCatalogRecommendations({
  recordId,
  params,
  enabled,
}: UseCatalogRecommendationsOptions) {
  const query = useRecommendCatalogs(recordId, params, {
    query: {
      enabled,
      staleTime: RESULT_STALE_TIME_MS,
      retry: false,
      select: (response) =>
        response.status === 200 ? response.data : undefined,
    },
  });

  const body = query.data;
  const pendingJobId = isCatalogJobStatus(body) ? body.job_id : undefined;

  const jobQuery = useGetCatalogsJob(recordId, pendingJobId ?? "", {
    query: {
      enabled: enabled && pendingJobId !== undefined,
      retry: false,
      select: (response) =>
        response.status === 200 ? response.data : undefined,
      refetchInterval: (job) => {
        if (job.state.status === "error") {
          return false;
        }
        return isCatalogRecommendation(okData(job.state.data))
          ? false
          : JOB_POLL_INTERVAL_MS;
      },
    },
  });

  const jobBody = jobQuery.data;
  let result: CatalogRecommendationResponse | undefined;
  if (isCatalogRecommendation(jobBody)) {
    result = jobBody;
  } else if (isCatalogRecommendation(body)) {
    result = body;
  }

  const isError = query.isError || jobQuery.isError;
  const isLoading = enabled && result === undefined && !isError;
  const isFetching = query.isFetching || jobQuery.isFetching;
  const error = query.error ?? jobQuery.error;

  function refetch() {
    void query.refetch();
    if (pendingJobId !== undefined) {
      void jobQuery.refetch();
    }
  }

  return {
    result,
    publications: collectPublications(result?.recommendations ?? []),
    isLoading,
    isFetching,
    isError,
    errorMessage: formatError(error),
    refetch,
  };
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : "error desconocido";
}
