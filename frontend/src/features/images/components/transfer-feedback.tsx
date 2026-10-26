import { Link } from "@tanstack/react-router";
import { X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  formatBytes,
  type ImageTransfer,
  isActiveTransfer,
  useCancelTransfer,
  useImageTransfer,
  useResumeTransfer,
} from "../candidate-api";
import { formatQueryError } from "../format-query-error";
import { useTransfersStore } from "../transfers-store";

const STATUS_LABEL: Record<string, string> = {
  queued: "En cola",
  transferring: "Transfiriendo",
  annotating: "Anotando cabecera",
  storing: "Guardando",
  completed: "Lista",
  failed: "Falló",
  cancelled: "Cancelada",
  interrupted: "Interrumpida",
};

function remainingLabel(
  transferred: number,
  total: number | null,
  speed: number | null,
): string | null {
  if (total === null || speed === null || speed <= 0 || transferred >= total) {
    return null;
  }
  const seconds = Math.ceil((total - transferred) / speed);
  if (seconds < 60) {
    return `queda ~${seconds} s`;
  }
  return `queda ~${Math.ceil(seconds / 60)} min`;
}

export function TransferFeedback({
  transferId,
}: Readonly<{ transferId: string }>) {
  const transferQuery = useImageTransfer(transferId);
  const transfer = transferQuery.data ?? null;
  const cancel = useCancelTransfer();
  const resume = useResumeTransfer();
  if (transfer === null) {
    return null;
  }
  const percent =
    transfer.progress === null ? null : Math.round(transfer.progress * 100);
  const speed =
    transfer.speed_bytes_per_second === null
      ? null
      : `${formatBytes(transfer.speed_bytes_per_second)}/s`;
  const remaining = remainingLabel(
    transfer.bytes_transferred,
    transfer.total_bytes,
    transfer.speed_bytes_per_second,
  );

  return (
    <div
      data-testid="transfer-feedback"
      className="pointer-events-auto flex flex-col gap-2 rounded-md border border-border bg-background p-3 shadow-sm"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm">
          <strong className="font-semibold">{transfer.display_name}</strong>
          <span className="text-muted-foreground">
            {" "}
            · {transfer.product_filename}
          </span>
        </p>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-7 shrink-0"
          aria-label="Cerrar seguimiento"
          onClick={() => {
            useTransfersStore.getState().remove(transfer.transfer_id);
          }}
        >
          <X className="size-4" />
        </Button>
      </div>
      <p className="text-sm">
        {STATUS_LABEL[transfer.status] ?? transfer.status}
        {percent !== null ? ` · ${percent}%` : ""}
        {remaining ? ` · ${remaining}` : ""}
      </p>
      <progress
        className="h-2 w-full appearance-none overflow-hidden rounded-full bg-muted [&::-moz-progress-bar]:bg-primary [&::-webkit-progress-bar]:bg-muted [&::-webkit-progress-value]:bg-primary"
        max={100}
        value={percent ?? undefined}
        aria-label="Progreso de la importación"
      />
      <p className="text-xs text-muted-foreground">
        {formatBytes(transfer.bytes_transferred)}
        {transfer.total_bytes !== null
          ? ` de ${formatBytes(transfer.total_bytes)}`
          : ""}
        {speed ? ` · ${speed}` : ""}
      </p>
      {transfer.error !== null && transfer.error !== "" && (
        <p className="text-xs text-destructive">{transfer.error}</p>
      )}
      <div className="flex gap-2">
        {isActiveTransfer(transfer.status) && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              cancel.mutate(
                { transferId: transfer.transfer_id },
                { onError: (error) => toast.error(formatQueryError(error)) },
              );
            }}
          >
            Cancelar
          </Button>
        )}
        {!!transfer.resumable && (
          <Button
            type="button"
            size="sm"
            onClick={() => {
              resume.mutate(
                { transferId: transfer.transfer_id },
                { onError: (error) => toast.error(formatQueryError(error)) },
              );
            }}
          >
            Reanudar
          </Button>
        )}
        {transfer.status === "completed" && transfer.record_id && (
          <Button type="button" size="sm" asChild>
            <Link
              to="/image/$recordId/{-$slug}"
              params={{
                recordId: transfer.record_id,
                slug: transfer.slug ?? undefined,
              }}
            >
              Abrir imagen
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}

export type { ImageTransfer };
