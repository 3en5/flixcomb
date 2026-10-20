import json

import httpx

from flixcomb import cli
from flixcomb.db import DB
from flixcomb.sync import sync_catalog
from flixcomb.tmdb import BASE_URL, TMDB

MOVIES = {
    1: {"title": "מלך האריות", "original_title": "The Lion King", "release_date": "1994-06-15",
        "overview": "", "genres": [{"name": "אנימציה"}],
        "release_dates": {"results": [{"iso_3166_1": "US", "release_dates": [{"certification": "G"}]}]}},
    2: {"title": "Heat", "original_title": "Heat", "release_date": "1995-12-15", "overview": "",
        "genres": [], "release_dates": {"results": [{"iso_3166_1": "US",
                                                    "release_dates": [{"certification": "R"}]}]}},
}
SHOWS = {
    10: {"name": "Bluey", "original_name": "Bluey", "first_air_date": "2018-10-01", "overview": "",
         "genres": [], "content_ratings": {"results": [{"iso_3166_1": "US", "rating": "TV-Y"}]}},
}


def fake_tmdb(movies=MOVIES, shows=SHOWS, calls=None):
    def handler(request: httpx.Request):
        if calls is not None:
            calls.append(request.url.path)
        parts = request.url.path.strip("/").split("/")[1:]  # drop API version
        if parts[0] == "discover":
            assert request.url.params["with_watch_providers"] == "8"
            src = movies if parts[1] == "movie" else shows
            return httpx.Response(200, json={"page": 1, "total_pages": 1,
                                             "results": [{"id": i} for i in src]})
        src = movies if parts[0] == "movie" else shows
        return httpx.Response(200, json=src[int(parts[1])])
    client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler))
    return TMDB("token", client=client)


def test_sync_fetches_details_once_and_tracks_availability(tmp_path):
    db = DB(tmp_path / "f.db")
    calls = []
    r = sync_catalog(db, fake_tmdb(calls=calls), "IL")
    assert (r.available, r.added) == (3, 3)
    lion = db.get_title("movie", 1)
    assert lion["title"] == "מלך האריות" and lion["age"] == 0 and lion["cert"] == "US:G"
    assert db.get_title("movie", 2)["age"] == 17

    # second sync: Heat left Netflix, no detail calls for known titles
    calls.clear()
    r = sync_catalog(db, fake_tmdb(movies={1: MOVIES[1]}, calls=calls), "IL")
    assert (r.available, r.added) == (2, 0)
    assert all("discover" in c for c in calls)
    assert db.get_title("movie", 2)["available"] == 0
    assert {(t["kind"], t["tmdb_id"]) for t in db.available_titles()} == {("movie", 1), ("tv", 10)}


def test_cli_approve_and_plan(tmp_path, monkeypatch, capsys):
    path = tmp_path / "f.db"
    db = DB(path)
    sync_catalog(db, fake_tmdb(), "IL")
    db.close()
    monkeypatch.setenv("FLIXCOMB_DB", str(path))

    cli.main(["approve", "kids", "tv:10"])
    cli.main(["approved", "kids"])
    assert "Bluey" in capsys.readouterr().out

    cli.main(["plan", "kids", "--format", "json"])
    plan = json.loads(capsys.readouterr().out)
    assert plan["cap"] == 0
    # Lion King (0) blocked; Heat (17) is far above the cap and hidden by Netflix itself
    assert [(b["kind"], b["tmdb_id"]) for b in plan["block"]] == [("movie", 1)]

    cli.main(["search", "lion"])
    assert "movie:1" in capsys.readouterr().out
