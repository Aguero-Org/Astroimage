import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

type ImportNameDialogProps = {
  filename: string | null;
  pending: boolean;
  onCancel: () => void;
  onConfirm: (displayName: string) => void;
};

export function ImportNameDialog({
  filename,
  pending,
  onCancel,
  onConfirm,
}: Readonly<ImportNameDialogProps>) {
  const [displayName, setDisplayName] = useState("");
  const open = filename !== null;
  const trimmed = displayName.trim();

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) {
          setDisplayName("");
          onCancel();
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nombre de la imagen</DialogTitle>
          <DialogDescription>
            Es el nombre que verás en el catálogo. El archivo FITS sigue siendo{" "}
            <strong className="font-semibold text-foreground">
              {filename}
            </strong>
            .
          </DialogDescription>
        </DialogHeader>
        <label className="flex flex-col gap-1 text-sm" htmlFor="display-name">
          Nombre descriptivo
          <Input
            id="display-name"
            value={displayName}
            autoFocus
            placeholder="Por ejemplo, núcleo de Andrómeda"
            onChange={(event) => setDisplayName(event.target.value)}
          />
        </label>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
          <Button
            type="button"
            data-testid="confirm-import-name"
            disabled={trimmed.length === 0 || pending}
            onClick={() => onConfirm(trimmed)}
          >
            Importar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
