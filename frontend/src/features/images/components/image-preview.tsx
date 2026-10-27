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
    <div className="relative size-32 shrink-0 overflow-hidden bg-muted">
      <img
        src={src}
        alt={name}
        className={`absolute inset-0 size-full object-cover ${phase === "hidden" ? "invisible" : ""}`}
        data-testid="image-preview"
        onLoad={() => setPhase("ready")}
        onError={() => setPhase("hidden")}
      />
      {phase === "loading" ? (
        <Skeleton
          className="absolute inset-0 size-full"
          data-testid="image-preview-skeleton"
        />
      ) : null}
    </div>
  );
}
