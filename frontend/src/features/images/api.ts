import { useListHubbleImages } from "@/api/generated/hub/hub";

export function useImageRecords(query: string) {
  const params =
    query.trim().length > 0 ? { cuerpo_celeste: query } : undefined;
  return useListHubbleImages(params);
}
