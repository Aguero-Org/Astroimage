import type { ReactNode } from "react";
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

type SummaryCardProps = {
  title: ReactNode;
  detail?: ReactNode;
  meta: ReactNode;
  actions: ReactNode;
  testId?: string;
};

const FACT_WIDTHS = ["5rem", "4rem", "4.5rem", "7rem", "7rem", "4rem"];

export function SummaryCardSkeleton({ testId }: Readonly<{ testId?: string }>) {
  return (
    <li>
      <Card className="gap-2 py-3" data-testid={testId} aria-hidden>
        <CardHeader className="px-4">
          <CardTitle className="text-base">
            <Skeleton className="h-5 w-2/5" />
          </CardTitle>
          <CardDescription>
            <Skeleton className="h-4 w-1/4" />
          </CardDescription>
          <CardAction className="flex items-center gap-1">
            <Skeleton className="size-9 rounded-md" />
            <Skeleton className="size-9 rounded-md" />
          </CardAction>
        </CardHeader>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 px-4">
          {FACT_WIDTHS.map((width) => (
            <Skeleton
              key={width}
              className="h-4 rounded-md"
              style={{ width }}
            />
          ))}
        </div>
      </Card>
    </li>
  );
}

export function SummaryCard({
  title,
  detail,
  meta,
  actions,
  testId,
}: Readonly<SummaryCardProps>) {
  return (
    <li>
      <Card className="gap-2 py-3" data-testid={testId}>
        <CardHeader className="px-4">
          <CardTitle className="text-base">{title}</CardTitle>
          {detail !== undefined && <CardDescription>{detail}</CardDescription>}
          <CardAction className="flex items-center gap-1">{actions}</CardAction>
        </CardHeader>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 px-4">
          {meta}
        </div>
      </Card>
    </li>
  );
}
