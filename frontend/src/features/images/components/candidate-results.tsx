import {
  Calendar,
  File,
  Filter,
  HardDriveDownload,
  Hash,
  Telescope,
  Weight,
} from "lucide-react";
import { useState } from "react";
import type { CandidateSchema } from "@/api/generated/model";
import { BrandLoader } from "@/components/brand-loader";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  type CandidateSortField,
  useCandidateSearch,
  useSelectCandidate,
} from "../candidate-api";
import { MastSourceLink } from "../mast-source-link";
import { usePagedSort } from "../use-paged-sort";
import {
  CatalogCard,
  CatalogList,
  CatalogSort,
  type CatalogSortField,
} from "./catalog-card";
import { CatalogFacts, catalogLabels } from "./catalog-facts";
import { FilePager } from "./fits-file-table";
import { ImportNameDialog } from "./import-name-dialog";
import { TransferFeedback } from "./transfer-feedback";

const SORT_FIELDS: CatalogSortField<CandidateSortField>[] = [
  { field: "product_filename", label: catalogLabels.filename, icon: File },
  { field: "instrument", label: catalogLabels.instrument, icon: Telescope },
  { field: "proposal_id", label: catalogLabels.proposal, icon: Hash },
  { field: "filters", label: catalogLabels.filters, icon: Filter },
  { field: "size_bytes", label: catalogLabels.size, icon: Weight },
  { field: "observed_at", label: catalogLabels.observed, icon: Calendar },
];

type CandidateResultsProps = {
  query: string;
};

export function CandidateResults({ query }: Readonly<CandidateResultsProps>) {
  const { page, setPage, sort, order, toggleSort } =
    usePagedSort<CandidateSortField>("product_filename", "asc");
  const [transferIds, setTransferIds] = useState<string[]>([]);
  const [pending, setPending] = useState<CandidateSchema | null>(null);
  const search = useCandidateSearch(query, page, sort, order);
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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-medium">Archivos de Hubble</h2>
        {pageData && pageData.items.length > 0 && (
          <CatalogSort
            fields={SORT_FIELDS}
            sort={sort}
            order={order}
            onSort={toggleSort}
          />
        )}
      </div>
      {!!waiting && <BrandLoader label="Buscando en MAST…" />}
      {!!search.isError && (
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
        <CatalogList>
          {pageData.items.map((item) => (
            <CatalogCard
              key={item.data_uri}
              title={item.product_filename}
              meta={
                <CatalogFacts
                  instrument={item.instrument}
                  proposalId={item.proposal_id}
                  filters={item.filters}
                  observedAt={item.observed_at}
                  sizeBytes={item.size_bytes}
                />
              }
              actions={
                <>
                  <MastSourceLink dataUri={item.data_uri} />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        className="text-primary hover:bg-primary/10 hover:text-primary"
                        data-testid="import-candidate"
                        aria-label={`Importar ${item.product_filename}`}
                        disabled={select.isPending}
                        onClick={() => setPending(item)}
                      >
                        <HardDriveDownload className="size-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      Importar {item.product_filename}
                    </TooltipContent>
                  </Tooltip>
                </>
              }
            />
          ))}
        </CatalogList>
      )}
      {pageData !== null && (
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
