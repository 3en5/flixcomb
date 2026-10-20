"""Run the probe against a fake restrictions page that mimics Netflix's flow."""

import os

import pytest

pw = pytest.importorskip("playwright.sync_api")

CATALOG = ["Bluey", "Bluey Minisodes", "Heat", "Peppa Pig", "Lupin"]

FAKE_PAGE = """
<!doctype html><html><body>
<h1>Title Restrictions</h1>
<input role="combobox" id="q" type="text">
<ul role="listbox" id="opts"></ul>
<ul id="chips"></ul>
<button id="save">Save</button>
<script>
const catalog = %s, limit = %d;
let chips = JSON.parse(localStorage.getItem("chips") || "[]");
const render = () => document.getElementById("chips").innerHTML =
  chips.map(c => `<li>${c}</li>`).join("");
render();
document.getElementById("q").addEventListener("input", e => {
  const v = e.target.value.toLowerCase(), opts = document.getElementById("opts");
  opts.innerHTML = "";
  if (!v) return;
  for (const t of catalog.filter(t => t.toLowerCase().includes(v))) {
    const li = document.createElement("li");
    li.setAttribute("role", "option"); li.textContent = t;
    li.onclick = () => { chips.push(t); render(); opts.innerHTML = ""; e.target.value = ""; };
    opts.appendChild(li);
  }
});
document.getElementById("save").onclick = () =>
  localStorage.setItem("chips", JSON.stringify(chips.slice(0, limit)));
</script></body></html>
"""


@pytest.fixture
def page_factory(tmp_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get("FLIXCOMB_CHROMIUM") or None)

        def make(limit=1000):
            import json
            html = FAKE_PAGE % (json.dumps(CATALOG), limit)
            page = browser.new_page()
            page.route("http://netflix.test/**",
                       lambda route: route.fulfill(content_type="text/html", body=html))
            page.goto("http://netflix.test/restrictions")
            return page

        yield make
        browser.close()


def test_add_title_picks_exact_match_and_skips_unrelated(page_factory):
    from flixcomb.netflix import RestrictionsPage
    rp = RestrictionsPage(page_factory(), timeout_ms=1000)
    r = rp.add_title("Bluey")
    assert (r.status, r.matched) == ("added", "Bluey")  # not "Bluey Minisodes"
    assert rp.add_title("Lupi").status == "added"  # prefix match
    assert rp.add_title("Frozen").status == "no_match"


def test_probe_saves_in_batches_and_verifies(page_factory, tmp_path):
    from flixcomb.netflix import run_probe
    report = run_probe(page_factory(), ["Bluey", "Heat", "Peppa Pig", "Nope"], tmp_path,
                       wait_for_user=lambda msg: None, batch_size=2, delay=0, log=lambda m: None)
    assert report.stopped_reason is None
    assert (report.attempted, report.added, report.persisted) == (4, 3, 3)
    assert len(report.batches) == 2


def test_probe_detects_a_size_limit(page_factory, tmp_path):
    from flixcomb.netflix import run_probe
    report = run_probe(page_factory(limit=3), ["Bluey", "Heat", "Peppa Pig", "Lupin"], tmp_path,
                       wait_for_user=lambda msg: None, batch_size=2, delay=0, log=lambda m: None)
    assert report.stopped_reason == "only 3 of 4 saved titles came back"
    assert (tmp_path / "mismatch_2.png").exists()
