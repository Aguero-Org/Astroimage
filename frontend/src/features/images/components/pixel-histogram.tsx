import type { HistogramResponse } from "@/api/generated/model";
import { HelpHint } from "@/components/ui/help-hint";
import { Skeleton } from "@/components/ui/skeleton";

type PixelHistogramProps = {
  histogram: HistogramResponse | undefined;
  isPending: boolean;
  isError: boolean;
  pmin: number;
  pmax: number;
  showPercentiles: boolean;
};

function percentileIndex(counts: number[], percentile: number): number {
  const total = counts.reduce((sum, count) => sum + count, 0);
  if (total <= 0 || counts.length === 0) {
    return 0;
  }
  const target = (total * percentile) / 100;
  let accumulated = 0;
  for (const [index, count] of counts.entries()) {
    accumulated += count;
    if (accumulated >= target) {
      return index;
    }
  }
  return counts.length - 1;
}

export function PixelHistogram({
  histogram,
  isPending,
  isError,
  pmin,
  pmax,
  showPercentiles,
}: Readonly<PixelHistogramProps>) {
  if (isPending) {
    return <Skeleton data-testid="histogram-loading" className="h-16 w-full" />;
  }
  if (isError || !histogram || histogram.counts.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">
        No hay histograma disponible.
      </p>
    );
  }

  const maxCount = Math.max(...histogram.counts, 1);
  const barCount = histogram.counts.length;
  const lowIndex = percentileIndex(histogram.counts, pmin);
  const highIndex = percentileIndex(histogram.counts, pmax);

  return (
    <div data-testid="pixel-histogram" className="mb-3 flex flex-col gap-1">
      <div className="flex items-center gap-1 text-xs font-medium">
        Histograma
        <HelpHint label="Histograma" testId="help-histogram">
          Distribución de valores de píxel del HDU actual. Las líneas marcan los
          percentiles Pmin y Pmax usados al recortar el render.
        </HelpHint>
      </div>
      <svg
        viewBox={`0 0 ${barCount} 1`}
        preserveAspectRatio="none"
        className="h-16 w-full rounded-md bg-muted"
        aria-labelledby="pixel-histogram-title"
      >
        <title id="pixel-histogram-title">Histograma de píxeles</title>
        {histogram.counts.map((count, index) => {
          const height = count / maxCount;
          return (
            <rect
              key={`${histogram.bin_centers[index]}-${count}`}
              x={index}
              y={1 - height}
              width={1}
              height={height}
              className="fill-primary"
            />
          );
        })}
        {showPercentiles ? (
          <>
            <line
              x1={lowIndex + 0.5}
              x2={lowIndex + 0.5}
              y1={0}
              y2={1}
              className="stroke-accent"
              strokeWidth={barCount / 80}
            />
            <line
              x1={highIndex + 0.5}
              x2={highIndex + 0.5}
              y1={0}
              y2={1}
              className="stroke-accent"
              strokeWidth={barCount / 80}
            />
          </>
        ) : null}
      </svg>
      <p className="flex justify-between text-[0.65rem] text-muted-foreground">
        <span data-testid="histogram-min">
          {histogram.minimum.toPrecision(4)}
        </span>
        <span data-testid="histogram-max">
          {histogram.maximum.toPrecision(4)}
        </span>
      </p>
    </div>
  );
}
