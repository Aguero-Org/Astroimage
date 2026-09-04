import { useNavigate } from "@tanstack/react-router";
import { Skeleton } from "@/components/ui/skeleton";
import { useImageRecords } from "../api";
import { ImageListItem } from "./image-list-item";

type ImageListProps = {
  query: string;
  isFetching: boolean;
  fetchError: Error | null;
};

export function ImageList({
  query,
  isFetching,
  fetchError,
}: Readonly<ImageListProps>) {
  const navigate = useNavigate();
  const { data: response, isPending, isError } = useImageRecords(query);

  if (isPending) {
    return (
      <div className="mx-auto flex max-w-lg flex-col gap-2">
        {["a", "b", "c"].map((key) => (
          <Skeleton key={key} className="h-16 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <p className="mx-auto max-w-lg text-sm text-destructive">
        Algo salió mal.
      </p>
    );
  }

  if (isFetching) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center gap-3">
        <Skeleton className="h-16 w-full rounded-xl" />
        <p className="text-sm text-muted-foreground">
          Obteniendo del archivo Hubble…
        </p>
      </div>
    );
  }

  if (fetchError) {
    return (
      <p className="mx-auto max-w-lg text-sm text-destructive">
        Error al obtener: {fetchError.message}
      </p>
    );
  }

  const records = response?.status === 200 ? response.data.records : [];

  if (records.length === 0) {
    return (
      <p className="mx-auto max-w-lg text-sm text-muted-foreground">
        No se encontraron imágenes. Intenta buscar un cuerpo celeste (ej. M31).
      </p>
    );
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-2">
      {records.map((record) => (
        <ImageListItem
          key={record.record_id}
          record={record}
          onSelect={(id) =>
            navigate({ to: "/image/$recordId", params: { recordId: id } })
          }
        />
      ))}
    </div>
  );
}
