import { Link } from "@tanstack/react-router";
import { Trash2 } from "lucide-react";
import { useState } from "react";
import { BrandLoader } from "@/components/brand-loader";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import {
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@/components/ui/table";
import { type RecordSortField, useDeleteImage, useImageRecords } from "../api";
import { formatBytes } from "../candidate-api";
import { formatWhen } from "../format-when";
import { MastSourceLink } from "../mast-source-link";
import { usePagedSort } from "../use-paged-sort";
import { DeleteImageDialog } from "./delete-image-dialog";
import { FilePager, FitsFileTable } from "./fits-file-table";

type ImageListProps = {
  query: string;
};

const COLUMNS: { field: RecordSortField; label: string }[] = [
  { field: "display_name", label: "Nombre" },
  { field: "product_filename", label: "Archivo" },
  { field: "instrument", label: "Instrumento" },
  { field: "proposal_id", label: "Propuesta" },
  { field: "filters", label: "Filtros" },
  { field: "observed_at", label: "Observada" },
  { field: "created_at", label: "Importada" },
  { field: "size_bytes", label: "Tamaño" },
];

export function ImageList({ query }: Readonly<ImageListProps>) {
  const { page, setPage, sort, order, toggleSort } =
    usePagedSort<RecordSortField>("created_at", "desc");
  const [pendingDelete, setPendingDelete] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const {
    data: response,
    isPending,
    isError,
  } = useImageRecords(query, page, sort, order);
  const remove = useDeleteImage();
  const pageData = response?.status === 200 ? response.data : null;
  const records = pageData?.records ?? [];

  return (
    <section className="flex w-full flex-col gap-2">
      <h2 className="flex items-center gap-1 text-sm font-medium">
        Imágenes disponibles
        <HelpHint label="FITS" testId="help-fits" glossaryId="fits">
          Cada fila es un FITS guardado. Se abre como imagen y sus metadatos van
          al inspector.
        </HelpHint>
      </h2>
      {!!isPending && <BrandLoader label="Cargando imágenes…" />}
      {!!isError && <p className="text-sm text-destructive">Algo salió mal.</p>}
      {!isPending &&
        !isError &&
        records.length === 0 &&
        (query.trim().length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No hay imágenes cargadas en el servidor.
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">
            No se encontraron imágenes para{" "}
            <strong className="font-semibold text-foreground">
              {query.trim()}
            </strong>
            .
          </p>
        ))}
      {!isPending && !isError && records.length > 0 && (
        <FitsFileTable
          testId="image-list"
          columns={COLUMNS.map((column) =>
            column.field === "product_filename"
              ? {
                  ...column,
                  hint: (
                    <HelpHint
                      label="Nombre de archivo"
                      testId="help-slug-archivo"
                      glossaryId="slug-archivo"
                    >
                      Nombre con el que se guardó el FITS. El enlace abre el
                      visor.
                    </HelpHint>
                  ),
                }
              : column,
          )}
          sort={sort}
          order={order}
          onSort={toggleSort}
          trailingHead={
            <>
              <TableHead>Fuente</TableHead>
              <TableHead />
            </>
          }
        >
          <TableBody>
            {records.map((record) => (
              <TableRow key={record.record_id} data-testid="image-list-item">
                <TableCell>{record.display_name}</TableCell>
                <TableCell>
                  <Link
                    to="/image/$recordId/{-$slug}"
                    params={{
                      recordId: record.record_id,
                      slug: record.slug === "" ? undefined : record.slug,
                    }}
                    data-testid="image-list-item-open"
                    className="text-primary underline-offset-2 hover:underline dark:text-ring"
                  >
                    {record.name}
                  </Link>
                </TableCell>
                <TableCell>{record.instrument ?? "—"}</TableCell>
                <TableCell>{record.proposal_id}</TableCell>
                <TableCell>{record.filters ?? "—"}</TableCell>
                <TableCell>{formatWhen(record.observed_at)}</TableCell>
                <TableCell>{formatWhen(record.created_at)}</TableCell>
                <TableCell>{formatBytes(record.size_bytes)}</TableCell>
                <TableCell>
                  <MastSourceLink dataUri={record.data_uri} />
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    aria-label={`Eliminar ${record.display_name}`}
                    data-testid="delete-image"
                    onClick={() =>
                      setPendingDelete({
                        id: record.record_id,
                        name: record.display_name,
                      })
                    }
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </FitsFileTable>
      )}
      {pageData !== null && (
        <FilePager
          page={page}
          hasMore={pageData.has_more === true}
          onPage={setPage}
        />
      )}
      <DeleteImageDialog
        target={pendingDelete}
        isPending={remove.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={(id) => {
          void remove.mutateAsync({ recordId: id }).then(() => {
            setPendingDelete(null);
          });
        }}
      />
    </section>
  );
}
