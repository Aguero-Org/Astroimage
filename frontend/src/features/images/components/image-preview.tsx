import { useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { apiBaseUrl } from "@/lib/api-client";

type ImagePreviewProps = {
  recordId: string;
  name: string;
};

export function ImagePreview({ recordId, name }: Readonly<ImagePreviewProps>) {
  const [phase, setPhase] = useState<"loading" | "ready" | "hidden">("loading");
  const src = `${apiBaseUrl()}/image/${recordId}/preview?size=256`;
  return (
    <div className="relative size-16 shrink-0 overflow-hidden rounded-md bg-muted">
      {phase === "loading" ? (
        <Skeleton
          className="absolute inset-0 size-16"
          data-testid="image-preview-skeleton"
        />
      ) : null}
      {phase === "hidden" ? null : (
        <img
          src={src}
          alt={name}
          width={64}
          height={64}
          className="size-16 object-cover"
          data-testid="image-preview"
          onLoad={() => setPhase("ready")}
          onError={() => setPhase("hidden")}
        />
      )}
    </div>
  );
}
