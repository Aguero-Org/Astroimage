import { HardDriveDownload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
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
import { ApiError } from "@/lib/api-client";
import { useImportFitsUrl, useImportLocalFits } from "../api";
import { formatQueryError } from "../format-query-error";

type ImportSource = "files" | "url";

const FITS_EXTENSION = /\.(fits|fit|fts)$/i;

function isFitsFile(file: File): boolean {
  return FITS_EXTENSION.test(file.name);
}

function importErrorMessage(error: unknown, source: ImportSource): string {
  if (error instanceof ApiError && error.status === 409) {
    return source === "url"
      ? "Ese enlace ya está importado."
      : "Ese archivo ya está en el servidor.";
  }
  if (error instanceof ApiError && error.status === 400) {
    return "No se pudo importar el FITS. Revisá que sea una imagen 2D y que no supere el tamaño permitido.";
  }
  return formatQueryError(error);
}

function draggedFiles(event: DragEvent): boolean {
  return [...(event.dataTransfer?.types ?? [])].includes("Files");
}

function fileNames(files: readonly File[]) {
  return files.map((file, index) => {
    let separator = "";
    if (index > 0) {
      separator = index === files.length - 1 ? " y " : ", ";
    }
    return (
      <span key={`${file.name}-${file.size}-${file.lastModified}`}>
        {separator}
        <strong className="font-semibold text-foreground">{file.name}</strong>
      </span>
    );
  });
}

export function ImportFitsControl() {
  const [open, setOpen] = useState(false);
  const [source, setSource] = useState<ImportSource>("files");
  const [files, setFiles] = useState<File[]>([]);
  const [rejected, setRejected] = useState<string[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [urlError, setUrlError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const pendingRef = useRef(false);
  const importFiles = useImportLocalFits();
  const importUrl = useImportFitsUrl();
  const pending = importFiles.isPending || importUrl.isPending;
  pendingRef.current = pending;
  const trimmedUrl = url.trim();
  const canSubmit =
    !pending && (source === "files" ? files.length > 0 : trimmedUrl.length > 0);

  function takeFiles(selected: readonly File[]) {
    setSource("files");
    setFiles(selected.filter(isFitsFile));
    setRejected(
      selected.filter((file) => !isFitsFile(file)).map((file) => file.name),
    );
    setOpen(true);
  }

  const takeFilesRef = useRef(takeFiles);
  takeFilesRef.current = takeFiles;

  useEffect(() => {
    let depth = 0;

    function onEnter(event: DragEvent) {
      if (pendingRef.current || !draggedFiles(event)) {
        return;
      }
      event.preventDefault();
      depth += 1;
      setDragging(true);
      setSource("files");
      setOpen(true);
    }

    function onOver(event: DragEvent) {
      if (!draggedFiles(event)) {
        return;
      }
      event.preventDefault();
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = pendingRef.current ? "none" : "copy";
      }
    }

    function onLeave(event: DragEvent) {
      if (!draggedFiles(event)) {
        return;
      }
      depth -= 1;
      if (depth <= 0) {
        depth = 0;
        setDragging(false);
      }
    }

    function onDrop(event: DragEvent) {
      if (!draggedFiles(event)) {
        return;
      }
      event.preventDefault();
      depth = 0;
      setDragging(false);
      if (pendingRef.current) {
        return;
      }
      takeFilesRef.current([...(event.dataTransfer?.files ?? [])]);
    }

    window.addEventListener("dragenter", onEnter);
    window.addEventListener("dragover", onOver);
    window.addEventListener("dragleave", onLeave);
    window.addEventListener("drop", onDrop);
    return () => {
      window.removeEventListener("dragenter", onEnter);
      window.removeEventListener("dragover", onOver);
      window.removeEventListener("dragleave", onLeave);
      window.removeEventListener("drop", onDrop);
    };
  }, []);

  function resetForm() {
    setSource("files");
    setFiles([]);
    setRejected([]);
    setTitle("");
    setDescription("");
    setUrl("");
    setUrlError(null);
  }

  function close() {
    if (pending) {
      return;
    }
    setOpen(false);
    resetForm();
  }

  function submit() {
    if (source === "files") {
      importFiles.mutate(
        {
          data: {
            files,
            display_name: title.trim() || undefined,
            description: description.trim() || undefined,
          },
        },
        {
          onSuccess: (imported) => {
            toast.success(
              imported.length === 1
                ? `Importado ${imported[0]?.slug ?? "el archivo"}.`
                : `Importados ${imported.length} archivos.`,
            );
            setOpen(false);
            resetForm();
          },
          onError: (error) => toast.error(importErrorMessage(error, "files")),
        },
      );
      return;
    }
    if (!/^(https?:\/\/|mast:)/i.test(trimmedUrl)) {
      setUrlError(
        "El enlace tiene que ser http, https o un URI de MAST (mast:).",
      );
      return;
    }
    importUrl.mutate(
      {
        data: {
          url: trimmedUrl,
          display_name: title.trim() || undefined,
          description: description.trim() || undefined,
        },
      },
      {
        onSuccess: (imported) => {
          toast.success(`Importado ${imported.slug}.`);
          setOpen(false);
          resetForm();
        },
        onError: (error) => toast.error(importErrorMessage(error, "url")),
      },
    );
  }

  return (
    <>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="text-primary hover:bg-primary/10 hover:text-primary"
            data-testid="import-fits"
            aria-label="Importar FITS"
            onClick={() => setOpen(true)}
          >
            <HardDriveDownload className="size-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>Importar FITS</TooltipContent>
      </Tooltip>
      <Dialog
        open={open}
        onOpenChange={(next) => {
          if (!next) {
            close();
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-1">
              Importar FITS
              <HelpHint
                label="Importar FITS"
                testId="help-import-fits"
                glossaryId="importar-fits"
              >
                Sube uno o varios archivos, soltalos en el inicio, o indica un
                enlace http, https o mast:. El servidor guarda solo imágenes
                FITS de dos dimensiones.
              </HelpHint>
            </DialogTitle>
          </DialogHeader>
          <div
            role="radiogroup"
            aria-label="Origen del FITS"
            className="flex flex-col gap-2"
          >
            <Label className="cursor-pointer font-normal">
              <input
                type="radio"
                name="fits-import-source"
                value="files"
                checked={source === "files"}
                disabled={pending}
                data-testid="import-fits-source-files"
                onChange={() => setSource("files")}
              />
              <span>Archivos de la computadora</span>
            </Label>
            <Label className="cursor-pointer font-normal">
              <input
                type="radio"
                name="fits-import-source"
                value="url"
                checked={source === "url"}
                disabled={pending}
                data-testid="import-fits-source-url"
                onChange={() => setSource("url")}
              />
              <span>Enlace</span>
            </Label>
          </div>
          {source === "files" ? (
            <div key="files" className="flex flex-col gap-2">
              <Label htmlFor="import-fits-files">Archivos .fits</Label>
              <Input
                id="import-fits-files"
                data-testid="import-fits-files"
                type="file"
                accept=".fits,.fit,.fts"
                multiple
                disabled={pending}
                onChange={(event) => {
                  takeFiles([...(event.target.files ?? [])]);
                }}
              />
              {files.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  Se van a subir {fileNames(files)}.
                </p>
              )}
              {rejected.length > 0 && (
                <p className="text-sm text-destructive">
                  No es un FITS:{" "}
                  {rejected.map((name) => (
                    <strong
                      key={name}
                      className="font-semibold text-foreground"
                    >
                      {name}
                    </strong>
                  ))}
                  .
                </p>
              )}
            </div>
          ) : (
            <div key="url" className="flex flex-col gap-2">
              <Label htmlFor="import-fits-url">
                Enlace http, https o mast:
              </Label>
              <Input
                id="import-fits-url"
                data-testid="import-fits-url"
                type="url"
                value={url}
                disabled={pending}
                placeholder="https://"
                onChange={(event) => {
                  setUrl(event.target.value);
                  setUrlError(null);
                }}
              />
              {urlError !== null && (
                <p className="text-sm text-destructive">{urlError}</p>
              )}
            </div>
          )}
          <div className="flex flex-col gap-2">
            <Label htmlFor="import-fits-title">Título</Label>
            <Input
              id="import-fits-title"
              data-testid="import-fits-title"
              value={title}
              maxLength={200}
              disabled={pending}
              placeholder="Si lo dejás vacío, se usa el nombre del archivo"
              onChange={(event) => setTitle(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="import-fits-description">Descripción</Label>
            <Input
              id="import-fits-description"
              data-testid="import-fits-description"
              value={description}
              maxLength={500}
              disabled={pending}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={close}
              disabled={pending}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              data-testid="confirm-import-fits"
              disabled={!canSubmit}
              onClick={submit}
            >
              {pending ? "Importando…" : "Importar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {dragging ? (
        <div
          data-testid="import-fits-dropzone"
          className="pointer-events-none fixed inset-0 z-[60] flex items-center justify-center bg-background/80 p-6"
        >
          <p className="rounded-lg border border-primary bg-card px-6 py-4 text-sm font-medium text-foreground">
            Soltá el archivo para importarlo
          </p>
        </div>
      ) : null}
    </>
  );
}
