import { keepPreviousData, useQueryClient } from "@tanstack/react-query";
import {
  getGetImageTransferQueryKey,
  getListHubbleImagesQueryKey,
  useCancelImageTransfer,
  useGetImageTransfer,
  useResumeImageTransfer,
  useSearchHubbleCandidates,
} from "@/api/generated/hub/hub";
import type {
  SearchHubbleCandidatesOrder,
  SearchHubbleCandidatesSort,
  TransferStatusSchema,
} from "@/api/generated/model";
import { okData } from "@/lib/api-response";

export type CandidateSortField = SearchHubbleCandidatesSort;
export type CandidateSortOrder = SearchHubbleCandidatesOrder;
export type ImageTransfer = TransferStatusSchema;

const ACTIVE = new Set(["queued", "transferring", "annotating", "storing"]);

export function isActiveTransfer(status: string | undefined): boolean {
  return status !== undefined && ACTIVE.has(status);
}

export function formatBytes(value: number | null): string {
  if (value === null) {
    return "—";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function useCandidateSearch(
  query: string,
  page: number,
  sort: CandidateSortField,
  order: CandidateSortOrder,
) {
  const trimmed = query.trim();
  return useSearchHubbleCandidates(
    {
      query: trimmed.length > 0 ? trimmed : "-",
      page,
      limit: 8,
      sort,
      order,
    },
    {
      query: {
        enabled: trimmed.length > 0,
        placeholderData: keepPreviousData,
        select: (response) => (response.status === 200 ? response.data : null),
      },
    },
  );
}

export function useImageTransfer(transferId: string | null) {
  const queryClient = useQueryClient();
  return useGetImageTransfer(transferId ?? "", {
    query: {
      enabled: transferId !== null,
      select: (response) =>
        response.status === 200 ? response.data : undefined,
      refetchInterval: (query) => {
        const status = okData<TransferStatusSchema>(query.state.data)?.status;
        if (status === "completed") {
          void queryClient.invalidateQueries({
            queryKey: getListHubbleImagesQueryKey(),
          });
        }
        return isActiveTransfer(status) ? 1000 : false;
      },
    },
  });
}

export function useCancelTransfer() {
  const queryClient = useQueryClient();
  return useCancelImageTransfer({
    mutation: {
      onSuccess: (result) => {
        if (result.status !== 200) {
          return;
        }
        queryClient.setQueryData(
          getGetImageTransferQueryKey(result.data.transfer_id),
          result,
        );
      },
    },
  });
}

export function useResumeTransfer() {
  const queryClient = useQueryClient();
  return useResumeImageTransfer({
    mutation: {
      onSuccess: (result) => {
        if (result.status !== 200) {
          return;
        }
        queryClient.setQueryData(
          getGetImageTransferQueryKey(result.data.transfer_id),
          result,
        );
      },
    },
  });
}
