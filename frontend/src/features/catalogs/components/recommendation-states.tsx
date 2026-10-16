import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type InfoProps = {
  testId: string;
  children: ReactNode;
};

export function RecommendationInfo({ testId, children }: Readonly<InfoProps>) {
  return (
    <p data-testid={testId} className="px-2 py-3 text-sm text-muted-foreground">
      {children}
    </p>
  );
}

const SKELETON_ROWS = [0, 1, 2];

export function RecommendationLoading() {
  return (
    <output
      data-testid="recommendations-loading"
      className="flex flex-col gap-2 px-2 py-3"
    >
      <span className="sr-only">
        Buscando catálogos y publicaciones para la región de esta imagen…
      </span>
      <div className="flex flex-col gap-2" aria-hidden>
        {SKELETON_ROWS.map((row) => (
          <article
            key={row}
            className="rounded-lg border border-sidebar-border bg-sidebar-accent/30 p-2"
          >
            <div className="flex items-start gap-2">
              <Skeleton className="mt-0.5 size-4 shrink-0 rounded-sm" />
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-3/5" />
                <Skeleton className="mt-1 h-3 w-2/5" />
                <Skeleton className="mt-1.5 h-4 w-20 rounded-full" />
                <Skeleton className="mt-1 h-3 w-full" />
                <Skeleton className="mt-1 h-3 w-4/5" />
              </div>
            </div>
          </article>
        ))}
      </div>
    </output>
  );
}

type ErrorProps = {
  message: string;
  onRetry: () => void;
};

export function RecommendationError({
  message,
  onRetry,
}: Readonly<ErrorProps>) {
  return (
    <div
      data-testid="recommendations-error"
      role="alert"
      className="flex flex-col items-start gap-2 px-2 py-3"
    >
      <p className="text-sm text-destructive">
        No se pudieron obtener las recomendaciones. {message}
      </p>
      <Button
        type="button"
        variant="outline"
        size="sm"
        data-testid="recommendations-retry"
        onClick={onRetry}
      >
        Reintentar
      </Button>
    </div>
  );
}
