import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function DeleteImageDialog({
  target,
  isPending,
  onCancel,
  onConfirm,
}: Readonly<{
  target: { id: string; name: string } | null;
  isPending: boolean;
  onCancel: () => void;
  onConfirm: (id: string) => void;
}>) {
  return (
    <Dialog
      open={target !== null}
      onOpenChange={(open) => {
        if (!open) {
          onCancel();
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Eliminar imagen</DialogTitle>
          <DialogDescription>
            Se borra{" "}
            <strong className="font-semibold text-foreground">
              {target?.name}
            </strong>{" "}
            del servidor. El original en MAST no se toca.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="destructive"
            data-testid="confirm-delete-image"
            disabled={isPending}
            onClick={() => {
              if (target === null) {
                return;
              }
              onConfirm(target.id);
            }}
          >
            Eliminar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
