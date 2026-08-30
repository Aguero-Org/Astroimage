import { useQuery } from "@tanstack/react-query";
import { customFetch } from "@/lib/api-client";
import type { ImageSummary } from "./types";

export function getImageSearchQueryKey(query: string) {
  return ["image-search", query] as const;
}

export function useImageSearch(query: string) {
  return useQuery({
    queryKey: getImageSearchQueryKey(query),
    queryFn: async () => {
      const result = await customFetch<{
        data: ImageSummary[];
        status: number;
      }>(`/image/search?query=${encodeURIComponent(query)}`);
      return result.data;
    },
    enabled: query.trim().length > 0,
  });
}
