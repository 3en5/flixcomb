"""Compute the Netflix settings that turn a profile into an allowlist.

Netflix only offers a maturity cap plus a per-title block list. To show only approved
titles we block every other title the cap would still let through. The cap is the lowest
tier that covers all approved titles; Netflix hides everything above it by itself, which
keeps the block list short.

Our ages are estimates from TMDB and Netflix may rate a title lower than we do, so titles
up to `safety_tiers` tiers above the cap are blocked too, as are titles of unknown age.
"""

from dataclasses import dataclass, field

# Netflix's maturity tiers (minimum viewer age).
DEFAULT_TIERS = (0, 7, 13, 16, 18)


@dataclass
class BlockItem:
    kind: str
    tmdb_id: int
    title: str
    original_title: str
    year: int | None
    age: int | None


@dataclass
class Plan:
    profile: str
    cap: int
    approved: int
    approved_unknown_age: int
    block: list[BlockItem] = field(default_factory=list)


def tier_for(age: int, tiers=DEFAULT_TIERS) -> int:
    """Lowest tier that permits a title for viewers aged `age`."""
    for t in tiers:
        if t >= age:
            return t
    return tiers[-1]


def make_plan(profile: str, available: list, approvals: list, tiers=DEFAULT_TIERS,
              safety_tiers: int = 1, unknown_age_assumed: int | None = None) -> Plan:
    """Build the block plan.

    `available` rows need kind, tmdb_id, title, original_title, year, age.
    `approvals` rows need kind, tmdb_id, age, age_override.
    An approved title of unknown age is assumed to be `unknown_age_assumed` (default: the top
    tier), so it is never hidden by the cap; override per title with an age_override.
    """
    if unknown_age_assumed is None:
        unknown_age_assumed = tiers[-1]

    approved_keys = {(a["kind"], a["tmdb_id"]) for a in approvals}
    approved_ages, unknown = [], 0
    for a in approvals:
        age = a["age_override"] if a["age_override"] is not None else a["age"]
        if age is None:
            unknown += 1
            age = unknown_age_assumed
        approved_ages.append(age)

    cap = tier_for(max(approved_ages), tiers) if approved_ages else tiers[0]
    cap_index = tiers.index(cap)
    block_up_to = tiers[min(cap_index + safety_tiers, len(tiers) - 1)]
    block_all = block_up_to == tiers[-1]

    plan = Plan(profile=profile, cap=cap, approved=len(approvals), approved_unknown_age=unknown)
    for t in available:
        if (t["kind"], t["tmdb_id"]) in approved_keys:
            continue
        if block_all or t["age"] is None or t["age"] <= block_up_to:
            plan.block.append(BlockItem(t["kind"], t["tmdb_id"], t["title"],
                                        t["original_title"], t["year"], t["age"]))
    plan.block.sort(key=lambda b: (b.title.casefold(), b.tmdb_id))
    return plan
