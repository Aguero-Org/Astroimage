import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { HelpHint } from "@/components/ui/help-hint";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePatchImageRecord } from "../api";
import { formatQueryError } from "../format-query-error";

const editSchema = z
  .object({
    displayName: z
      .string()
      .trim()
      .min(1, "El título no puede estar vacío")
      .max(200, "El título es demasiado largo"),
    description: z
      .string()
      .trim()
      .max(500, "La descripción es demasiado larga"),
    tags: z.string(),
  })
  .superRefine((value, context) => {
    const labels = value.tags
      .split(",")
      .map((label) => label.trim())
      .filter((label) => label.length > 0);
    const folded = labels.map((label) => label.toLocaleLowerCase());
    if (new Set(folded).size !== folded.length) {
      context.addIssue({
        code: "custom",
        path: ["tags"],
        message: "Hay etiquetas repetidas",
      });
    }
  });

type EditValues = z.infer<typeof editSchema>;

export type EditableImage = {
  record_id: string;
  display_name: string;
  description?: string | null;
  tags?: string[];
};

function splitTags(value: string): string[] {
  return value
    .split(",")
    .map((label) => label.trim())
    .filter((label) => label.length > 0);
}

export function EditImageButton({
  record,
}: Readonly<{ record: EditableImage }>) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button
        type="button"
        size="icon"
        variant="ghost"
        aria-label={`Editar ${record.display_name}`}
        data-testid="edit-image"
        onClick={() => setOpen(true)}
      >
        <Pencil className="size-4" />
      </Button>
      {open ? (
        <EditImageDialog record={record} onClose={() => setOpen(false)} />
      ) : null}
    </>
  );
}

function EditImageDialog({
  record,
  onClose,
}: Readonly<{ record: EditableImage; onClose: () => void }>) {
  const patch = usePatchImageRecord();
  const form = useForm<EditValues>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      displayName: record.display_name,
      description: record.description ?? "",
      tags: (record.tags ?? []).join(", "),
    },
  });

  async function onSubmit(values: EditValues) {
    try {
      await patch.mutateAsync({
        recordId: record.record_id,
        data: {
          display_name: values.displayName,
          description: values.description,
          tags: splitTags(values.tags),
        },
      });
      toast.success("Datos de la imagen actualizados");
      onClose();
    } catch (error) {
      toast.error(formatQueryError(error));
    }
  }

  return (
    <Dialog
      open
      onOpenChange={(next) => {
        if (!next) onClose();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Editar imagen</DialogTitle>
        </DialogHeader>
        <form className="grid gap-3" onSubmit={form.handleSubmit(onSubmit)}>
          <div className="grid gap-1.5">
            <Label htmlFor="edit-display-name">Título</Label>
            <Input id="edit-display-name" {...form.register("displayName")} />
            {form.formState.errors.displayName ? (
              <p className="text-sm text-destructive">
                {form.formState.errors.displayName.message}
              </p>
            ) : null}
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="edit-description">Descripción</Label>
            <Input id="edit-description" {...form.register("description")} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="edit-tags" className="flex items-center gap-1">
              Etiquetas
              <HelpHint label="Etiquetas" glossaryId="etiquetas-imagen">
                Palabras separadas por coma. No cambian el archivo FITS.
              </HelpHint>
            </Label>
            <Input id="edit-tags" {...form.register("tags")} />
            {form.formState.errors.tags ? (
              <p className="text-sm text-destructive">
                {form.formState.errors.tags.message}
              </p>
            ) : null}
          </div>
          <DialogFooter>
            <Button
              type="submit"
              disabled={patch.isPending}
              data-testid="edit-image-save"
            >
              Guardar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
