"""Refresh the local catalog from TMDB."""

from dataclasses import dataclass
from typing import Callable

from .db import DB
from .tmdb import KINDS, TMDB


@dataclass
class SyncResult:
    available: int = 0
    added: int = 0
    refreshed: int = 0


def sync_catalog(db: DB, tmdb: TMDB, region: str, refresh: bool = False,
                 progress: Callable[[str], None] = lambda _: None) -> SyncResult:
    """Record which titles are on Netflix in `region`.

    Details are fetched only for titles not yet in the catalog, unless `refresh` is set.
    """
    result = SyncResult()
    for kind in KINDS:
        progress(f"listing {kind} titles...")
        ids = set(tmdb.discover_ids(kind, region))
        known = db.known_ids(kind)
        todo = ids if refresh else ids - known
        for i, tmdb_id in enumerate(sorted(todo), 1):
            db.upsert_title(tmdb.details(kind, tmdb_id))
            if i % 100 == 0:
                progress(f"{kind}: {i}/{len(todo)} details fetched")
                db.commit()
        db.mark_availability(kind, ids)
        db.commit()
        result.available += len(ids)
        result.added += len(ids - known)
        result.refreshed += len(todo & known)
    return result
