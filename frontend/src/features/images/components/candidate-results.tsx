import { HardDriveDownload } from "lucide-react";
import { useState } from "react";
import type { CandidateSchema } from "@/api/generated/model";
import { BrandLoader } from "@/components/brand-loader";
import { Button } from "@/components/ui/button";
import {
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@/components/ui/table";
import {
  type CandidateSortField,
  type CandidateSortOrder,
  formatBytes,
  useCandidateSearch,
  useSelectCandidate,
} from "../candidate-api";
import { formatWhen } from "../format-when";
import { MastSourceLink } from "../mast-source-link";
import { FilePager, FitsFileTable } from "./fits-file-table";
import { ImportNameDialog } from "./import-name-dialog";
import { TransferFeedback } from "./transfer-feedback";

const COLUMNS: { field: CandidateSortField; label: string }[] = [
  { field: "product_filename", label: "Archivo" },
  { field: "instrument", label: "Instrumento" },
  { field: "proposal_id", label: "Propuesta" },
  { field: "filters", label: "Filtros" },
  { field: "size_bytes", label: "Tamaño" },
  { field: "observed_at", label: "Observada" },
];

type CandidateResultsProps = {
  query: string;
};

export function CandidateResults({ query }: Readonly<CandidateResultsProps>) {
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<CandidateSortField>("product_filename");
  const [order, setOrder] = useState<CandidateSortOrder>("asc");
  const [transferIds, setTransferIds] = useState<string[]>([]);
  const [pending, setPending] = useState<CandidateSchema | null>(null);
  const search = useCandidateSearch(query, page, sort, order);

  function toggleSort(field: CandidateSortField) {
    if (field === sort) {
      setOrder((current) => (current === "asc" ? "desc" : "asc"));
    } else {
      setSort(field);
      setOrder("asc");
    }
    setPage(1);
  }
  const select = useSelectCandidate();

  if (query.trim().length === 0) {
    return null;
  }

  const received = search.data?.status === 200 ? search.data.data : null;
  const pageData =
    received !== null &&
    received.sort === sort &&
    received.order === order &&
    received.page === page
      ? received
      : null;
  const waiting = pageData === null && (search.isPending || search.isFetching);

  return (
    <section className="flex w-full flex-col gap-3">
      <h2 className="text-sm font-medium">Archivos de Hubble</h2>
      {waiting && <BrandLoader label="Buscando en MAST…" />}
      {search.isError && (
        <p className="text-sm text-destructive">
          No se pudo buscar candidatos para{" "}
          <strong className="font-semibold">{query.trim()}</strong>.
        </p>
      )}
      {pageData && pageData.items.length === 0 && (
        <p className="text-sm text-muted-foreground">
          MAST no devolvió archivos de ciencia para{" "}
          <strong className="font-semibold text-foreground">
            {query.trim()}
          </strong>
          .
        </p>
      )}
      {pageData && pageData.items.length > 0 && (
        <FitsFileTable
          columns={COLUMNS}
          sort={sort}
          order={order}
          onSort={(field) => toggleSort(field as CandidateSortField)}
          trailingHead={
            <>
              <TableHead>Fuente</TableHead>
              <TableHead />
            </>
          }
        >
          <TableBody>
            {pageData.items.map((item) => (
              <TableRow key={item.data_uri}>
                <TableCell>{item.product_filename}</TableCell>
                <TableCell>{item.instrument ?? "—"}</TableCell>
                <TableCell>{item.proposal_id}</TableCell>
                <TableCell>{item.filters ?? "—"}</TableCell>
                <TableCell>{formatBytes(item.size_bytes)}</TableCell>
                <TableCell>{formatWhen(item.observed_at)}</TableCell>
                <TableCell>
                  <MastSourceLink dataUri={item.data_uri} />
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    type="button"
                    size="sm"
                    data-testid="import-candidate"
                    disabled={select.isPending}
                    onClick={() => setPending(item)}
                  >
                    <HardDriveDownload className="size-4" />
                    Importar
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </FitsFileTable>
      )}
      {pageData && (
        <FilePager
          page={page}
          hasMore={pageData.has_more === true}
          onPage={setPage}
        />
      )}
      <ImportNameDialog
        key={pending?.data_uri ?? "none"}
        filename={pending?.product_filename ?? null}
        pending={select.isPending}
        onCancel={() => setPending(null)}
        onConfirm={(displayName) => {
          if (pending === null) {
            return;
          }
          void select
            .mutateAsync({
              data: {
                candidate_token: pending.token,
                display_name: displayName,
              },
            })
            .then((result) => {
              if (result.status !== 200) {
                return;
              }
              const transferId = result.data.transfer_id;
              setTransferIds((current) =>
                current.includes(transferId)
                  ? current
                  : [...current, transferId],
              );
              setPending(null);
            });
        }}
      />
      {transferIds.map((transferId) => (
        <TransferFeedback key={transferId} transferId={transferId} />
      ))}
    </section>
  );
}
