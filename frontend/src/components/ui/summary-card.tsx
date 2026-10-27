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
  media?: ReactNode;
  testId?: string;
};

const FACT_WIDTHS = [
  ["instrument", "5rem"],
  ["proposal", "4rem"],
  ["filters", "4.5rem"],
  ["observed", "7rem"],
  ["imported", "7rem"],
  ["size", "4rem"],
] as const;

function FactSkeletons() {
  return FACT_WIDTHS.map(([name, width]) => (
    <Skeleton key={name} className="h-4 rounded-md" style={{ width }} />
  ));
}

export function SummaryCardSkeleton({
  testId,
  preview = false,
}: Readonly<{ testId?: string; preview?: boolean }>) {
  const header = preview ? (
    <div className="flex items-start gap-3">
      <div className="min-w-0 flex-1 space-y-1">
        <Skeleton className="h-4 w-2/5" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <div className="flex items-center gap-1">
        <Skeleton className="size-8 rounded-md" />
        <Skeleton className="size-8 rounded-md" />
        <Skeleton className="size-8 rounded-md" />
      </div>
    </div>
  ) : (
    <CardHeader className="px-4">
      <CardTitle className="text-base">
        <Skeleton className="h-5 w-2/5" />
      </CardTitle>
      <CardDescription>
        <Skeleton className="h-3 w-1/3" />
      </CardDescription>
      <CardAction className="flex items-center gap-1">
        <Skeleton className="size-9 rounded-md" />
        <Skeleton className="size-9 rounded-md" />
      </CardAction>
    </CardHeader>
  );
  const facts = (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      {preview ? <Skeleton className="h-5 w-16 rounded-full" /> : null}
      <FactSkeletons />
    </div>
  );
  return (
    <li>
      <Card
        className={
          preview
            ? "flex-row items-stretch gap-0 overflow-hidden p-0"
            : "gap-2 py-3"
        }
        data-testid={testId}
        aria-hidden
      >
        {preview ? <Skeleton className="size-32 shrink-0" /> : null}
        {preview ? (
          <div className="flex min-w-0 flex-1 flex-col gap-2 p-3">
            {header}
            {facts}
          </div>
        ) : (
          <>
            {header}
            <div className="px-4">{facts}</div>
          </>
        )}
      </Card>
    </li>
  );
}

export function SummaryCard({
  title,
  detail,
  meta,
  actions,
  media,
  testId,
}: Readonly<SummaryCardProps>) {
  const header =
    media !== undefined ? (
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-sm leading-none font-semibold">{title}</div>
          {detail !== undefined && (
            <div className="mt-1 text-xs leading-none text-muted-foreground">
              {detail}
            </div>
          )}
        </div>
        <div className="flex shrink-0 items-center">{actions}</div>
      </div>
    ) : (
      <CardHeader className="px-4">
        <CardTitle className="text-base">{title}</CardTitle>
        {detail !== undefined && <CardDescription>{detail}</CardDescription>}
        <CardAction className="flex items-center gap-1">{actions}</CardAction>
      </CardHeader>
    );
  const facts = (
    <div
      className={`flex flex-wrap items-center gap-x-3 gap-y-1 ${media !== undefined ? "" : "px-4"}`}
    >
      {meta}
    </div>
  );
  return (
    <li>
      <Card
        className={
          media !== undefined
            ? "flex-row items-stretch gap-0 overflow-hidden p-0"
            : "gap-2 py-3"
        }
        data-testid={testId}
      >
        {media}
        {media !== undefined ? (
          <div className="flex min-w-0 flex-1 flex-col gap-2 p-3">
            {header}
            {facts}
          </div>
        ) : (
          <>
            {header}
            {facts}
          </>
        )}
      </Card>
    </li>
  );
}
