import type { ReactNode } from "react";
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type SummaryCardProps = {
  title: ReactNode;
  detail?: ReactNode;
  meta: ReactNode;
  actions: ReactNode;
  testId?: string;
};

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
