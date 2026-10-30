import { keepPreviousData, useQueryClient } from "@tanstack/react-query";
import {
  useImportFitsFiles,
  useImportFitsFromUrl,
} from "@/api/generated/fits/fits";
import {
  getGetImageInfoQueryKey,
  getListHubbleImagesQueryKey,
  useDeleteHubbleImage,
  useGetImageInfo,
  useListHubbleImages,
  usePatchImageRecord as usePatchImageRecordMutation,
} from "@/api/generated/hub/hub";
import type {
  DetectSourcesParams,
  ListHubbleImagesSort,
  RenderFitsHistogramParams,
  RenderFitsImageParams,
} from "@/api/generated/model";
import {
  useRenderFitsHistogram,
  useRenderFitsImage,
} from "@/api/generated/render/render";
import {
  useDetectSources,
  useGetBestPreset,
} from "@/api/generated/sources/sources";

export type RecordSortField = ListHubbleImagesSort;

export function useImageRecords(
  query: string,
  page = 1,
  sort: RecordSortField = "created_at",
  order: "asc" | "desc" = "desc",
) {
  const cuerpoCeleste = query.trim();
  return useListHubbleImages(
    {
      cuerpo_celeste: cuerpoCeleste.length > 0 ? cuerpoCeleste : undefined,
      page,
      limit: 8,
      sort,
      order,
    },
    {
      query: {
        placeholderData: keepPreviousData,
      },
    },
  );
}

export function useImageInfo(recordId: string) {
  return useGetImageInfo(recordId);
}

export function useImageRender(
  recordId: string,
  params: RenderFitsImageParams,
) {
  return useRenderFitsImage(recordId, params, {
    query: {
      retry: false,
      structuralSharing: false,
      gcTime: 60_000,
    },
  });
}

export function useImageHistogram(
  recordId: string,
  params: RenderFitsHistogramParams,
  enabled: boolean,
) {
  return useRenderFitsHistogram(recordId, params, {
    query: {
      enabled,
      retry: false,
    },
  });
}

export function useSourceDetection(
  recordId: string,
  params: DetectSourcesParams,
  enabled: boolean,
) {
  return useDetectSources(recordId, params, {
    query: {
      enabled,
      retry: false,
    },
  });
}

export function useBestPreset(recordId: string, hdu: number | null) {
  return useGetBestPreset(recordId, hdu === null ? undefined : { hdu }, {
    query: {
      enabled: false,
      retry: false,
    },
  });
}

export function usePatchImageRecord() {
  const queryClient = useQueryClient();
  return usePatchImageRecordMutation({
    mutation: {
      onSuccess: async (_data, variables) => {
        await queryClient.invalidateQueries({
          queryKey: getListHubbleImagesQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getGetImageInfoQueryKey(variables.recordId),
        });
      },
    },
  });
}

export function useDeleteImage() {
  const queryClient = useQueryClient();
  return useDeleteHubbleImage({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getListHubbleImagesQueryKey(),
        });
      },
    },
  });
}

function useRefreshImageList() {
  const queryClient = useQueryClient();
  return async () => {
    await queryClient.invalidateQueries({
      queryKey: getListHubbleImagesQueryKey(),
    });
  };
}

export function useImportLocalFits() {
  const refresh = useRefreshImageList();
  return useImportFitsFiles({
    mutation: {
      onSuccess: refresh,
    },
  });
}

export function useImportFitsUrl() {
  const refresh = useRefreshImageList();
  return useImportFitsFromUrl({
    mutation: {
      onSuccess: refresh,
    },
  });
}
