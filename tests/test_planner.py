from flixcomb.planner import make_plan, tier_for


def title(tmdb_id, age, kind="movie"):
    return {"kind": kind, "tmdb_id": tmdb_id, "title": f"T{tmdb_id}",
            "original_title": f"T{tmdb_id}", "year": 2020, "age": age}


def approval(tmdb_id, age, override=None, kind="movie"):
    return {"kind": kind, "tmdb_id": tmdb_id, "age": age, "age_override": override}


CATALOG = [title(1, 0), title(2, 7), title(3, 10), title(4, 13), title(5, 16),
           title(6, 18), title(7, None)]


def ids(plan):
    return [b.tmdb_id for b in plan.block]


def test_tier_for():
    assert tier_for(0) == 0
    assert tier_for(8) == 13
    assert tier_for(18) == 18
    assert tier_for(21) == 18


def test_cap_covers_approved_and_blocks_one_safety_tier_above():
    plan = make_plan("kids", CATALOG, [approval(2, 7)])
    assert plan.cap == 7
    # blocks everything up to 13 plus unknown ages, but not the approved title
    assert ids(plan) == [1, 3, 4, 7]


def test_zero_safety_tiers_blocks_only_up_to_cap():
    plan = make_plan("kids", CATALOG, [approval(2, 7)], safety_tiers=0)
    assert ids(plan) == [1, 7]


def test_high_cap_blocks_everything_not_approved():
    plan = make_plan("teen", CATALOG, [approval(5, 16)])
    assert plan.cap == 16
    assert ids(plan) == [1, 2, 3, 4, 6, 7]


def test_unknown_age_approval_assumes_top_tier_unless_overridden():
    plan = make_plan("kids", CATALOG, [approval(7, None)])
    assert plan.cap == 18 and plan.approved_unknown_age == 1
    plan = make_plan("kids", CATALOG, [approval(7, None, override=0)])
    assert plan.cap == 0 and plan.approved_unknown_age == 0
    assert ids(plan) == [1, 2]


def test_no_approvals_uses_lowest_tier():
    plan = make_plan("kids", CATALOG, [])
    assert plan.cap == 0
    assert ids(plan) == [1, 2, 7]


def test_same_id_different_kind_is_not_approved():
    catalog = [title(1, 0, kind="movie"), title(1, 0, kind="tv")]
    plan = make_plan("kids", catalog, [approval(1, 0, kind="movie")])
    assert [(b.kind, b.tmdb_id) for b in plan.block] == [("tv", 1)]
