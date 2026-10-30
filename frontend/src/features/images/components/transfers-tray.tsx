import { useTransfersStore } from "../transfers-store";
import { TransferFeedback } from "./transfer-feedback";

export function TransfersTray() {
  const transferIds = useTransfersStore((state) => state.transferIds);

  if (transferIds.length === 0) {
    return null;
  }

  return (
    <div
      data-testid="transfers-tray"
      className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-2 p-4"
    >
      {transferIds.map((transferId) => (
        <div key={transferId} className="pointer-events-auto w-full max-w-md">
          <TransferFeedback transferId={transferId} />
        </div>
      ))}
    </div>
  );
}
