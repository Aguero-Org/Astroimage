import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, X } from "lucide-react";
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
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { usePatchImageRecord } from "../api";
import { formatQueryError } from "../format-query-error";
import { TagChip } from "./image-tags";

const editSchema = z.object({
  displayName: z
    .string()
    .trim()
    .min(1, "El título no puede estar vacío")
    .max(200, "El título es demasiado largo"),
  description: z.string().trim().max(500, "La descripción es demasiado larga"),
  tags: z.array(z.string().trim().min(1).max(40)).max(20),
});

type EditValues = z.infer<typeof editSchema>;

export type EditableImage = {
  record_id: string;
  display_name: string;
  description?: string | null;
  tags?: string[];
};

export function EditImageButton({
  record,
}: Readonly<{ record: EditableImage }>) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="size-8 text-primary hover:bg-accent dark:text-ring"
            aria-label={`Editar ${record.display_name}`}
            data-testid="edit-image"
            onClick={() => setOpen(true)}
          >
            <Pencil className="size-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>Editar</TooltipContent>
      </Tooltip>
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
      tags: record.tags ?? [],
    },
  });
  const tags = form.watch("tags");
  const [draft, setDraft] = useState("");

  function addTags(rawParts: string[]) {
    const next = [...tags];
    for (const raw of rawParts) {
      const text = raw.trim();
      if (text.length === 0) {
        continue;
      }
      if (text.length > 40) {
        form.setError("tags", { message: "La etiqueta es demasiado larga" });
        return;
      }
      if (
        next.some(
          (label) => label.toLocaleLowerCase() === text.toLocaleLowerCase(),
        )
      ) {
        form.setError("tags", { message: "Esa etiqueta ya está" });
        return;
      }
      if (next.length >= 20) {
        form.setError("tags", { message: "Hay demasiadas etiquetas" });
        return;
      }
      next.push(text);
    }
    form.clearErrors("tags");
    form.setValue("tags", next, { shouldDirty: true });
    setDraft("");
  }

  function removeTag(label: string) {
    form.setValue(
      "tags",
      tags.filter((current) => current !== label),
      { shouldDirty: true },
    );
  }

  async function onSubmit(values: EditValues) {
    const pending = draft.trim();
    const nextTags = [...values.tags];
    if (pending.length > 0) {
      if (
        nextTags.some(
          (label) => label.toLocaleLowerCase() === pending.toLocaleLowerCase(),
        )
      ) {
        form.setError("tags", { message: "Esa etiqueta ya está" });
        return;
      }
      nextTags.push(pending);
    }
    try {
      await patch.mutateAsync({
        recordId: record.record_id,
        data: {
          display_name: values.displayName,
          description: values.description,
          tags: nextTags,
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
                Enter o una coma agrega la etiqueta. La cruz la quita. No
                cambian el archivo FITS.
              </HelpHint>
            </Label>
            {tags.length > 0 ? (
              <ul className="flex flex-wrap gap-1.5">
                {tags.map((label) => (
                  <li key={label}>
                    <TagChip label={label}>
                      <button
                        type="button"
                        className="inline-flex size-4 items-center justify-center rounded-full hover:opacity-70"
                        aria-label={`Quitar ${label}`}
                        onClick={() => removeTag(label)}
                      >
                        <X className="size-3" />
                      </button>
                    </TagChip>
                  </li>
                ))}
              </ul>
            ) : null}
            <Input
              id="edit-tags"
              value={draft}
              placeholder="Escribí y presioná Enter"
              onChange={(event) => {
                const value = event.target.value;
                if (value.includes(",")) {
                  addTags(value.split(","));
                  return;
                }
                setDraft(value);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  addTags([draft]);
                }
              }}
            />
            {form.formState.errors.tags?.message ? (
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
