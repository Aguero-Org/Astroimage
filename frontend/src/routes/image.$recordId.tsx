import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useGetImageInfo } from "@/api/generated/hub/hub";
import { useRenderFitsImage } from "@/api/generated/render/render";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createFileRoute("/image/$recordId")({
  component: ImageDetailPage,
});

function ImageDetailPage() {
  const { recordId } = Route.useParams();

  const renderQuery = useRenderFitsImage(recordId);
  const infoQuery = useGetImageInfo(recordId);

  const blob =
    renderQuery.data?.status === 200
      ? (renderQuery.data.data as Blob)
      : undefined;
  const objectUrl = useObjectUrl(blob);
  const info = infoQuery.data?.status === 200 ? infoQuery.data.data : undefined;

  return (
    <main className="flex min-h-svh justify-center p-6">
      <Card className="w-full max-w-4xl">
        <CardHeader>
          <CardTitle className="text-2xl">
            {info?.source_name ?? recordId}
          </CardTitle>
        </CardHeader>

        <CardContent className="flex flex-col gap-6">
          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-medium">Rendered image</h2>
            {renderQuery.isPending ? (
              <div className="flex flex-col gap-2">
                <Skeleton className="h-96 w-full rounded-xl" />
                <p className="text-sm text-muted-foreground">
                  Rendering image…
                </p>
              </div>
            ) : renderQuery.isError ? (
              <p className="text-sm text-destructive">
                Failed to render: {String(renderQuery.error)}
              </p>
            ) : objectUrl ? (
              <img
                src={objectUrl}
                alt={info?.source_name ?? recordId}
                className="max-w-full rounded border"
              />
            ) : (
              <p className="text-sm text-muted-foreground">
                No image available.
              </p>
            )}
          </section>

          {infoQuery.isPending ? (
            <Skeleton className="h-32 w-full rounded-xl" />
          ) : info ? (
            <section className="flex flex-col gap-2">
              <h2 className="text-lg font-medium">Metadata</h2>
              <pre className="overflow-auto rounded bg-muted p-4 text-sm">
                {JSON.stringify(info, null, 2)}
              </pre>
            </section>
          ) : null}
        </CardContent>
      </Card>
    </main>
  );
}

function useObjectUrl(blob: Blob | undefined): string | undefined {
  const [url, setUrl] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!blob) {
      setUrl(undefined);
      return;
    }
    const next = URL.createObjectURL(blob);
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [blob]);

  return url;
}
