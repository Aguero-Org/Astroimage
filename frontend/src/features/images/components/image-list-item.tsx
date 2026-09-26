import { Link } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ImageRecord } from "../types";

type ImageListItemProps = {
  record: ImageRecord;
};

export function ImageListItem({ record }: Readonly<ImageListItemProps>) {
  return (
    <Link
      to="/image/$recordId/{-$slug}"
      params={{
        recordId: record.record_id,
        slug: record.slug === "" ? undefined : record.slug,
      }}
      data-testid="image-list-item-open"
      className="w-full cursor-pointer text-left"
    >
      <Card
        data-testid="image-list-item"
        className="pointer-events-none gap-3 py-4 transition-colors hover:bg-accent/50"
      >
        <CardHeader className="px-4">
          <CardTitle className="text-sm">{record.name}</CardTitle>
          {record.slug !== "" && record.slug !== record.name ? (
            <p
              data-testid="image-list-item-slug"
              className="text-xs text-muted-foreground"
            >
              {record.slug}
            </p>
          ) : null}
        </CardHeader>
        <CardContent className="flex items-center gap-2 px-4">
          <Badge variant="outline">{record.record_id.slice(0, 8)}…</Badge>
          <span className="text-xs text-muted-foreground">Ver imagen →</span>
        </CardContent>
      </Card>
    </Link>
  );
}
