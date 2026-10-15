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

export function RecommendationLoading() {
  return (
    <div
      data-testid="recommendations-loading"
      aria-live="polite"
      className="flex flex-col gap-2 px-2 py-3"
    >
      <p className="text-sm text-muted-foreground">
        Buscando catálogos y publicaciones para la región de esta imagen…
      </p>
      {[0, 1, 2].map((row) => (
        <Skeleton key={row} className="h-16 w-full rounded-lg" />
      ))}
    </div>
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
