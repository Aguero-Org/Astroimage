import { useGetImageInfo } from "@/api/generated/hub/hub";
import { Skeleton } from "@/components/ui/skeleton";

type ImageInfoProps = {
  recordId: string;
};

export function ImageInfo({ recordId }: ImageInfoProps) {
  const infoQuery = useGetImageInfo(recordId);
  const info = infoQuery.data?.status === 200 ? infoQuery.data.data : undefined;

  if (infoQuery.isPending) {
    return <Skeleton className="h-32 w-full rounded-xl" />;
  }

  if (!info) {
    return null;
  }

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">Metadatos</h2>
      <pre className="overflow-auto rounded bg-muted p-4 text-sm">
        {JSON.stringify(info, null, 2)}
      </pre>
    </section>
  );
}
