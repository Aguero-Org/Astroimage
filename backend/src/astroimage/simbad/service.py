from __future__ import annotations

import asyncio
import re
import warnings
from collections import defaultdict
from collections.abc import Sequence
from typing import cast
from uuid import UUID

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning

from astroimage.fits.reader import FitsMetadata, FitsReader
from astroimage.fits.service import FitsService
from astroimage.shared.logging import simbad_service_log as _log
from astroimage.simbad.cache import SimbadReferenceCache, simbad_cache_key
from astroimage.simbad.model import (
    SimbadImageMatch,
    SimbadObject,
    SimbadReference,
    SkyDetection,
)
from astroimage.simbad.provider import SimbadCatalogProvider
from astroimage.simbad.schema import (
    SimbadImageMatchSchema,
    SimbadObjectSchema,
    SimbadReferenceSchema,
    SimbadReferencesConfigSchema,
    SimbadReferencesResponse,
    SimbadReferencesSummarySchema,
)
from astroimage.sources.service import SourceDetectionService

_DEFAULT_QUERY_TIMEOUT_S = 120.0
_MIN_RADIUS_ARCSEC = 60.0
_ALIASES_PER_OBJECT = 200
_REFERENCES_PER_OBJECT_FACTOR = 3
_MAX_AUXILIARY_RECORDS = 5000
_ADS_URL = "https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"
_DOI_URL = "https://doi.org/{doi}"
_GAIA_ID_PATTERN = re.compile(r"^Gaia\s+(?:DR\d+|EDR3)\s+(\d+)$", re.IGNORECASE)


def _world_coordinates(metadata: FitsMetadata) -> WCS | None:
    if not metadata.wcs.present:
        return None
    header = fits.Header()
    for key, value in metadata.header.items():
        header[key] = value
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FITSFixedWarning)
        return WCS(header, naxis=2, relax=True)


def _to_sky(wcs: WCS, x: float, y: float) -> SkyCoord:
    return cast(SkyCoord, wcs.pixel_to_world(x, y))


def _field_region(
    metadata: FitsMetadata,
    wcs: WCS,
    *,
    margin_arcsec: float,
) -> tuple[SkyCoord, float]:
    shape = metadata.image.shape
    height, width = (int(shape[0]), int(shape[1])) if shape and len(shape) >= 2 else (1, 1)
    height = max(height, 1)
    width = max(width, 1)
    center = _to_sky(wcs, (width - 1) / 2.0, (height - 1) / 2.0)
    corner_world = cast(
        SkyCoord,
        wcs.pixel_to_world(
            [0.0, width - 1.0, width - 1.0, 0.0],
            [0.0, 0.0, height - 1.0, height - 1.0],
        ),
    )
    corners = SkyCoord(
        ra=[float(value) * u.deg for value in corner_world.ra.deg],
        dec=[float(value) * u.deg for value in corner_world.dec.deg],
        frame="icrs",
    )
    footprint_radius = float(center.separation(corners).max().to_value(u.arcsec))
    return center, max(footprint_radius + margin_arcsec, _MIN_RADIUS_ARCSEC)


def _fallback_region(wcs: WCS) -> tuple[SkyCoord, float]:
    crval = wcs.wcs.crval
    center = SkyCoord(ra=float(crval[0]) * u.deg, dec=float(crval[1]) * u.deg, frame="icrs")
    return center, _MIN_RADIUS_ARCSEC


def _gaia_source_id(aliases: Sequence[str]) -> str | None:
    for alias in aliases:
        match = _GAIA_ID_PATTERN.fullmatch(alias)
        if match is not None:
            return match.group(1)
    return None


def _ads_url(bibcode: str) -> str:
    return _ADS_URL.format(bibcode=bibcode)


def _doi_url(doi: str | None) -> str | None:
    return _DOI_URL.format(doi=doi) if doi is not None else None


def _reference_schema(reference: SimbadReference) -> SimbadReferenceSchema:
    return SimbadReferenceSchema(
        bibcode=reference.bibcode,
        year=reference.year,
        title=reference.title,
        doi=reference.doi,
        journal=reference.journal,
        object_count=reference.object_count,
        ads_url=_ads_url(reference.bibcode),
        doi_url=_doi_url(reference.doi),
    )


class SimbadReferenceService:
    def __init__(
        self,
        *,
        fits: FitsService,
        detection: SourceDetectionService | None,
        provider: SimbadCatalogProvider,
        cache: SimbadReferenceCache,
        reader: FitsReader | None = None,
        query_timeout_s: float = _DEFAULT_QUERY_TIMEOUT_S,
    ) -> None:
        self._fits = fits
        self._detection = detection
        self._provider = provider
        self._cache = cache
        self._reader = reader or FitsReader()
        self._query_timeout_s = query_timeout_s

    async def ensure_record(self, record_id: UUID) -> None:
        await self._fits.get_record(record_id)

    async def references_from_record(
        self,
        record_id: UUID,
        *,
        client_id: str = "anonymous",
        hdu_index: int | None = None,
        config: SimbadReferencesConfigSchema | None = None,
        refresh: bool = False,
    ) -> SimbadReferencesResponse:
        resolved = config or SimbadReferencesConfigSchema()
        key = simbad_cache_key(
            record_id=record_id,
            client_id=client_id,
            hdu_index=hdu_index,
            config=resolved,
        )
        if not refresh:
            cached = self._cache.get(key)
            if cached is not None:
                _log.info("simbad_cache_hit", record_id=str(record_id), client_id=client_id)
                return cached
        record = await self._fits.get_record(record_id)
        payload = await self._fits.get_payload(record)
        result = await self.references(
            payload,
            source_name=record.original_filename,
            hdu_index=hdu_index,
            client_id=client_id,
            config=resolved,
            record_id=record_id,
        )
        self._cache.set(key, result)
        return result

    async def references(
        self,
        payload: bytes,
        *,
        source_name: str | None = None,
        hdu_index: int | None = None,
        client_id: str = "anonymous",
        config: SimbadReferencesConfigSchema | None = None,
        record_id: UUID | None = None,
    ) -> SimbadReferencesResponse:
        resolved = config or SimbadReferencesConfigSchema()
        metadata = self._reader.read_metadata_from_bytes(
            payload,
            source_name=source_name,
            hdu_index=hdu_index,
        )
        wcs = _world_coordinates(metadata)
        if wcs is None:
            _log.info("simbad_skipped", reason="no wcs", source_name=metadata.source_name)
            return SimbadReferencesResponse(
                source_name=metadata.source_name,
                limit=resolved.limit,
                include_aliases=resolved.include_aliases,
                include_bibliography=resolved.include_bibliography,
                wcs_present=False,
                queried=False,
            )
        center, radius = self._region(metadata, wcs, resolved)
        objects, error = await self._query_region(center, radius, resolved)
        if error is not None:
            return self._response(
                metadata.source_name,
                center,
                radius,
                resolved,
                [],
                queried=False,
                error=error,
                warnings=[],
                detections=[],
            )
        if not objects:
            return self._response(
                metadata.source_name,
                center,
                radius,
                resolved,
                [],
                queried=True,
                error=None,
                warnings=[],
                detections=[],
            )

        main_ids = [obj.main_id for obj in objects]
        alias_task = asyncio.create_task(
            self._safe_aliases(main_ids, enabled=resolved.include_aliases)
        )
        reference_task = asyncio.create_task(
            self._safe_references(
                main_ids,
                enabled=resolved.include_bibliography,
                max_references=resolved.max_references_per_object,
            )
        )
        aliases, alias_warning = await alias_task
        references, reference_warning = await reference_task
        detections, detection_warning = await self._detections(
            record_id,
            wcs,
            hdu_index,
            client_id=client_id,
        )
        warnings = [
            warning
            for warning in (alias_warning, reference_warning, detection_warning)
            if warning is not None
        ]
        object_schemas = [
            self._object_schema(obj, aliases, references, detections, resolved) for obj in objects
        ]
        return self._response(
            metadata.source_name,
            center,
            radius,
            resolved,
            object_schemas,
            queried=True,
            error=None,
            warnings=warnings,
            detections=detections,
        )

    def _region(
        self,
        metadata: FitsMetadata,
        wcs: WCS,
        config: SimbadReferencesConfigSchema,
    ) -> tuple[SkyCoord, float]:
        try:
            return _field_region(
                metadata,
                wcs,
                margin_arcsec=config.crossmatch_radius_arcsec,
            )
        except (AttributeError, TypeError, ValueError):
            return _fallback_region(wcs)

    async def _query_region(
        self,
        center: SkyCoord,
        radius: float,
        config: SimbadReferencesConfigSchema,
    ) -> tuple[list[SimbadObject], str | None]:
        try:
            objects = await asyncio.wait_for(
                asyncio.to_thread(
                    self._provider.query_region,
                    center,
                    radius,
                    row_limit=config.limit,
                    object_type=config.object_type,
                ),
                timeout=self._query_timeout_s,
            )
        except TimeoutError:
            _log.warning("simbad_query_timed_out", timeout_s=self._query_timeout_s)
            return [], f"SIMBAD query timed out after {self._query_timeout_s} seconds"
        except Exception as exc:
            _log.warning("simbad_query_failed", detail=str(exc), exc_info=exc)
            return [], f"SIMBAD query failed: {exc}"
        return list(objects), None

    async def _safe_aliases(
        self,
        main_ids: list[str],
        *,
        enabled: bool,
    ) -> tuple[dict[str, tuple[str, ...]], str | None]:
        if not enabled:
            return {}, None
        max_records = min(max(len(main_ids) * _ALIASES_PER_OBJECT, 100), _MAX_AUXILIARY_RECORDS)
        try:
            aliases = await asyncio.wait_for(
                asyncio.to_thread(
                    self._provider.query_aliases,
                    main_ids,
                    max_records=max_records,
                ),
                timeout=self._query_timeout_s,
            )
        except TimeoutError:
            _log.warning("simbad_aliases_timed_out", timeout_s=self._query_timeout_s)
            return {}, "SIMBAD identifier query timed out"
        except Exception as exc:
            _log.warning("simbad_aliases_failed", detail=str(exc), exc_info=exc)
            return {}, f"SIMBAD identifier query failed: {exc}"
        grouped: dict[str, list[str]] = defaultdict(list)
        for alias in aliases:
            grouped[alias.object_id].append(alias.name)
        return {key: tuple(values) for key, values in grouped.items()}, None

    async def _safe_references(
        self,
        main_ids: list[str],
        *,
        enabled: bool,
        max_references: int,
    ) -> tuple[dict[str, tuple[SimbadReference, ...]], str | None]:
        if not enabled or max_references <= 0:
            return {}, None
        max_records = min(
            max(len(main_ids) * max_references * _REFERENCES_PER_OBJECT_FACTOR, 100),
            _MAX_AUXILIARY_RECORDS,
        )
        try:
            references = await asyncio.wait_for(
                asyncio.to_thread(
                    self._provider.query_references,
                    main_ids,
                    max_records=max_records,
                ),
                timeout=self._query_timeout_s,
            )
        except TimeoutError:
            _log.warning("simbad_references_timed_out", timeout_s=self._query_timeout_s)
            return {}, "SIMBAD bibliography query timed out"
        except Exception as exc:
            _log.warning("simbad_references_failed", detail=str(exc), exc_info=exc)
            return {}, f"SIMBAD bibliography query failed: {exc}"
        grouped: dict[str, list[SimbadReference]] = defaultdict(list)
        for reference in references:
            grouped[reference.object_id].append(reference)
        ordered: dict[str, tuple[SimbadReference, ...]] = {}
        for object_id, values in grouped.items():
            values.sort(key=lambda item: (item.year or 0, item.bibcode), reverse=True)
            ordered[object_id] = tuple(values[:max_references])
        return ordered, None

    async def _detections(
        self,
        record_id: UUID | None,
        wcs: WCS,
        hdu_index: int | None,
        *,
        client_id: str,
    ) -> tuple[list[SkyDetection], str | None]:
        if self._detection is None or record_id is None:
            return [], None
        try:
            result = await self._detection.detect_from_record(
                record_id,
                client_id=client_id,
                hdu_index=hdu_index,
            )
        except Exception as exc:
            _log.warning("simbad_detection_failed", detail=str(exc), exc_info=exc)
            return [], f"Image source crossmatch failed: {exc}"
        detections: list[SkyDetection] = []
        for point in result.point_sources:
            coordinate = _to_sky(wcs, point.xcentroid, point.ycentroid)
            detections.append(
                SkyDetection(
                    source_id=point.source_id,
                    object_type="point",
                    ra_deg=float(coordinate.ra.deg),
                    dec_deg=float(coordinate.dec.deg),
                )
            )
        for extended in result.extended_sources:
            coordinate = _to_sky(wcs, extended.xcentroid, extended.ycentroid)
            detections.append(
                SkyDetection(
                    source_id=extended.source_id,
                    object_type="extended",
                    ra_deg=float(coordinate.ra.deg),
                    dec_deg=float(coordinate.dec.deg),
                )
            )
        return detections, None

    def _object_schema(
        self,
        obj: SimbadObject,
        aliases: dict[str, tuple[str, ...]],
        references: dict[str, tuple[SimbadReference, ...]],
        detections: list[SkyDetection],
        config: SimbadReferencesConfigSchema,
    ) -> SimbadObjectSchema:
        object_aliases = aliases.get(obj.main_id, ())
        return SimbadObjectSchema(
            main_id=obj.main_id,
            otype=obj.otype,
            otype_text=obj.otype_text,
            ra_deg=obj.ra_deg,
            dec_deg=obj.dec_deg,
            separation_arcsec=obj.separation_arcsec,
            spectral_type=obj.spectral_type,
            parallax_mas=obj.parallax_mas,
            parallax_error_mas=obj.parallax_error_mas,
            major_axis_arcmin=obj.major_axis_arcmin,
            minor_axis_arcmin=obj.minor_axis_arcmin,
            position_angle_deg=obj.position_angle_deg,
            radial_velocity_km_s=obj.radial_velocity_km_s,
            redshift=obj.redshift,
            total_reference_count=obj.reference_count,
            gaia_source_id=_gaia_source_id(object_aliases),
            aliases=list(object_aliases),
            references=[
                _reference_schema(reference) for reference in references.get(obj.main_id, ())
            ],
            image_match=self._image_match(obj, detections, config),
        )

    @staticmethod
    def _image_match(
        obj: SimbadObject,
        detections: list[SkyDetection],
        config: SimbadReferencesConfigSchema,
    ) -> SimbadImageMatchSchema | None:
        if not detections:
            return None
        radius = max(float(config.crossmatch_radius_arcsec), 1e-9)
        power = max(float(config.probability_power), 0.1)
        object_coord = SkyCoord(
            ra=[obj.ra_deg] * u.deg,
            dec=[obj.dec_deg] * u.deg,
            frame="icrs",
        )
        detection_coords = SkyCoord(
            ra=[detection.ra_deg for detection in detections] * u.deg,
            dec=[detection.dec_deg for detection in detections] * u.deg,
            frame="icrs",
        )
        indexes, separations, _ = object_coord.match_to_catalog_sky(detection_coords)
        separation_arcsec = float(separations[0].to_value(u.arcsec))
        matched = separation_arcsec <= radius
        probability = (1.0 - min(separation_arcsec / radius, 1.0)) ** power if matched else 0.0
        detection = detections[int(indexes[0])]
        match = SimbadImageMatch(
            source_id=detection.source_id,
            object_type=detection.object_type,
            separation_arcsec=separation_arcsec,
            probability=probability,
            matched=matched,
        )
        return SimbadImageMatchSchema(
            source_id=match.source_id,
            object_type=match.object_type,
            separation_arcsec=match.separation_arcsec,
            probability=match.probability,
            matched=match.matched,
        )

    @staticmethod
    def _response(
        source_name: str | None,
        center: SkyCoord,
        radius: float,
        config: SimbadReferencesConfigSchema,
        objects: list[SimbadObjectSchema],
        *,
        queried: bool,
        error: str | None,
        warnings: list[str],
        detections: list[SkyDetection],
    ) -> SimbadReferencesResponse:
        return SimbadReferencesResponse(
            source_name=source_name,
            ra_deg=float(center.ra.deg),
            dec_deg=float(center.dec.deg),
            radius_arcsec=radius,
            limit=config.limit,
            include_aliases=config.include_aliases,
            include_bibliography=config.include_bibliography,
            wcs_present=True,
            queried=queried,
            error=error,
            warnings=warnings,
            summary=SimbadReferencesSummarySchema(
                object_count=len(objects),
                matched_source_count=sum(
                    1 for item in objects if item.image_match and item.image_match.matched
                ),
                detection_count=len(detections),
                reference_count=sum(len(item.references) for item in objects),
            ),
            objects=objects,
        )
