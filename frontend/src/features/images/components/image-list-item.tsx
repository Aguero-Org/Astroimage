import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ImageRecord } from "../types";

type ImageListItemProps = {
  record: ImageRecord;
};

export function ImageListItem({ record }: ImageListItemProps) {
  return (
    <Card className="gap-3 py-4">
      <CardHeader className="px-4">
        <CardTitle className="text-sm">{record.name}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-2 px-4">
        <Badge variant="outline">{record.record_id}</Badge>
      </CardContent>
    </Card>
  );
}
