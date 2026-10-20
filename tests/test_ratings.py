from flixcomb import ratings


def test_cert_to_age():
    assert ratings.cert_to_age("PG-13") == 13
    assert ratings.cert_to_age("tv-ma") == 17
    assert ratings.cert_to_age("16+") == 16
    assert ratings.cert_to_age("12") == 12
    assert ratings.cert_to_age("NR") is None
    assert ratings.cert_to_age("") is None
    assert ratings.cert_to_age(None) is None


def test_pick_age_prefers_israel_then_strictest():
    certs = {"US": ["PG"], "IL": ["12", "16"]}
    assert ratings.pick_age(certs) == (16, "IL:16")


def test_pick_age_falls_back_past_unusable_ratings():
    certs = {"IL": ["NR"], "US": ["R"]}
    assert ratings.pick_age(certs) == (17, "US:R")
    assert ratings.pick_age({"FR": ["10"]}) == (None, None)


def test_movie_and_tv_payloads():
    movie = {"results": [{"iso_3166_1": "US", "release_dates": [
        {"certification": ""}, {"certification": "PG-13"}]}]}
    assert ratings.movie_certs(movie) == {"US": ["PG-13"]}
    tv = {"results": [{"iso_3166_1": "US", "rating": "TV-Y7"}, {"iso_3166_1": "GB", "rating": ""}]}
    assert ratings.tv_certs(tv) == {"US": ["TV-Y7"]}
