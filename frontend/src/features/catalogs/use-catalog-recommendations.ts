import {
  useGetCatalogsJob,
  useRecommendCatalogs,
} from "@/api/generated/catalogs/catalogs";
import type { RecommendCatalogsParams } from "@/api/generated/model";
import { pendingJobId, polledJobResult } from "@/lib/polled-job";
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
  const started = useRecommendCatalogs(recordId, params, {
    query: {
      enabled,
      staleTime: RESULT_STALE_TIME_MS,
      retry: false,
    },
  });

  const jobId = pendingJobId(started.data, isCatalogJobStatus);
  const job = useGetCatalogsJob(recordId, jobId ?? "", {
    query: {
      enabled: enabled && jobId !== undefined,
      retry: false,
      refetchInterval: (query) => {
        if (query.state.status === "error") {
          return false;
        }
        return isCatalogRecommendation(query.state.data)
          ? false
          : JOB_POLL_INTERVAL_MS;
      },
    },
  });

  const { result, isFetching, isError, error, refetch } = polledJobResult({
    start: started,
    job,
    isJob: isCatalogJobStatus,
    isResult: isCatalogRecommendation,
  });

  return {
    result,
    publications: collectPublications(
      result?.recommendations ?? [],
      result?.papers ?? [],
    ),
    isLoading: enabled && result === undefined && !isError,
    isFetching,
    isError,
    errorMessage: formatError(error),
    refetch,
  };
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : "error desconocido";
}
