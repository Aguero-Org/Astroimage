import { keepPreviousData, useQueryClient } from "@tanstack/react-query";
import {
  getListHubbleImagesQueryKey,
  useDeleteHubbleImage,
  useListHubbleImages,
} from "@/api/generated/hub/hub";
import type { ListHubbleImagesSort } from "@/api/generated/model";

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
    { query: { placeholderData: keepPreviousData } },
  );
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
