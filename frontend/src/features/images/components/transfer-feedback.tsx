import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import {
  formatBytes,
  type ImageTransfer,
  useCancelTransfer,
  useImageTransfer,
  useResumeTransfer,
} from "../candidate-api";

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
  const transfer =
    transferQuery.data?.status === 200 ? transferQuery.data.data : null;
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
      className="flex flex-col gap-2 rounded-md border border-border p-3"
    >
      <p className="text-sm">
        <strong className="font-semibold">{transfer.display_name}</strong>
        <span className="text-muted-foreground">
          {" "}
          · {transfer.product_filename}
        </span>
      </p>
      <p className="text-sm">
        {STATUS_LABEL[transfer.status] ?? transfer.status}
        {percent !== null ? ` · ${percent}%` : ""}
        {remaining ? ` · ${remaining}` : ""}
      </p>
      <div
        className="h-2 overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent ?? undefined}
      >
        <div
          className={
            percent === null
              ? "h-full w-1/3 animate-pulse bg-primary"
              : "h-full bg-primary"
          }
          style={percent === null ? undefined : { width: `${percent}%` }}
        />
      </div>
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
        {(transfer.status === "queued" ||
          transfer.status === "transferring" ||
          transfer.status === "annotating" ||
          transfer.status === "storing") && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              void cancel.mutateAsync({ transferId: transfer.transfer_id });
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
              void resume.mutateAsync({ transferId: transfer.transfer_id });
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
