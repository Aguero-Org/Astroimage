import {
  useGetCatalogsJob,
  useRecommendCatalogs,
} from "@/api/generated/catalogs/catalogs";
import type { RecommendCatalogsParams } from "@/api/generated/model";
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
    },
  });

  const body = query.data?.status === 200 ? query.data.data : undefined;
  const pendingJobId = isCatalogJobStatus(body) ? body.job_id : undefined;

  const jobQuery = useGetCatalogsJob(recordId, pendingJobId ?? "", {
    query: {
      enabled: enabled && pendingJobId !== undefined,
      retry: false,
      refetchInterval: (job) => {
        if (job.state.status === "error") {
          return false;
        }
        const jobBody =
          job.state.data?.status === 200 ? job.state.data.data : undefined;
        return isCatalogRecommendation(jobBody) ? false : JOB_POLL_INTERVAL_MS;
      },
    },
  });

  const jobBody =
    jobQuery.data?.status === 200 ? jobQuery.data.data : undefined;
  const result = isCatalogRecommendation(jobBody)
    ? jobBody
    : isCatalogRecommendation(body)
      ? body
      : undefined;

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
