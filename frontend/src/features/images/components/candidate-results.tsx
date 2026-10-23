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
import { useSelectHubbleCandidate } from "@/api/generated/hub/hub";
import type { CandidateSchema } from "@/api/generated/model";
import { Button } from "@/components/ui/button";
import { FilePager } from "@/components/ui/file-pager";
import { SortControls, type SortField } from "@/components/ui/sort-controls";
import { SummaryCard, SummaryCardSkeleton } from "@/components/ui/summary-card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { type CandidateSortField, useCandidateSearch } from "../candidate-api";
import { MastSourceLink } from "../mast-source-link";
import { resultsView } from "../results-view";
import { usePagedSort } from "../use-paged-sort";
import { CatalogFacts, catalogLabels } from "./catalog-facts";
import { ImportNameDialog } from "./import-name-dialog";
import { TransferFeedback } from "./transfer-feedback";

const SKELETON_ROWS = [0, 1, 2];

const SORT_FIELDS: SortField<CandidateSortField>[] = [
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
  const [importing, setImporting] = useState<CandidateSchema | null>(null);
  const search = useCandidateSearch(query, page, sort, order);
  const select = useSelectHubbleCandidate();

  if (query.trim().length === 0) {
    return null;
  }

  const view = resultsView(search, {
    isEmpty: (page) => page.items.length === 0,
  });

  return (
    <section className="flex w-full flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-medium">Archivos de Hubble</h2>
        {view.status === "ready" && (
          <SortControls
            fields={SORT_FIELDS}
            sort={sort}
            order={order}
            onSort={toggleSort}
          />
        )}
      </div>
      {view.status === "loading" && (
        <output className="block">
          <span className="sr-only">Buscando en MAST…</span>
          <ul
            data-testid="candidate-results-skeleton"
            className="flex w-full flex-col gap-3"
            aria-hidden
          >
            {SKELETON_ROWS.map((row) => (
              <SummaryCardSkeleton key={row} />
            ))}
          </ul>
        </output>
      )}
      {view.status === "error" && (
        <p className="text-sm text-destructive">
          No se pudo buscar candidatos para{" "}
          <strong className="font-semibold">{query.trim()}</strong>.
        </p>
      )}
      {view.status === "empty" && (
        <p className="text-sm text-muted-foreground">
          MAST no devolvió archivos de ciencia para{" "}
          <strong className="font-semibold text-foreground">
            {query.trim()}
          </strong>
          {"."}
        </p>
      )}
      {view.status === "ready" && (
        <ul className="flex w-full flex-col gap-3">
          {view.page.items.map((item) => (
            <SummaryCard
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
                        onClick={() => setImporting(item)}
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
        </ul>
      )}
      {(view.status === "ready" || view.status === "empty") && (
        <FilePager
          page={page}
          hasMore={view.page.has_more === true}
          onPage={setPage}
        />
      )}
      <ImportNameDialog
        key={importing?.data_uri ?? "none"}
        filename={importing?.product_filename ?? null}
        submitting={select.isPending}
        onCancel={() => setImporting(null)}
        onConfirm={(displayName) => {
          if (importing === null) {
            return;
          }
          void select
            .mutateAsync({
              data: {
                candidate_token: importing.token,
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
              setImporting(null);
            });
        }}
      />
      {transferIds.map((transferId) => (
        <TransferFeedback key={transferId} transferId={transferId} />
      ))}
    </section>
  );
}
