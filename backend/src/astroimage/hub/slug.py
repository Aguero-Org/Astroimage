from __future__ import annotations

import hashlib
import re


def product_slug(
    *,
    target_name: str,
    instrument: str | None,
    proposal_id: str,
    observation_id: str,
    data_uri: str,
) -> str:
    label = instrument or proposal_id or "product"
    digest = hashlib.sha256(f"{observation_id}{data_uri}".encode()).hexdigest()[:8]
    raw = f"{target_name}-{label}-{digest}".lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return cleaned[:120] or digest
