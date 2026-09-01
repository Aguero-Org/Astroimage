import { Skeleton } from "@/components/ui/skeleton";
import { useImageRecords } from "../api";
import { ImageListItem } from "./image-list-item";

type ImageListProps = {
  query: string;
};

export function ImageList({ query }: ImageListProps) {
  const { data: response, isPending, isError } = useImageRecords(query);

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

  const records = response?.status === 200 ? response.data.records : [];

  if (records.length === 0) {
    return (
      <p className="mx-auto max-w-lg text-sm text-muted-foreground">
        No images found.
      </p>
    );
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-2">
      {records.map((record) => (
        <ImageListItem key={record.record_id} record={record} />
      ))}
    </div>
  );
}
