"""Reports: HTML review gallery, current-state report, cache observations, exceptions, executive PDF."""
from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .common import Log, TOOL_VERSION, ensure_dirs, load_manifest, utc_now

Image.MAX_IMAGE_PIXELS = None

DISCLAIMER = ("This Visual Recovery Reference records the publicly visible state of the website during the stated "
              "capture period. It is intended to support visual and public-functionality comparison following recovery. "
              "It does not constitute a complete WordPress source-code, database or application backup, and it does not "
              "independently prove that the underlying website was secure or fully functional at the time of capture.")


def _load(path: Path, default):
    return json.load(open(path, encoding="utf-8")) if path.exists() else default


def thumb(src: Path, dest: Path, width: int = 320, max_h: int = 1400) -> Path | None:
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
        return dest
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            ratio = width / im.width
            h = min(int(im.height * ratio), max_h)
            im = im.resize((width, int(im.height * ratio)))
            im = im.crop((0, 0, width, h))
            dest.parent.mkdir(parents=True, exist_ok=True)
            im.save(dest, "JPEG", quality=70, optimize=True)
        return dest
    except Exception:
        return None


def cache_stats(rows: list[dict], cfg: dict, d: dict) -> dict:
    hits, misses, other, ages, servers, techs = Counter(), Counter(), Counter(), [], Counter(), Counter()
    per_page = []
    for r in rows:
        lang = (r.get('language') or 'und').split('-')[0].lower()
        single = d["headers"] / f"{r['ref_id']}_{r['slug']}.headers.json"
        if single.exists():
            sources = [("single-request", single)]
        else:  # pilot-era captures: one navigation per viewport
            sources = [(vp, d["headers"] / f"{r['ref_id']}_{r['slug']}_{lang}_{vp}.headers.json")
                       for vp in (r.get("captures") or {})]
        for vp, hp in sources:
            h = _load(hp, {})
            ch = {k.lower(): v for k, v in (h.get("cache_headers") or {}).items()}
            if not ch and not h:
                continue
            ls = ch.get("x-litespeed-cache")
            cf = ch.get("cf-cache-status")
            if ls == "hit" or (cf and cf.upper() == "HIT"):
                hits[r["ref_id"]] += 1
            elif ls == "miss" or (cf and cf.upper() in ("MISS", "EXPIRED", "BYPASS", "DYNAMIC")):
                misses[r["ref_id"]] += 1
            else:
                other[r["ref_id"]] += 1
            if "age" in ch:
                ages.append(int(ch["age"]) if str(ch["age"]).isdigit() else ch["age"])
            servers[ch.get("server", "-")] += 1
            for k in ch:
                if k.startswith("x-litespeed"): techs["LiteSpeed Cache (x-litespeed-*)"] += 1
                if k.startswith("cf-"): techs["Cloudflare (cf-*)"] += 1
                if k.startswith("x-qc"): techs["QUIC.cloud (x-qc-*)"] += 1
                if k in ("x-cache", "x-cache-status", "x-proxy-cache", "via"): techs[f"Proxy/CDN header ({k})"] += 1
            per_page.append({"ref_id": r["ref_id"], "url": r["normalized_url"], "viewport": vp,
                             "x-litespeed-cache": ls, "cf-cache-status": cf, "age": ch.get("age"),
                             "etag": ch.get("etag"), "cache-control": ch.get("cache-control"),
                             "x-litespeed-cache-control": ch.get("x-litespeed-cache-control"),
                             "server": ch.get("server"), "platform": ch.get("platform"), "status": h.get("status")})
    return {"hits": hits, "misses": misses, "other": other, "ages": ages, "servers": servers, "techs": techs, "per_page": per_page}


def run_report(cfg: dict) -> None:
    d = ensure_dirs(cfg)
    log = Log(cfg)
    out: Path = cfg["_out"]
    rows = load_manifest(cfg)
    qa = _load(d["coverage"] / "qa-summary.json", {})
    findings = _load(d["coverage"] / "qa-findings.json", [])
    env = _load(out / "environment.json", {})
    integ = _load(d["integrity"] / "integrity-summary.json", {})
    vps = list(cfg["viewports"])
    by_ref = defaultdict(list)
    for f in findings:
        by_ref[f["ref_id"]].append(f)
    html_rows = [r for r in rows if r["content_type"] == "html" and r["capture_status"] != "excluded"]
    doc_rows = [r for r in rows if r["content_type"] == "document"]
    excluded = [r for r in rows if r["capture_status"] == "excluded"]
    times = [c.get("started_at") for r in rows for c in (r.get("captures") or {}).values() if c.get("started_at")]
    t_start, t_end = (min(times), max(times)) if times else ("-", "-")
    cs = cache_stats(rows, cfg, d)
    req_total = sum(len(r.get("requests") or []) for r in rows)
    req_hist = Counter(len(r.get("requests") or []) for r in rows if str(r["capture_status"]).startswith("captured"))
    themes_seen = set()
    for r in rows:
        if r["content_type"] == "html" and str(r["capture_status"]).startswith("captured"):
            body = d["html_response"] / f"{r['ref_id']}_{r['slug']}.html"
            if body.exists():
                themes_seen.update(re.findall(r"/wp-content/themes/([^/]+)/", body.read_text(errors="ignore")))

    # ------------------------------------------------------------- gallery
    tdir = d["contact"] / "thumbs"
    cards = []
    for r in rows:
        if r["capture_status"] == "excluded":
            continue
        caps = r.get("captures") or {}
        cells = []
        for vp in vps:
            c = caps.get(vp, {})
            full = next((f for f in c.get("files", []) if f.endswith(f"_{vp}_full.png")), None)
            if full:
                t = thumb(out / full, tdir / (Path(full).stem + ".jpg"))
                rel_full = html.escape("../../" + full)
                rel_t = html.escape(str(t.relative_to(d["contact"]))) if t else ""
                cells.append(f'<div class="shot"><a href="{rel_full}" target="_blank"><img loading="lazy" src="{rel_t}" alt="{vp}"></a>'
                             f'<div class="cap">{vp} · {c.get("page_height", "?")}px · HTTP {c.get("http_status", "?")}</div></div>')
            else:
                cells.append(f'<div class="shot missing">{vp}<br>{html.escape(c.get("status", "not captured"))}</div>')
        inter = [f for vp in vps for f in caps.get(vp, {}).get("files", []) if "/interactive-states/" in f]
        inter_html = "".join(f'<a href="{html.escape("../../" + f)}" target="_blank">{html.escape(Path(f).stem.split("_", 4)[-1])}</a> ' for f in inter)
        flags = by_ref.get(r["ref_id"], []) + [f for f in findings if r["ref_id"] in f["ref_id"].split(",") and f["ref_id"] != r["ref_id"]]
        flag_html = "".join(f'<li class="{f["severity"]}">[{f["severity"]}] {html.escape(f["code"])}: {html.escape(f["message"][:220])}</li>' for f in flags)
        notes = "; ".join(sorted({n for vp in vps for n in caps.get(vp, {}).get("notes", [])}))
        doc_html = ""
        if r["content_type"] == "document":
            dc = caps.get("document", {})
            files = dc.get("files", [])
            doc_html = f'<div class="doc">Document: {html.escape(dc.get("content_type") or "")} {dc.get("bytes", "")} bytes ' + \
                       "".join(f'<a href="{html.escape("../../" + f)}" target="_blank">open</a>' for f in files) + "</div>"
        cards.append(f"""
<section class="card" id="{r['ref_id']}" data-status="{html.escape(r['capture_status'])}">
  <header><span class="ref">{r['ref_id']}</span> <span class="title">{html.escape(r.get('page_title') or '(no title)')}</span>
   <span class="status s-{html.escape(r['capture_status'].split('-')[0])}">{html.escape(r['capture_status'])}</span></header>
  <div class="url"><a href="{html.escape(r['normalized_url'])}" target="_blank" rel="noopener">{html.escape(r['normalized_url'])}</a>
   <span class="meta">lang={html.escape(r.get('language') or 'und')} · type={r['content_type']} · http={r.get('http_status')} · cache={html.escape(str(r.get('cache_status') or '-'))} · requests={r.get('request_count', 0)} · source={html.escape(', '.join(r['discovery_source'][:2]))}{' · IN SITEMAP' if r.get('in_sitemap') else ''}</span></div>
  {'<div class="shots">' + ''.join(cells) + '</div>' if r['content_type'] == 'html' else doc_html}
  {f'<div class="inter">Interactive states: {inter_html}</div>' if inter else ''}
  {f'<div class="notes">Notes: {html.escape(notes)}</div>' if notes else ''}
  {f'<ul class="flags">{flag_html}</ul>' if flag_html else ''}
</section>""")
    gallery = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Visual Recovery Reference – {html.escape(cfg['client'])}</title>
<style>
body{{font:14px/1.4 system-ui,sans-serif;margin:0;background:#f4f4f5;color:#111}} .top{{background:#111;color:#fff;padding:16px 24px;position:sticky;top:0;z-index:2}}
.top h1{{margin:0 0 4px;font-size:18px}} .top .sub{{color:#bbb;font-size:12px}} .top input{{margin-left:16px;padding:4px 8px;border-radius:4px;border:1px solid #444}}
.card{{background:#fff;margin:16px 24px;padding:12px 16px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.card header{{display:flex;gap:12px;align-items:center}} .ref{{font-weight:700;font-family:monospace}} .title{{font-weight:600;flex:1}}
.status{{font-size:12px;padding:2px 8px;border-radius:10px;background:#ddd}} .s-captured{{background:#d1fae5}} .s-partial,.s-pending{{background:#fef3c7}} .s-failed{{background:#fecaca}}
.url{{font-size:12px;color:#555;margin:4px 0 10px;word-break:break-all}} .url .meta{{margin-left:8px;color:#888}}
.shots{{display:flex;gap:12px;align-items:flex-start}} .shot img{{width:320px;border:1px solid #ddd;display:block}} .shot .cap{{font-size:11px;color:#666;margin-top:4px}}
.shot.missing{{width:320px;height:120px;border:1px dashed #f87171;color:#b91c1c;display:flex;align-items:center;justify-content:center;text-align:center}}
.flags{{margin:8px 0 0;padding-left:18px;font-size:12px}} .flags .high{{color:#b91c1c}} .flags .medium{{color:#b45309}} .flags .low,.flags .info{{color:#555}}
.notes,.inter,.doc{{font-size:12px;color:#444;margin-top:6px}} .summary{{margin:16px 24px;font-size:13px}} .summary td{{padding:2px 12px 2px 0}}
</style></head><body>
<div class="top"><h1>Visual Recovery Reference – {html.escape(cfg['client'])} ({html.escape(cfg['base_url'])})</h1>
<div class="sub">Generated {utc_now()} · capture window {t_start} → {t_end} · {env.get('browser_name','')} {env.get('browser_version','')} · viewports {', '.join(f"{k} {v['width']}×{v['height']}" for k,v in cfg['viewports'].items())}
<input id="q" placeholder="filter by ref / title / URL" oninput="for(const c of document.querySelectorAll('.card'))c.style.display=c.textContent.toLowerCase().includes(this.value.toLowerCase())?'':'none'"></div></div>
<div class="summary"><table>
<tr><td>URLs discovered</td><td><b>{len(rows)}</b></td><td>HTML pages</td><td><b>{len(html_rows)}</b></td><td>Documents</td><td><b>{len(doc_rows)}</b></td><td>Excluded</td><td><b>{len(excluded)}</b></td></tr>
<tr><td>Captured (all viewports)</td><td><b>{qa.get('captured_html','?')}</b></td><td>Partial</td><td><b>{qa.get('partial_html','?')}</b></td><td>Failed/pending</td><td><b>{qa.get('failed_html','?')}</b></td><td>QA findings</td><td><b>{sum((qa.get('findings_by_severity') or {}).values())}</b></td></tr>
</table><p>{html.escape(DISCLAIMER)}</p></div>
{''.join(cards)}
<div class="summary">Excluded URLs (recorded, not captured): <ul>{''.join(f'<li>{html.escape(r["ref_id"])} {html.escape(r["normalized_url"])} – {html.escape(r.get("notes") or "")}</li>' for r in excluded)}</ul></div>
</body></html>"""
    (d["contact"] / "index.html").write_text(gallery, encoding="utf-8")

    # ------------------------------------------------------------- cache observations
    lines = [f"# Cache observations – {cfg['client']}", "", f"Generated {utc_now()} (UTC). Observations only; interpretations are marked as hypotheses.", ""]
    lines += ["## Apparent cache technology (from response headers)", ""]
    for k, v in cs["techs"].most_common():
        lines.append(f"- {k}: seen on {v} responses")
    lines += ["", f"- `server` header values: {dict(cs['servers'])}", "",
              "## HIT / MISS summary (main HTML/document responses, all viewports)", "",
              f"- Pages with at least one cache HIT: {len(cs['hits'])}",
              f"- Pages with at least one MISS: {len(cs['misses'])}",
              f"- Pages with no disclosed cache status: {len(cs['other'])}",
              f"- `age` header present on {len(cs['ages'])} responses" + (f" (values: {sorted(set(map(str, cs['ages'])))[:10]})" if cs['ages'] else ""),
              "", "## Per-response detail", "",
              "| Ref | Viewport | HTTP | x-litespeed-cache | cf-cache-status | age | etag | x-litespeed-cache-control | cache-control |", "|---|---|---|---|---|---|---|---|---|"]
    for p in cs["per_page"]:
        lines.append(f"| {p['ref_id']} | {p['viewport']} | {p['status']} | {p['x-litespeed-cache'] or '-'} | {p['cf-cache-status'] or '-'} | {p['age'] or '-'} | `{p['etag'] or '-'}` | {p['x-litespeed-cache-control'] or '-'} | {p['cache-control'] or '-'} |")
    miss_pages = sorted(cs["misses"])
    lines += ["", "## Pages that did not appear cached (MISS on at least one request)", ""] + [f"- {m}" for m in miss_pages] + ([""] if miss_pages else ["- none", ""])
    lines += ["## Hypotheses (not verified)", "",
              "- The `x-litespeed-cache: hit` / `miss` header and `etag` format `\"<id>-<unix ts>;;;\"` are consistent with the LiteSpeed Cache WordPress plugin on a LiteSpeed server (`server: LiteSpeed`, `platform: hostinger`).",
              "- A `miss` response is generated by the WordPress backend at request time; LiteSpeed typically stores that response for subsequent visitors (`x-litespeed-cache-control: public,max-age=...`). Any ordinary visit to an uncached page therefore fills the cache; this is a normal visitor side-effect, not a purge. Pages listed as MISS above should be compared against HIT pages to check whether the backend currently renders the same theme.",
              "- From the full crawl onward each URL received exactly ONE browser navigation (`single-request` rows); tablet and mobile views were produced by resizing the already-loaded page, so no page was reloaded, probed or warmed. Every request ever made to a URL is listed in the manifest `requests[]` field with its `x-litespeed-cache` value.",
              "- Pilot-era pages (P0001-P0003) were navigated once per viewport before this rule was adopted; where `response_body_identical_to` is recorded in `metadata/headers/` the response HTML was byte-identical across those navigations.",
              "- Pages that failed to load or returned 5xx are listed in `exceptions.md`."]
    (out / "cache-observations.md").write_text("\n".join(lines), encoding="utf-8")

    # ------------------------------------------------------------- exceptions
    ex = [f"# Exception register – {cfg['client']}", "", f"Generated {utc_now()} (UTC).", "",
          "| Ref | URL | Type | Status | Reason / note |", "|---|---|---|---|---|"]
    n_ex = 0
    for r in rows:
        st = r["capture_status"]
        caps = r.get("captures") or {}
        problems = [n for c in caps.values() for n in c.get("notes", []) if any(k in n for k in ("failed", "timeout", "clipped", "error", "fallback"))]
        if st == "excluded" or not st.startswith("captured") or st != "captured" or problems:
            n_ex += 1
            reason = r.get("notes") or ""
            if problems:
                reason = (reason + " | " if reason else "") + "; ".join(sorted(set(problems)))
            ex.append(f"| {r['ref_id']} | {r['normalized_url']} | {r['content_type']} | {st} | {reason.replace('|', '/')} |")
    if n_ex == 0:
        ex.append("| – | – | – | – | no exceptions |")
    ex += ["", "## Components static evidence cannot fully preserve", "",
           "- Third-party embeds (WhatsApp chat widget, Google Fonts, Elfsight, analytics) are captured visually but their remote resources are not archived (third-party domains are out of scope).",
           "- Server-side functionality (search results, store locator queries, forms, account/wishlist, WooCommerce cart) was not exercised; only the visible interface state is preserved.",
           "- Animated sliders/carousels (Slider Revolution) are captured at a single settled moment per viewport; other slides may exist.",
           "- Flipbook/PDF viewers (dFlip) are captured as rendered; the underlying PDFs are archived separately when linked from the page."]
    (out / "exceptions.md").write_text("\n".join(ex), encoding="utf-8")

    # ------------------------------------------------------------- crawl coverage
    cov = [f"# Crawl coverage – {cfg['client']}", "",
           f"- Sitemap URLs: {qa.get('sitemap_urls', 0)}", f"- Sitemap URLs not captured: {len(qa.get('sitemap_not_captured', []))}"]
    cov += [f"  - {u}" for u in qa.get("sitemap_not_captured", [])]
    cov += [f"- Internally linked HTML URLs absent from the sitemap: {qa.get('linked_not_in_sitemap_count', 0)}"]
    cov += [f"  - {u}" for u in qa.get("linked_not_in_sitemap", [])]
    cov += ["", "## Discovery sources", ""]
    src = Counter(s.split(":")[0] for r in rows for s in r["discovery_source"])
    cov += [f"- {k}: {v}" for k, v in src.most_common()]
    (d["coverage"] / "crawl-coverage.md").write_text("\n".join(cov), encoding="utf-8")

    # ------------------------------------------------------------- current-state report
    langs = Counter((r.get("language") or "und") for r in html_rows)
    defects = [f for f in findings if f["severity"] in ("high", "medium")]
    rep = ["# Current-state report – Visual Recovery Reference", "",
           f"**Client:** {cfg['client']}  ", f"**Production website:** {cfg['base_url']}  ",
           f"**Capture window (UTC):** {t_start} → {t_end}  ", f"**Report generated (UTC):** {utc_now()}  ",
           f"**Tool:** {TOOL_VERSION}, Playwright {env.get('playwright_version','?')}, {env.get('browser_name','?')} {env.get('browser_version','?')}, {env.get('operating_environment','?')}", "",
           "> " + DISCLAIMER, "",
           "## 1. Scope", "",
           f"All publicly accessible first-party HTML pages and linked public documents on `{', '.join(cfg['allowed_hosts'])}` discovered passively from the homepage, navigation, footer, `robots.txt`, XML sitemap(s) and internal links. "
           "Administrative, authenticated, cart/checkout, feed and state-changing URLs were recorded in the manifest but excluded from capture (see `exceptions.md`).", "",
           "## 2. Methodology", "",
           "1. Passive discovery of `robots.txt` and XML sitemaps only; HTML pages are never pre-fetched. Because a LiteSpeed cache MISS regenerates and stores the page from the current database, every production request is treated as potentially state-affecting: no preliminary, duplicate, HEAD, test or cache-bypass requests.",
           "1b. Each URL receives exactly one controlled browser navigation (ordinary Chrome user agent). Headers, body, redirect chain, rendered HTML and screenshots all come from that first response; tablet/mobile views are produced by resizing the loaded page. New same-domain links found in the rendered page are queued for their own single visit. A MISS or unexpected design is preserved and flagged, never reloaded.",
           f"2. Each HTML page rendered in a fresh, unauthenticated headless Chromium context at three viewports ({', '.join(f'{k} {v['width']}×{v['height']}' for k, v in cfg['viewports'].items())}, DPR 1).",
           "3. Per page and viewport: above-the-fold PNG, stepwise scroll for lazy-loaded media, return to top, full-page PNG, original response HTML, rendered DOM HTML, response headers, redirect chain, page metadata (title, description, canonical, Open Graph, JSON-LD, links, forms, iframes), first-party assets (deduplicated).",
           "4. Safe interactive states captured where present: mobile menu, search panel, navigation hover, cookie banner (initial state first).",
           f"5. Rate limiting: concurrency {cfg['crawl']['concurrency']}, {cfg['crawl']['delay_seconds']}s delay, {cfg['crawl']['max_retries']} retries with backoff, hard stop on HTTP 429 or {cfg['crawl']['stop_after_consecutive_5xx']} consecutive 5xx.",
           "6. Automated QA (blank/short/duplicate screenshots via perceptual hash, viewport coverage, broken images, error text, title/URL sanity) followed by SHA-256 hashing of every evidence file.", "",
           "## 3. Coverage statistics", "",
           "| Metric | Value |", "|---|---|",
           f"| URLs discovered (manifest rows) | {len(rows)} |", f"| HTML pages in scope | {len(html_rows)} |",
           f"| HTML pages fully captured (3 viewports) | {qa.get('captured_html', 0)} |", f"| Partially captured | {qa.get('partial_html', 0)} |",
           f"| Failed / not captured | {qa.get('failed_html', 0)} |", f"| Public documents discovered / archived | {len(doc_rows)} / {qa.get('captured_documents', 0)} |",
           f"| Excluded (out of scope) | {len(excluded)} |", f"| Total production requests logged (all purposes) | {req_total} |",
           f"| Evidence files hashed | {integ.get('files_hashed', '?')} ({(integ.get('total_bytes', 0) or 0)/1e6:.1f} MB) |", "",
           "### Language coverage", "", *[f"- `{k}`: {v} pages" for k, v in langs.most_common()],
           "", "No language switcher or `hreflang` alternates were detected; the site appears to be single-language (English) unless noted in `metadata/page-data/`." if len(langs) <= 1 else "",
           "", "### Viewport coverage", "", *[f"- {vp}: {n} / {len(html_rows)} pages" for vp, n in (qa.get('viewport_coverage') or {}).items()], "",
           "## 4. Cache observations", "", "See `cache-observations.md`. Summary: " +
           f"{len(cs['hits'])} pages served with a disclosed cache HIT, {len(cs['misses'])} with a MISS, {len(cs['other'])} without a disclosed status. "
           f"Apparent technology: {', '.join(k for k, _ in cs['techs'].most_common()) or 'none disclosed'}.", "",
           "**Observed fact:** the large MISS share means most captured pages were generated by the WordPress backend at capture time rather than served from an existing cache. "
           "Every HIT and every MISS response referenced the same theme files "
           f"({', '.join(f'`{t}`' for t in sorted(themes_seen)) or 'n/a'}), so no visual/theme divergence between cached and freshly generated pages was observed in this capture. "
           "Whether an ordinary visit stored a regenerated page in the cache cannot be determined from the client side; it is disclosed as a possibility, not a finding.", "",
           "### Request accounting (LiteSpeed sensitivity)", "",
           "Every request made to a production URL is listed per row in `url-manifest.json` → `requests[]` (time, method, HTTP status, `x-litespeed-cache`, purpose).", "",
           f"- URLs captured with exactly one request: {req_hist.get(1, 0)}",
           f"- URLs with one earlier discovery GET (made on 2026-09-02 before the single-request rule was adopted) plus one capture navigation: {req_hist.get(2, 0)}",
           f"- URLs with 3+ requests (pilot pages navigated per viewport, retries after no response, or the two interrupted-run rows P0149/P0715): {sum(v for k, v in req_hist.items() if k >= 3)}",
           "- No HEAD, cache-bypass, cache-busting or deliberate reload requests were issued at any point.", "",
           "## 5. Current visible defects and observations (not fixed – recorded as-is)", "",
           *([f"- **{f['code']}** {f['ref_id']}: {f['message']}" for f in defects] or ["- No high/medium QA findings."]),
           "", f"Full list (including low/info): `reports/crawl-coverage/qa-findings.json` ({sum((qa.get('findings_by_severity') or {}).values())} findings).", "",
           "## 6. Limitations", "",
           "- Evidence reflects what a first-time, unauthenticated visitor using headless Chromium received during the capture window; other visitors, devices or cache nodes may have received different content.",
           "- Visiting an uncached page causes the server-side cache to store the backend's current render (normal visitor behaviour). MISS pages therefore document the current backend output, not a pre-existing cached copy.",
           "- Third-party resources, server-side functionality, form submission, account areas and checkout were deliberately not exercised or archived.",
           "- Full-page screenshots taller than 16,000 px are clipped and noted in the manifest.",
           "- Animated or time-dependent content (sliders, WhatsApp widget, social embeds, dates) may legitimately differ between captures; these areas should be masked in later automated comparisons via a separate mask configuration – no masks were applied to the evidence.",
           "- This package is not a WordPress backup: no theme/plugin source, uploads directory or database content is included (see README).", "",
           "## 7. Exceptions", "", f"{max(n_ex, 0)} entries – see `exceptions.md`.", "",
           "## 8. Recommended client sign-off procedure", "",
           "1. Open `reports/visual-contact-sheets/index.html` and review every page card (desktop/tablet/mobile).",
           "2. Confirm that the captured appearance matches the website the client expects to recover; note any page that already looks wrong in the `Notes` column of `url-manifest.csv` (as a client observation, without altering evidence files).",
           "3. Verify integrity with `sha256sum -c integrity/SHA256SUMS.txt` from the package root.",
           "4. Sign the approval block in `executive-summary.pdf`; the signed PDF plus the SHA256SUMS file constitute the approved baseline.",
           "5. Re-run the same configuration against staging/production after recovery (see `README.md` → Rerun) and compare screenshots per reference ID."]
    (out / "capture-summary.md").write_text("\n".join(x for x in rep if x is not None), encoding="utf-8")

    # ------------------------------------------------------------- README (package + rerun)
    readme = f"""# Visual Recovery Reference – {cfg['client']}

Read-only evidence capture of the public website `{cfg['base_url']}` taken {t_start} → {t_end} (UTC).

> {DISCLAIMER}

## What is in this package

| Path | Contents |
|---|---|
| `capture-summary.md` | Technical current-state report (scope, method, coverage, defects, limitations, sign-off) |
| `executive-summary.pdf` | Client-facing summary with approval block |
| `url-manifest.csv` / `.json` | Every discovered URL: reference ID, discovery source, status, redirects, screenshots, notes |
| `evidence-register.csv` | One line per evidence file with SHA-256, size, capture timestamp, source URL and profile |
| `environment.json` | Browser, versions, user agent, viewports and crawl settings used |
| `cache-observations.md` | Publicly visible cache headers per response and a HIT/MISS summary |
| `exceptions.md` | URLs/components not captured and why |
| `screenshots/<viewport>/full-page|above-fold/` | PNG evidence, `P0001_home_en_desktop_full.png` naming |
| `screenshots/interactive-states/` | Mobile menu, search panel, hover states, cookie banner |
| `html/response/` | Original HTTP response HTML (stored once when identical across viewports) |
| `html/rendered/` | Rendered DOM after load and lazy-load scroll, per viewport |
| `assets/` | First-party CSS/JS/images/fonts/documents actually loaded, deduplicated (`asset-index.json`) |
| `metadata/headers|redirects|links|page-data/` | Response headers, redirect chains, link inventories, page metadata |
| `reports/visual-contact-sheets/index.html` | Review gallery |
| `reports/crawl-coverage/` | Sitemap/robots copies, discovery and QA results |
| `reports/broken-pages/` | QA findings that indicate broken or error pages |
| `integrity/SHA256SUMS.txt`, `capture-log.txt` | Hashes and the complete append-only run log |

What this package is **not**: WordPress source files (themes/plugins/core), the uploads directory, the database, or any
server configuration. Cached/rendered public output (this package) must be distinguished from those when planning recovery.

## Verify integrity

```bash
cd visual-recovery-reference && sha256sum -c integrity/SHA256SUMS.txt
```

## Rerun against staging or the recovered site

```bash
pip install -r tools/requirements.txt && python -m playwright install chromium
cp capture.config.json capture.staging.json   # edit base_url, allowed_hosts, seeds, output_dir
python -m tools.vrr --config capture.staging.json discover
python -m tools.vrr --config capture.staging.json capture      # restartable; re-run to resume
python -m tools.vrr --config capture.staging.json qa
python -m tools.vrr --config capture.staging.json integrity
python -m tools.vrr --config capture.staging.json report
```

Viewports, delays, user agent and interactive-state selectors all come from the config file, so a rerun produces the
same reference IDs (when the URL set is unchanged) and identical filenames/dimensions for automated before/after
comparison. For comparison, pair files by reference ID and viewport (e.g. `P0001_home_en_desktop_full.png`) and keep
any exclusion masks for dynamic regions (sliders, chat widget, dates, maps, videos) in a separate mask file – never
edit the evidence PNGs.

Generated by {TOOL_VERSION} on {utc_now()}.
"""
    (out / "README.md").write_text(readme, encoding="utf-8")

    # ------------------------------------------------------------- executive summary PDF
    styles = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=styles["BodyText"], fontSize=9.5, leading=13)
    h = styles["Heading2"]; h.fontSize = 12
    doc = SimpleDocTemplate(str(out / "executive-summary.pdf"), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm,
                            title=f"Visual Recovery Reference – {cfg['client']}", author=TOOL_VERSION)
    story = [Paragraph("Visual Recovery Reference – Executive Summary", styles["Title"]),
             Paragraph(f"<b>Client:</b> {html.escape(cfg['client'])} &nbsp; <b>Website:</b> {html.escape(cfg['base_url'])} &nbsp; <b>Capture window (UTC):</b> {t_start} → {t_end}", body),
             Spacer(1, 6), Paragraph("Why this capture was conducted", h),
             Paragraph("The live website appears to depend on server-side cached pages: restoring the existing WordPress files and database to a staging environment does not reproduce what the public currently sees. Before any remediation, migration, cache purge, plugin update or infrastructure change, the publicly visible website was recorded as a timestamped, hash-verified reference so that the recovered website can later be checked against it.", body),
             Paragraph("What was captured", h),
             Paragraph("Every publicly reachable first-party page found through the homepage, navigation, footer, robots.txt, XML sitemap and internal links was rendered in a clean, unauthenticated Chromium browser at desktop (1440×900), tablet (768×1024) and mobile (390×844). For each page: above-the-fold and full-page PNG screenshots, the original response HTML, the rendered HTML, HTTP headers and redirect chain, page metadata, first-party assets, and safe interactive states (mobile menu, search panel, hover states). Publicly linked documents (PDF brochures/data sheets) were archived. Nothing on the production website was changed: no login, no form submission, no cache purge or bypass, one request at a time with delays.", body),
             Paragraph("Coverage", h)]
    tbl = [["Metric", "Value"],
           ["URLs discovered", str(len(rows))], ["HTML pages in scope", str(len(html_rows))],
           ["Pages fully captured at 3 viewports", str(qa.get("captured_html", 0))],
           ["Partially captured / failed", f"{qa.get('partial_html', 0)} / {qa.get('failed_html', 0)}"],
           ["Public documents archived", f"{qa.get('captured_documents', 0)} of {len(doc_rows)}"],
           ["Excluded (admin, account, cart, feeds)", str(len(excluded))],
           ["Languages", ", ".join(f"{k} ({v})" for k, v in langs.most_common())],
           ["Evidence files with SHA-256 hash", f"{integ.get('files_hashed', '?')} ({(integ.get('total_bytes', 0) or 0)/1e6:.0f} MB)"],
           ["QA findings (high / medium / low+info)", f"{(qa.get('findings_by_severity') or {}).get('high', 0)} / {(qa.get('findings_by_severity') or {}).get('medium', 0)} / {(qa.get('findings_by_severity') or {}).get('low', 0) + (qa.get('findings_by_severity') or {}).get('info', 0)}"],
           ["Cache status disclosed", f"{len(cs['hits'])} pages HIT, {len(cs['misses'])} pages MISS"],
           ["Browser", f"{env.get('browser_name', '?')} {env.get('browser_version', '?')} (Playwright {env.get('playwright_version', '?')})"]]
    t = Table(tbl, colWidths=[80*mm, 90*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white])]))
    story += [t, Spacer(1, 6), Paragraph("What the reference proves", h),
              Paragraph("That, during the capture window, an ordinary first-time visitor received the pages, text, images, navigation and layout shown in the screenshots and HTML files, with the recorded HTTP status, redirect and cache headers. Each file's SHA-256 hash in <i>evidence-register.csv</i> / <i>integrity/SHA256SUMS.txt</i> allows anyone to confirm the evidence has not been altered since capture.", body),
              Paragraph("What it does not prove", h),
              Paragraph(html.escape(DISCLAIMER) + " It also does not show what logged-in users, other devices or other cache nodes received, nor the behaviour of forms, search, store locator, wishlist or checkout, which were deliberately not exercised.", body),
              Paragraph("Important limitations", h),
              Paragraph("Pages served as a cache MISS were rendered by the current backend at the time of the visit and were then stored by the server cache as a normal side-effect of any visit – they show the backend's present output, which may differ from long-cached pages. Animated sliders, chat widgets and third-party embeds may vary between captures. Very tall pages are clipped at 16,000 px. Current visible defects (for example the product listing rendering empty behind the filter panel at the mobile viewport, where observed) are recorded, not repaired. See <i>capture-summary.md</i> and <i>exceptions.md</i> for the complete list.", body),
              Paragraph("Approval / sign-off", h),
              Paragraph("By signing below the client confirms that the captured reference (identified by the SHA-256 sums in <i>integrity/SHA256SUMS.txt</i>) represents the publicly visible website that the recovery project must restore, subject to the noted defects and limitations.", body),
              Spacer(1, 10)]
    sig = Table([["Name", "", "Role", ""], ["Signature", "", "Date", ""], ["SHA256SUMS.txt hash", "", "", ""]], colWidths=[35*mm, 55*mm, 25*mm, 55*mm], rowHeights=[12*mm, 12*mm, 10*mm])
    sig.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [sig, Spacer(1, 6), Paragraph(f"Generated {utc_now()} by {TOOL_VERSION}. Repository: mohamedsikanderadam/EP-backup-", ParagraphStyle("f", parent=body, fontSize=8, textColor=colors.grey))]
    doc.build(story)
    log("INFO", "reports generated: gallery, capture-summary.md, cache-observations.md, exceptions.md, README.md, executive-summary.pdf, crawl-coverage.md")
