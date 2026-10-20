"""Command line interface.

Configuration comes from the environment:
  TMDB_TOKEN          TMDB API read access token (required for `sync`)
  FLIXCOMB_DB         database path (default: flixcomb.db)
  FLIXCOMB_REGION     Netflix country (default: IL)
  FLIXCOMB_LANGUAGE   title language (default: he-IL)
"""

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict

from .db import DB
from .planner import make_plan
from .sync import sync_catalog
from .tmdb import KINDS, TMDB


def parse_ref(ref: str) -> tuple[str, int]:
    """Parse "movie:123" / "tv:456"."""
    kind, _, num = ref.partition(":")
    if kind not in KINDS or not num.isdigit():
        raise argparse.ArgumentTypeError(f"expected movie:<id> or tv:<id>, got {ref!r}")
    return kind, int(num)


def fmt_title(row) -> str:
    year = f" ({row['year']})" if row["year"] else ""
    orig = f" / {row['original_title']}" if row["original_title"] and row["original_title"] != row["title"] else ""
    age = f"{row['age']}+" if row["age"] is not None else "?"
    return f"{row['kind']}:{row['tmdb_id']}  [{age}]  {row['title']}{orig}{year}"


def cmd_sync(db: DB, args):
    token = os.environ.get("TMDB_TOKEN")
    if not token:
        sys.exit("TMDB_TOKEN is not set")
    tmdb = TMDB(token, language=os.environ.get("FLIXCOMB_LANGUAGE", "he-IL"))
    region = os.environ.get("FLIXCOMB_REGION", "IL")
    r = sync_catalog(db, tmdb, region, refresh=args.refresh,
                     progress=lambda msg: print(msg, file=sys.stderr))
    print(f"{r.available} titles on Netflix {region}: {r.added} new, {r.refreshed} refreshed")


def cmd_search(db: DB, args):
    rows = db.search(args.query, limit=args.limit)
    for row in rows:
        gone = "" if row["available"] else "  (no longer on Netflix)"
        print(fmt_title(row) + gone)
    if not rows:
        print("no matches")


def cmd_approve(db: DB, args):
    kind, tmdb_id = args.ref
    row = db.get_title(kind, tmdb_id)
    if row is None:
        print(f"warning: {kind}:{tmdb_id} is not in the catalog (run sync?)", file=sys.stderr)
    db.approve(args.profile, kind, tmdb_id, age_override=args.age, note=args.note)
    print(f"approved for {args.profile}: " + (fmt_title(row) if row else f"{kind}:{tmdb_id}"))


def cmd_revoke(db: DB, args):
    kind, tmdb_id = args.ref
    if db.revoke(args.profile, kind, tmdb_id):
        print(f"revoked {kind}:{tmdb_id} for {args.profile}")
    else:
        sys.exit(f"{kind}:{tmdb_id} was not approved for {args.profile}")


def cmd_approved(db: DB, args):
    rows = db.approvals(args.profile)
    for row in rows:
        if row["title"] is None:
            print(f"{row['kind']}:{row['tmdb_id']}  (not in catalog)")
        else:
            print(fmt_title(row))
    if not rows:
        print(f"nothing approved for {args.profile}")


def cmd_plan(db: DB, args):
    plan = make_plan(args.profile, db.available_titles(), db.approvals(args.profile),
                     safety_tiers=args.safety_tiers)
    if args.format == "json":
        json.dump(asdict(plan), sys.stdout, ensure_ascii=False, indent=2)
        print()
        return
    if args.format == "csv":
        w = csv.writer(sys.stdout)
        w.writerow(["kind", "tmdb_id", "title", "original_title", "year", "age"])
        for b in plan.block:
            w.writerow([b.kind, b.tmdb_id, b.title, b.original_title, b.year, b.age])
        return
    print(f"profile:        {plan.profile}")
    print(f"maturity cap:   {plan.cap}+")
    print(f"approved:       {plan.approved}"
          + (f" ({plan.approved_unknown_age} of unknown age, assumed top tier; use --age)"
             if plan.approved_unknown_age else ""))
    print(f"titles to block: {len(plan.block)}")
    print()
    for b in plan.block:
        orig = f" / {b.original_title}" if b.original_title and b.original_title != b.title else ""
        print(f"  {b.title}{orig}" + (f" ({b.year})" if b.year else ""))


def cmd_probe(db: DB, args):
    from pathlib import Path

    from playwright.sync_api import sync_playwright

    from .netflix import run_probe

    if args.titles:
        with open(args.titles, encoding="utf-8") as f:
            titles = [line.strip() for line in f if line.strip()]
    else:
        titles = [t["title"] for t in db.available_titles()]
    titles = titles[:args.count]
    if not titles:
        sys.exit("no titles: run sync first, or pass --titles FILE")

    print(f"Probe will try to restrict {len(titles)} titles, saving every {args.batch_size}.")
    print("Use a TEST profile only: everything added here will be hidden on it.\n")

    def wait_for_user(msg):
        input(f"\n{msg}\nPress Enter here when ready... ")

    out_dir = Path(args.out)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            args.browser_profile, headless=False, locale="he-IL",
            executable_path=os.environ.get("FLIXCOMB_CHROMIUM") or None)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(args.url)
        report = run_probe(page, titles, out_dir, wait_for_user, batch_size=args.batch_size,
                           delay=args.delay, input_selector=args.input_selector)
        ctx.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nattempted {report.attempted}, added {report.added}, "
          f"found after reload {report.persisted}")
    print(f"stopped: {report.stopped_reason or 'no, all batches completed'}")
    print(f"details in {out_dir}/report.json")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flixcomb", description="Allowlist filter for Netflix profiles")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sync", help="refresh the Netflix catalog from TMDB")
    s.add_argument("--refresh", action="store_true", help="re-fetch details of known titles")
    s.set_defaults(func=cmd_sync)

    s = sub.add_parser("search", help="search the catalog")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("approve", help="allow a title on a profile")
    s.add_argument("profile")
    s.add_argument("ref", type=parse_ref, help="movie:<id> or tv:<id>")
    s.add_argument("--age", type=int, help="override the estimated minimum age")
    s.add_argument("--note")
    s.set_defaults(func=cmd_approve)

    s = sub.add_parser("revoke", help="remove an approval")
    s.add_argument("profile")
    s.add_argument("ref", type=parse_ref)
    s.set_defaults(func=cmd_revoke)

    s = sub.add_parser("approved", help="list approved titles for a profile")
    s.add_argument("profile")
    s.set_defaults(func=cmd_approved)

    s = sub.add_parser("plan", help="show the maturity cap and titles to block for a profile")
    s.add_argument("profile")
    s.add_argument("--format", choices=["text", "csv", "json"], default="text")
    s.add_argument("--safety-tiers", type=int, default=1,
                   help="also block titles this many tiers above the cap (default: 1)")
    s.set_defaults(func=cmd_plan)

    s = sub.add_parser("probe", help="test how many title restrictions Netflix accepts")
    s.add_argument("--titles", help="file with one title per line (default: catalog titles)")
    s.add_argument("--count", type=int, default=500, help="titles to try (default: 500)")
    s.add_argument("--batch-size", type=int, default=50)
    s.add_argument("--delay", type=float, default=1.0, help="seconds between titles")
    s.add_argument("--url", default="https://www.netflix.com/account")
    s.add_argument("--browser-profile", default=".flixcomb-browser",
                   help="browser data folder; keeps you logged in between runs")
    s.add_argument("--input-selector", help="CSS selector of the title search box, if not found")
    s.add_argument("--out", default="probe-output")
    s.set_defaults(func=cmd_probe)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    db = DB(os.environ.get("FLIXCOMB_DB", "flixcomb.db"))
    try:
        args.func(db, args)
    finally:
        db.close()


if __name__ == "__main__":
    main()
