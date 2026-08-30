import { Skeleton } from "@/components/ui/skeleton";
import { useImageSearch } from "../api";
import { ImageListItem } from "./image-list-item";

type ImageListProps = {
  query: string;
};

export function ImageList({ query }: ImageListProps) {
  const { data, isPending, isError } = useImageSearch(query);

  if (query.trim().length === 0) {
    return null;
  }

  if (isPending) {
    return (
      <div className="mx-auto flex max-w-lg flex-col gap-2">
        {["a", "b", "c"].map((key) => (
          <Skeleton key={key} className="h-16 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <p className="mx-auto max-w-lg text-sm text-destructive">
        Something went wrong.
      </p>
    );
  }

  if (data == null || data.length === 0) {
    return (
      <p className="mx-auto max-w-lg text-sm text-muted-foreground">
        No images found.
      </p>
    );
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-2">
      {data.map((image) => (
        <ImageListItem key={image.id} image={image} />
      ))}
    </div>
  );
}
