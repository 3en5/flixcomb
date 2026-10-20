"""Convert TMDB certifications to an estimated minimum viewer age."""

import re

# Countries consulted in order; the first one with a usable rating wins.
COUNTRY_PRIORITY = ("IL", "US", "GB")

_KNOWN = {
    # US movies
    "G": 0, "PG": 8, "PG-13": 13, "R": 17, "NC-17": 18,
    # US TV
    "TV-Y": 0, "TV-Y7": 7, "TV-Y7-FV": 7, "TV-G": 0, "TV-PG": 10, "TV-14": 14, "TV-MA": 17,
    # GB
    "U": 0, "12A": 12, "R18": 18,
}

_NUMERIC = re.compile(r"^(\d{1,2})\+?$")


def cert_to_age(cert: str | None) -> int | None:
    if not cert:
        return None
    cert = cert.strip().upper()
    if cert in _KNOWN:
        return _KNOWN[cert]
    m = _NUMERIC.match(cert)
    return int(m.group(1)) if m else None


def pick_age(certs_by_country: dict[str, list[str]]) -> tuple[int | None, str | None]:
    """Return (age, "COUNTRY:CERT") from the highest-priority country with a known rating.

    Within one country the strictest (highest) rating is used.
    """
    for country in COUNTRY_PRIORITY:
        ages = [(cert_to_age(c), c) for c in certs_by_country.get(country, [])]
        ages = [(a, c) for a, c in ages if a is not None]
        if ages:
            age, cert = max(ages)
            return age, f"{country}:{cert}"
    return None, None


def movie_certs(release_dates: dict) -> dict[str, list[str]]:
    """Extract certifications from a TMDB movie `release_dates` payload."""
    out: dict[str, list[str]] = {}
    for country in release_dates.get("results", []):
        certs = [r.get("certification", "") for r in country.get("release_dates", [])]
        out[country["iso_3166_1"]] = [c for c in certs if c]
    return out


def tv_certs(content_ratings: dict) -> dict[str, list[str]]:
    """Extract certifications from a TMDB TV `content_ratings` payload."""
    out: dict[str, list[str]] = {}
    for r in content_ratings.get("results", []):
        if r.get("rating"):
            out.setdefault(r["iso_3166_1"], []).append(r["rating"])
    return out
