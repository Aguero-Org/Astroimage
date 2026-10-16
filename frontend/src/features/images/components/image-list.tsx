import { Link } from "@tanstack/react-router";
import {
  Calendar,
  CalendarPlus,
  File,
  Filter,
  Hash,
  Telescope,
  Trash2,
  Type,
  Weight,
} from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FilePager } from "@/components/ui/file-pager";
import { HelpHint } from "@/components/ui/help-hint";
import { SortControls, type SortField } from "@/components/ui/sort-controls";
import { SummaryCard, SummaryCardSkeleton } from "@/components/ui/summary-card";
import { glossaryPath } from "@/features/glossary/entries";
import { type RecordSortField, useDeleteImage, useImageRecords } from "../api";
import { MastSourceLink } from "../mast-source-link";
import { usePagedSort } from "../use-paged-sort";
import { CatalogFacts, catalogLabels } from "./catalog-facts";
import { DeleteImageDialog } from "./delete-image-dialog";

const filenameGlossary = { glossaryId: "slug-archivo" } as const;

type ImageListProps = {
  query: string;
};

type ViewerRecord = {
  record_id: string;
  slug: string;
};

function RecordViewerLink({
  record,
  className,
  testId,
  children,
}: Readonly<{
  record: ViewerRecord;
  className?: string;
  testId?: string;
  children: ReactNode;
}>) {
  return (
    <Link
      to="/image/$recordId/{-$slug}"
      params={{
        recordId: record.record_id,
        slug: record.slug === "" ? undefined : record.slug,
      }}
      data-testid={testId}
      className={className}
    >
      {children}
    </Link>
  );
}

const SKELETON_ROWS = [0, 1, 2];

const SORT_FIELDS: SortField<RecordSortField>[] = [
  { field: "display_name", label: catalogLabels.displayName, icon: Type },
  { field: "product_filename", label: catalogLabels.filename, icon: File },
  { field: "instrument", label: catalogLabels.instrument, icon: Telescope },
  { field: "proposal_id", label: catalogLabels.proposal, icon: Hash },
  { field: "filters", label: catalogLabels.filters, icon: Filter },
  { field: "observed_at", label: catalogLabels.observed, icon: Calendar },
  { field: "created_at", label: catalogLabels.imported, icon: CalendarPlus },
  { field: "size_bytes", label: catalogLabels.size, icon: Weight },
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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-1 text-sm font-medium">
          Imágenes disponibles
          <HelpHint label="FITS" testId="help-fits" glossaryId="fits">
            Cada ficha es un FITS guardado. El{" "}
            <a
              href={glossaryPath(filenameGlossary.glossaryId)}
              className="underline"
            >
              nombre de archivo
            </a>{" "}
            abre el visor.
          </HelpHint>
        </h2>
        {!isPending && !isError && records.length > 0 && (
          <SortControls
            fields={SORT_FIELDS}
            sort={sort}
            order={order}
            onSort={toggleSort}
          />
        )}
      </div>
      {!!isPending && (
        <output className="block">
          <span className="sr-only">Cargando imágenes…</span>
          <ul
            data-testid="image-list-skeleton"
            className="flex w-full flex-col gap-3"
            aria-hidden
          >
            {SKELETON_ROWS.map((row) => (
              <SummaryCardSkeleton key={row} />
            ))}
          </ul>
        </output>
      )}
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
            {"."}
          </p>
        ))}
      {!isPending && !isError && records.length > 0 && (
        <ul data-testid="image-list" className="flex w-full flex-col gap-3">
          {records.map((record) => (
            <SummaryCard
              key={record.record_id}
              testId="image-list-item"
              title={
                <RecordViewerLink record={record} className="hover:underline">
                  {record.display_name}
                </RecordViewerLink>
              }
              detail={
                <RecordViewerLink
                  record={record}
                  testId="image-list-item-open"
                  className="text-primary underline-offset-2 hover:underline dark:text-ring"
                >
                  {record.name}
                </RecordViewerLink>
              }
              meta={
                <CatalogFacts
                  instrument={record.instrument}
                  proposalId={record.proposal_id}
                  filters={record.filters}
                  observedAt={record.observed_at}
                  importedAt={record.created_at}
                  sizeBytes={record.size_bytes}
                />
              }
              actions={
                <>
                  <MastSourceLink dataUri={record.data_uri} />
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    className="text-destructive hover:bg-destructive/10 hover:text-destructive"
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
                </>
              }
            />
          ))}
        </ul>
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
