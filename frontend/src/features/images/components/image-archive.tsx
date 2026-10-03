import type { FitsMetadataSchema } from "@/api/generated/model";
import { BrandLoader } from "@/components/brand-loader";
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

export function ImageArchive({ info, isPending }: Readonly<ImageArchiveProps>) {
  if (isPending) {
    return <BrandLoader label="Cargando metadatos…" />;
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
        <CollapsibleSection id="archive-header" title="Header FITS" nested>
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
