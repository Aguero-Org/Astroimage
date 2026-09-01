import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ImageRecord } from "../types";

type ImageListItemProps = {
  record: ImageRecord;
  onSelect: (recordId: string) => void;
};

export function ImageListItem({ record, onSelect }: ImageListItemProps) {
  return (
    <Card
      className="cursor-pointer gap-3 py-4 transition-colors hover:bg-accent/50"
      role="button"
      tabIndex={0}
      onClick={() => onSelect(record.record_id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(record.record_id);
        }
      }}
    >
      <CardHeader className="px-4">
        <CardTitle className="text-sm">{record.name}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-2 px-4">
        <Badge variant="outline">{record.record_id.slice(0, 8)}…</Badge>
        <span className="text-xs text-muted-foreground">View image →</span>
      </CardContent>
    </Card>
  );
}
