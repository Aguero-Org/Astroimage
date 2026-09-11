import { useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchHubbleImage } from "@/api/generated/hub/hub";

export function useImageFetch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (q: string) => fetchHubbleImage({ query: q }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/image"] });
    },
  });
}
