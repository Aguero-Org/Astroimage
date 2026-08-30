import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ImageSummary } from "../types";

type ImageListItemProps = {
  image: ImageSummary;
};

export function ImageListItem({ image }: ImageListItemProps) {
  return (
    <Card className="gap-3 py-4">
      <CardHeader className="px-4">
        <CardTitle className="text-sm">{image.name}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-2 px-4">
        <Badge variant="secondary">{image.filter}</Badge>
        <Badge variant="outline">
          {image.width}×{image.height}
        </Badge>
        <span className="text-xs text-muted-foreground">
          {image.exposure}s · {image.dateObs.split("T")[0]}
        </span>
      </CardContent>
    </Card>
  );
}
