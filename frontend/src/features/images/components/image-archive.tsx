import { Fragment } from "react";
import type { FitsMetadataSchema } from "@/api/generated/model";
import { HelpHint } from "@/components/ui/help-hint";
import { Skeleton } from "@/components/ui/skeleton";
import {
  archiveGroupRows,
  IMAGE_ARCHIVE_GROUPS,
} from "../image-archive-groups";
import { CollapsibleSection } from "./collapsible-section";
import { CopyableValue, MetadataGroup } from "./metadata-group";

type ImageArchiveProps = {
  info: FitsMetadataSchema | undefined;
  isPending: boolean;
};

const SKELETON_GROUPS = [0, 1, 2];
const SKELETON_ROWS = [0, 1, 2, 3];

function ImageArchiveSkeleton() {
  return (
    <output className="block" data-testid="image-archive-skeleton">
      <span className="sr-only">Cargando metadatos…</span>
      <div aria-hidden>
        {SKELETON_GROUPS.map((group) => (
          <div key={group} className="mb-3">
            <Skeleton className="mb-2 h-4 w-24" />
            <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
              {SKELETON_ROWS.map((row) => (
                <Fragment key={row}>
                  <Skeleton className="h-3.5 w-16" />
                  <Skeleton className="h-3.5 w-28" />
                </Fragment>
              ))}
            </div>
          </div>
        ))}
      </div>
    </output>
  );
}

export function ImageArchive({ info, isPending }: Readonly<ImageArchiveProps>) {
  if (isPending) {
    return <ImageArchiveSkeleton />;
  }
  if (!info) {
    return (
      <p className="text-xs text-muted-foreground">
        No hay metadatos disponibles.
      </p>
    );
  }

  const headerEntries = Object.entries(info.header ?? {});

  return (
    <div data-testid="image-archive">
      {IMAGE_ARCHIVE_GROUPS.map((group) => (
        <MetadataGroup
          key={group.testId}
          title={group.title}
          testId={group.testId}
          rows={archiveGroupRows(group, info)}
        />
      ))}
      {headerEntries.length > 0 && (
        <CollapsibleSection
          id="archive-header"
          title="Header FITS"
          nested
          hint={
            <HelpHint
              label="Header FITS"
              testId="help-encabezado"
              glossaryId="encabezado"
            >
              Palabras clave crudas del archivo. Los grupos de arriba ya resumen
              lo útil.
            </HelpHint>
          }
        >
          <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
            {headerEntries.map(([key, headerValue]) => (
              <div key={key} className="contents">
                <dt className="text-muted-foreground">{key}</dt>
                <CopyableValue
                  label={key}
                  value={String(headerValue)}
                  testId={`meta-header-${key}`}
                />
              </div>
            ))}
          </dl>
        </CollapsibleSection>
      )}
    </div>
  );
}
