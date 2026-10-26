import type {
  GetSimbadReferencesParams,
  SimbadReferencesResponse,
} from "@/api/generated/model";
import { useGetSimbadReferences } from "@/api/generated/simbad/simbad";

type UseSimbadReferencesOptions = {
  recordId: string;
  hdu: number | null;
  enabled: boolean;
};

const STALE_TIME_MS = 5 * 60 * 1000;

export function useSimbadReferences({
  recordId,
  hdu,
  enabled,
}: UseSimbadReferencesOptions) {
  const params: GetSimbadReferencesParams | undefined =
    hdu === null ? undefined : { hdu };
  const query = useGetSimbadReferences(recordId, params, {
    query: {
      enabled,
      staleTime: STALE_TIME_MS,
      retry: false,
    },
  });

  const result: SimbadReferencesResponse | undefined = query.data;

  const isError = query.isError;
  const isLoading = enabled && result === undefined && !isError;
  const isFetching = query.isFetching;
  const error = query.error;

  function refetch() {
    void query.refetch();
  }

  return {
    result,
    objects: result?.objects ?? [],
    summary: result?.summary,
    isLoading,
    isFetching,
    isError,
    errorMessage: error instanceof Error ? error.message : "error desconocido",
    refetch,
  };
}

export type SimbadReferencesView = ReturnType<typeof useSimbadReferences>;
