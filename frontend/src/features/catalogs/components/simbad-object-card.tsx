import { ChevronDown, ExternalLink, LocateFixed } from "lucide-react";
import type { SimbadObjectSchema } from "@/api/generated/model";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { simbadObjectTypeName } from "../simbad-object-types";

type SimbadObjectCardProps = {
  object: SimbadObjectSchema;
  onFocusSource?: (sourceId: number, objectType: "point" | "extended") => void;
};

function formatCoord(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${value.toFixed(4)}°`;
}

function formatNumber(value: number | null | undefined, suffix = ""): string {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${value}${suffix}`;
}

function radialVelocity(object: SimbadObjectSchema): string {
  if (
    object.radial_velocity_km_s !== null &&
    object.radial_velocity_km_s !== undefined
  ) {
    return `${object.radial_velocity_km_s} km/s`;
  }
  if (object.redshift !== null && object.redshift !== undefined) {
    return `z ${object.redshift}`;
  }
  return "-";
}

function dimensions(object: SimbadObjectSchema): string | null {
  const major = object.major_axis_arcmin;
  const minor = object.minor_axis_arcmin;
  if (major === null || major === undefined) {
    return null;
  }
  if (minor === null || minor === undefined) {
    return `${major}′`;
  }
  return `${major}′ × ${minor}′`;
}

function objectTypeLabel(object: SimbadObjectSchema): string | null {
  return simbadObjectTypeName(object.otype, object.otype_text);
}

function matchedSourceLabel(
  match: SimbadObjectSchema["image_match"],
): string | null {
  if (!match?.matched) {
    return null;
  }
  if (match.object_type === "point") {
    return `Fuente puntual #${match.source_id}`;
  }
  return `Fuente extendida #${match.source_id}`;
}

function SimbadFocusRow({
  object,
  onFocusSource,
}: Readonly<SimbadObjectCardProps>) {
  const match = object.image_match;
  const sourceLabel = matchedSourceLabel(match);
  if (!match?.matched || sourceLabel === null) {
    return null;
  }
  const objectType =
    match.object_type === "point" || match.object_type === "extended"
      ? match.object_type
      : null;
  const canFocus = onFocusSource !== undefined && objectType !== null;
  const separation = match.separation_arcsec;
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
      <span>{sourceLabel}</span>
      {separation !== null && separation !== undefined ? (
        <span>Δ {separation.toFixed(2)}″</span>
      ) : null}
      {canFocus ? (
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="h-7 px-2 text-xs"
          data-testid="simbad-object-focus"
          onClick={() => onFocusSource(match.source_id, objectType)}
        >
          <LocateFixed aria-hidden className="size-3.5" />
          Ir a la fuente
        </Button>
      ) : null}
    </div>
  );
}

export function SimbadObjectCard({
  object,
  onFocusSource,
}: Readonly<SimbadObjectCardProps>) {
  const sourceLabel = matchedSourceLabel(object.image_match);
  const size = dimensions(object);
  const typeLabel = objectTypeLabel(object);

  return (
    <Collapsible asChild>
      <article
        data-testid="simbad-object-card"
        className="rounded-lg border border-sidebar-border bg-sidebar transition-colors data-[state=open]:bg-sidebar-accent/40"
      >
        <div className="flex items-center gap-1 p-2.5">
          <CollapsibleTrigger asChild>
            <button
              type="button"
              aria-label={`Ver detalles de ${object.main_id}`}
              data-testid="simbad-object-toggle"
              className="group flex min-w-0 flex-1 items-center gap-2 rounded-md px-1 py-0.5 text-left hover:bg-sidebar-accent/60 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            >
              <ChevronDown
                aria-hidden
                className="size-4 shrink-0 text-muted-foreground transition-transform group-data-[state=open]:rotate-180"
              />
              <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="flex min-w-0 items-center gap-2">
                  <span
                    data-testid="simbad-object-name"
                    className="truncate text-sm font-semibold"
                  >
                    {object.main_id}
                  </span>
                  {typeLabel ? (
                    <Badge
                      data-testid="simbad-object-otype"
                      variant="secondary"
                      className="shrink-0"
                    >
                      {typeLabel}
                    </Badge>
                  ) : null}
                </span>
                {sourceLabel ? (
                  <span
                    data-testid="simbad-object-source"
                    className="truncate text-xs text-muted-foreground"
                  >
                    {sourceLabel}
                  </span>
                ) : null}
              </span>
            </button>
          </CollapsibleTrigger>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            data-testid="simbad-object-simbad-link"
            asChild
            className="shrink-0"
          >
            <a
              href={`https://simbad.cds.unistra.fr/simbad/sim-id?Ident=${encodeURIComponent(object.main_id)}`}
              target="_blank"
              rel="noreferrer"
              aria-label={`Abrir ${object.main_id} en SIMBAD`}
              title="Abrir en SIMBAD"
            >
              <ExternalLink aria-hidden className="size-4" />
            </a>
          </Button>
        </div>

        <CollapsibleContent>
          <div className="flex flex-col gap-3 border-t border-sidebar-border px-2.5 py-2">
            <SimbadFocusRow object={object} onFocusSource={onFocusSource} />

            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
              <dt className="text-muted-foreground">RA</dt>
              <dd>{formatCoord(object.ra_deg)}</dd>
              <dt className="text-muted-foreground">Dec</dt>
              <dd>{formatCoord(object.dec_deg)}</dd>
              <dt className="text-muted-foreground">Tipo espectral</dt>
              <dd>{object.spectral_type ?? "-"}</dd>
              <dt className="text-muted-foreground">Paralaje</dt>
              <dd>{formatNumber(object.parallax_mas, " mas")}</dd>
              <dt className="text-muted-foreground">RV/Redshift</dt>
              <dd>{radialVelocity(object)}</dd>
              {size ? (
                <>
                  <dt className="text-muted-foreground">Tamaño</dt>
                  <dd>{size}</dd>
                </>
              ) : null}
              {object.position_angle_deg !== null &&
              object.position_angle_deg !== undefined ? (
                <>
                  <dt className="text-muted-foreground">Ángulo de posición</dt>
                  <dd>{object.position_angle_deg}°</dd>
                </>
              ) : null}
              {object.total_reference_count !== null &&
              object.total_reference_count !== undefined ? (
                <>
                  <dt className="text-muted-foreground">Referencias</dt>
                  <dd>{object.total_reference_count}</dd>
                </>
              ) : null}
              {object.gaia_source_id ? (
                <>
                  <dt className="text-muted-foreground">Gaia</dt>
                  <dd className="truncate">{object.gaia_source_id}</dd>
                </>
              ) : null}
            </dl>

            {object.aliases && object.aliases.length > 0 ? (
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-xs text-muted-foreground">Alias:</span>
                {object.aliases.slice(0, 6).map((alias) => (
                  <Badge key={alias} variant="outline" className="text-xs">
                    {alias}
                  </Badge>
                ))}
                {object.aliases.length > 6 ? (
                  <span className="text-xs text-muted-foreground">
                    +{object.aliases.length - 6}
                  </span>
                ) : null}
              </div>
            ) : null}
          </div>
        </CollapsibleContent>
      </article>
    </Collapsible>
  );
}
