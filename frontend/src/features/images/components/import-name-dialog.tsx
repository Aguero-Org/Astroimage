import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
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
import { Label } from "@/components/ui/label";

const importNameSchema = z.object({
  displayName: z.string().trim().min(1),
});

type ImportNameValues = z.infer<typeof importNameSchema>;

type ImportNameDialogProps = {
  filename: string | null;
  submitting: boolean;
  onCancel: () => void;
  onConfirm: (displayName: string) => void;
};

export function ImportNameDialog({
  filename,
  submitting,
  onCancel,
  onConfirm,
}: Readonly<ImportNameDialogProps>) {
  const { register, handleSubmit, reset, formState } =
    useForm<ImportNameValues>({
      resolver: zodResolver(importNameSchema),
      defaultValues: { displayName: "" },
      mode: "onChange",
    });
  const open = filename !== null;

  const submitName = handleSubmit((values) => {
    onConfirm(values.displayName);
  });

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) {
          reset();
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
            {"."}
          </DialogDescription>
        </DialogHeader>
        <Label
          className="flex-col items-stretch gap-1 font-normal leading-normal"
          htmlFor="display-name"
        >
          Nombre descriptivo
          <Input
            id="display-name"
            autoFocus
            placeholder="Por ejemplo, núcleo de Andrómeda"
            {...register("displayName")}
          />
        </Label>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
          <Button
            type="button"
            data-testid="confirm-import-name"
            disabled={!formState.isValid || submitting}
            onClick={submitName}
          >
            Importar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
