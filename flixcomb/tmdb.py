"""Minimal TMDB client for listing what is streaming on Netflix in a region."""

from dataclasses import dataclass
from typing import Iterator

import httpx

from . import ratings

BASE_URL = "https://api.themoviedb.org/3"
NETFLIX_PROVIDER_ID = 8
KINDS = ("movie", "tv")

# TMDB's discover endpoint refuses pages beyond this.
MAX_DISCOVER_PAGES = 500


@dataclass
class Title:
    kind: str  # "movie" or "tv"
    tmdb_id: int
    title: str
    original_title: str
    year: int | None
    overview: str
    genres: list[str]
    age: int | None
    cert: str | None


class TMDB:
    def __init__(self, token: str, language: str = "he-IL", client: httpx.Client | None = None):
        self.language = language
        self.client = client or httpx.Client(base_url=BASE_URL, timeout=30)
        self.client.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, **params) -> dict:
        resp = self.client.get(path, params={"language": self.language, **params})
        resp.raise_for_status()
        return resp.json()

    def discover_ids(self, kind: str, region: str) -> Iterator[int]:
        """Yield TMDB ids of every `kind` title on Netflix (subscription) in `region`."""
        page, total = 1, 1
        while page <= min(total, MAX_DISCOVER_PAGES):
            data = self._get(
                f"/discover/{kind}",
                watch_region=region,
                with_watch_providers=NETFLIX_PROVIDER_ID,
                with_watch_monetization_types="flatrate",
                sort_by="popularity.desc",
                page=page,
            )
            total = data.get("total_pages", 1)
            for item in data.get("results", []):
                yield item["id"]
            page += 1

    def details(self, kind: str, tmdb_id: int) -> Title:
        if kind == "movie":
            d = self._get(f"/movie/{tmdb_id}", append_to_response="release_dates")
            certs = ratings.movie_certs(d.get("release_dates", {}))
            name, original, date = d.get("title"), d.get("original_title"), d.get("release_date")
        else:
            d = self._get(f"/tv/{tmdb_id}", append_to_response="content_ratings")
            certs = ratings.tv_certs(d.get("content_ratings", {}))
            name, original, date = d.get("name"), d.get("original_name"), d.get("first_air_date")
        age, cert = ratings.pick_age(certs)
        return Title(
            kind=kind,
            tmdb_id=tmdb_id,
            title=name or original or "",
            original_title=original or "",
            year=int(date[:4]) if date else None,
            overview=d.get("overview") or "",
            genres=[g["name"] for g in d.get("genres", [])],
            age=age,
            cert=cert,
        )
