"""Drive the Netflix parental controls page in a real browser.

Netflix has no API for this, so we work the website the way a person would. The page
structure is not documented and may change; element lookups are deliberately generic
(roles and visible text, Hebrew or English) and can be overridden with a CSS selector.
"""

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import Locator, Page, TimeoutError as PWTimeout

SAVE_BUTTON = re.compile(r"^\s*(save|שמור|שמירה)\s*$", re.I)


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().casefold()


@dataclass
class AddResult:
    title: str
    status: str  # "added", "no_match", "error"
    matched: str | None = None
    detail: str | None = None


class RestrictionsPage:
    def __init__(self, page: Page, input_selector: str | None = None, timeout_ms: int = 5000):
        self.page = page
        self.input_selector = input_selector
        self.timeout_ms = timeout_ms

    def find_input(self) -> Locator | None:
        """The title search box, or None if it is not on the page."""
        candidates = []
        if self.input_selector:
            candidates.append(self.page.locator(self.input_selector))
        candidates += [
            self.page.get_by_role("combobox"),
            self.page.locator("input[type=search]"),
            self.page.locator("input[type=text]"),
        ]
        for loc in candidates:
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    return loc.nth(i)
        return None

    def add_title(self, title: str) -> AddResult:
        box = self.find_input()
        if box is None:
            return AddResult(title, "error", detail="title search box not found")
        try:
            box.fill("")
            box.press_sequentially(title, delay=30)
            options = self.page.get_by_role("option")
            try:
                options.first.wait_for(state="visible", timeout=self.timeout_ms)
            except PWTimeout:
                return AddResult(title, "no_match", detail="no suggestions")
            want = normalize(title)
            texts = [normalize(t) for t in options.all_inner_texts()]
            # Prefer an exact match, then a suggestion starting with the title. Never pick an
            # unrelated suggestion: that would restrict the wrong title.
            for pick in (lambda t: t == want, lambda t: t.startswith(want)):
                for i, text in enumerate(texts):
                    if pick(text):
                        matched = options.nth(i).inner_text().strip()
                        options.nth(i).click()
                        return AddResult(title, "added", matched=matched)
            box.fill("")
            return AddResult(title, "no_match", detail=f"suggestions: {texts[:5]}")
        except Exception as e:  # keep going; the caller records and reports it
            return AddResult(title, "error", detail=str(e).splitlines()[0])

    def save(self) -> bool:
        button = self.page.get_by_role("button", name=SAVE_BUTTON)
        if button.count() == 0:
            return False
        button.first.click()
        self.page.wait_for_load_state("networkidle")
        return True

    def visible_text(self) -> str:
        return normalize(self.page.inner_text("body"))


@dataclass
class ProbeReport:
    url: str = ""
    attempted: int = 0
    added: int = 0
    persisted: int = 0
    stopped_reason: str | None = None
    batches: list[dict] = field(default_factory=list)
    results: list[AddResult] = field(default_factory=list)


def snapshot(page: Page, out_dir: Path, name: str):
    """Save HTML and a screenshot for diagnosing layout problems."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(out_dir / f"{name}.png"), full_page=True)


def run_probe(page: Page, titles: list[str], out_dir: Path, wait_for_user,
              batch_size: int = 50, delay: float = 1.0, input_selector: str | None = None,
              log=print) -> ProbeReport:
    """Add `titles` to the restrictions list in batches, saving and re-checking after each.

    Stops at the first batch where saved titles do not all come back after a reload, which
    is what a size limit would look like.
    """
    rp = RestrictionsPage(page, input_selector)
    report = ProbeReport()

    wait_for_user(
        "In the browser: log in, open the TEST profile's parental controls\n"
        "(Account > Profile > Viewing restrictions), enter your password if asked,\n"
        "and stop when the title restrictions search box is visible.")
    if rp.find_input() is None:
        snapshot(page, out_dir, "no_input")
        report.stopped_reason = "title search box not found; see no_input.html/png"
        return report
    report.url = page.url
    snapshot(page, out_dir, "start")

    persisted: list[AddResult] = []
    for start in range(0, len(titles), batch_size):
        batch = titles[start:start + batch_size]
        added = []
        for title in batch:
            r = rp.add_title(title)
            report.results.append(r)
            report.attempted += 1
            if r.status == "added":
                added.append(r)
                report.added += 1
            log(f"  [{report.attempted}/{len(titles)}] {r.status}: {title}"
                + (f" -> {r.matched}" if r.matched and r.matched != title else "")
                + (f" ({r.detail})" if r.detail else ""))
            time.sleep(delay)

        if not rp.save():
            snapshot(page, out_dir, f"no_save_{start}")
            report.stopped_reason = "save button not found"
            break

        page.goto(report.url)
        page.wait_for_load_state("networkidle")
        if rp.find_input() is None:
            wait_for_user("Netflix may be asking for your password again. "
                          "Enter it until the restrictions page is back.")
        text = rp.visible_text()
        persisted += added
        kept = sum(1 for r in persisted if normalize(r.matched or r.title) in text)
        report.persisted = kept
        report.batches.append({"saved_total": len(persisted), "found_after_reload": kept})
        log(f"batch saved: {kept}/{len(persisted)} restricted titles found after reload")
        if kept < len(persisted):
            snapshot(page, out_dir, f"mismatch_{start}")
            report.stopped_reason = f"only {kept} of {len(persisted)} saved titles came back"
            break
    return report
