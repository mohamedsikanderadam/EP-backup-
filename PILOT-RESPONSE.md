# Emirates Paints – Visual Recovery Reference: Phase 1 response and pilot

Date: 2026-09-02 (UTC) · Production: https://emiratespaints.com/ · Status: **pilot complete, awaiting approval for full crawl**

## 1. Understanding

The public site is served by LiteSpeed Cache on Hostinger (`x-litespeed-cache: hit`, PHP 7.4.33, WordPress + Yobazar child theme, Elementor Pro, WooCommerce, Revolution Slider, Essential Grid, Agile Store Locator, Ultimate Member, CF7, dFlip, Elfsight). What visitors see is largely cached rendered output which the restored files/database do not reproduce. The task is to freeze that public state as hash-verified evidence – screenshots, HTML, headers, metadata, assets – without changing anything on production. No repair, migration, cache action or login is performed.

## 2. Capture architecture

Repo `EP-backup-` → `tools/vrr` (Python 3.12 + Playwright/Chromium 151), config in `capture.config.json`, output in `visual-recovery-reference/`.

Pipeline: `discover` (passive URL discovery, urllib, redirects recorded) → `capture` (fresh unauthenticated Chromium context per page × viewport: above-fold PNG, stepwise lazy-load scroll, full-page PNG, original response HTML, rendered DOM, headers, redirect chain, metadata, links, forms, iframes, broken images, first-party assets, safe interactive states) → `qa` (blank/short/duplicate detection via perceptual hash, viewport coverage, error text, layout collapse, safety assertions) → `integrity` (SHA-256 for every file, `evidence-register.csv`, `SHA256SUMS.txt`) → `report` (HTML gallery, current-state report, cache observations, exceptions, README, executive-summary PDF with the required disclaimer).

Stable IDs `P0001…`; deterministic filenames `P0001_home_en_desktop_full.png`.

## 3. Production-safety controls (implemented, enforced in code)

- Concurrency 1, 2.5 s delay between requests, 2 retries with 15 s backoff, hard stop on HTTP 429 or 3 consecutive 5xx.
- Ordinary Chrome user agent; no cache-busting parameters, no `Cache-Control`/`Pragma` bypass headers, no CDN/proxy bypass.
- Same-domain only (`emiratespaints.com`, `www.`); third-party links inventoried, never followed.
- Excluded from capture (recorded in manifest as excluded): `/wp-admin`, `/wp-login.php`, `/wp-json`, `/xmlrpc.php`, `/my-account`, cart/checkout/order/pay, `?add-to-cart`, `?wc-ajax`, feeds, `?s=` search results, logout/nonce/state-changing links.
- No login, no form submission, no add-to-cart, no account creation. Cookie banner is captured before any dismissal.
- Evidence is append-only; integrity run records changed files rather than overwriting silently.

Unavoidable side effect (disclosed): a normal GET of an uncached page causes LiteSpeed to populate its cache for that URL – identical to any visitor. Observed on P0003 (miss → hit).

## 4. Required access / inputs

None beyond public HTTP. **Blocking item:** the GitHub repo `mohamedsikanderadam/EP-backup-` is not accessible to Devin (403 on push; not in the accessible repo list). Please create it (or grant access to the Devin GitHub app) so the package can be pushed and a PR opened. Optional: a client URL list and any previously known URLs to seed discovery.

## 5. Expected outputs

`visual-recovery-reference/`: `url-manifest.csv|json`, `screenshots/{desktop,tablet,mobile}/{above-the-fold,full-page}/`, `screenshots/interactive-states/`, `html/{response,rendered}/`, `metadata/{headers,redirects,pages,links}/`, `assets/`, `reports/visual-contact-sheets/index.html`, `reports/crawl-coverage/*`, `reports/broken-pages/*`, `cache-observations.md`, `exceptions.md`, `capture-summary.md`, `evidence-register.csv`, `integrity/SHA256SUMS.txt`, `executive-summary.pdf`, `environment.json`, `logs/capture.log`, `README.md` (rerun instructions).

## 6. Pilot plan and results

Pilot pages: homepage (P0001), `/products/` (P0002), `/product/aqua-emulsion/` (P0003), all three viewports.

| Page | HTTP | Cache | Desktop h | Tablet h | Mobile h |
|---|---|---|---|---|---|
| P0001 home | 200 | hit | 4494 | 4828 | 5109 |
| P0002 products | 200 | hit | 2480 | 3016 | **878** |
| P0003 aqua-emulsion | 200 | miss→hit | 2665 | 2819 | 3775 |

Interactive states captured: mobile menu open, desktop search panel open. 12 HTTP requests total (3 discovery + 9 renders); discovery also listed 88 URLs with 126 more queued.

Pilot findings that changed the tool:
1. Elementor entrance animations left sections at zero opacity in the first full-page screenshot → capture now waits for `.elementor-invisible` gates to clear and freezes CSS animations at end state (client-side only). Re-verified: homepage renders completely.
2. Theme hamburger exists twice in the DOM (one hidden) → selector logic picks the first *visible* control.

**Observed current-state defect (recorded, not fixed):** `/products/` at mobile 390 px renders only the filter sidebar over the footer; the product grid is absent (page 878 px vs 2480 px desktop). Flagged as `LAYOUT_COLLAPSE`. Screenshot: `screenshots/mobile/full-page/P0002_products_en_mobile_full.png`.

## 7. Estimated request volume (full crawl)

Discovery so far: 88 URLs seen, ~215 in queue; expect ~150–300 HTML pages after de-duplication (WooCommerce categories, product pages, attribute filters excluded). Per page: 1 discovery GET + 3 renders (each render loads ~40–90 first-party assets, mostly cache-hit static files). Estimate: **~600–1,200 HTML document requests, ~25–50k asset requests, over roughly 4–7 hours at the current 2.5 s pacing**, single-threaded. Storage estimate 1–3 GB (assets dominate; can be capped in config).

## 8. Risks and limitations

- Cache population side effect (above). Not a purge; cannot be avoided by any real browser visit.
- Headless capture cannot reproduce hover-only/scroll-parallax/video frames exactly; interactive coverage limited to safe click states.
- Pages > 20,000 px are clipped (noted in manifest).
- Site may serve device-specific or geo-specific cached variants (LiteSpeed mobile cache) that differ from what other visitors receive.
- WooCommerce filter/pagination combinations are unbounded; pagination followed, attribute-filter query URLs treated as functional and capped by `max_requests`.
- Third-party embeds (Elfsight WhatsApp, YouTube, maps) recorded as iframes/links only.
- Evidence of public appearance only – not a WordPress/database backup (disclaimer included in all reports).

## 9. Assumptions requiring confirmation

1. Client name is **Emirates Paints** (brief says "Emirates Spain" once).
2. Scope = `emiratespaints.com` + `www.` only; no other subdomains.
3. 2.5 s delay / single thread is acceptable to the host; no IP allow-listing needed.
4. Full crawl may include all WooCommerce product and category pages and paginated listings, and may archive linked PDFs (technical data sheets).
5. Evidence (~1–3 GB incl. assets) may be committed to the Git repo, or assets should be stored elsewhere and referenced by hash.
6. Repo `EP-backup-` to be created/shared so the package can be pushed.

**Awaiting: approval to run the full production crawl, and repo access.**

---

## Addendum – full crawl outcome (2026-09-02/03, LiteSpeed single-request model)

The request-volume estimate above assumed three navigations per page. After the LiteSpeed guidance the tool was changed to **one browser navigation per URL** (tablet/mobile by in-page resize). Actual figures:

| Metric | Value |
|---|---:|
| Manifest rows | 1,286 |
| HTML pages captured (3 viewports) | 609 (31 of them HTTP 404 pages, preserved) |
| Public documents archived | 46 |
| Excluded (admin/state-changing/feeds + combinatorial faceted-filter URLs) | 567 |
| Total production requests, all purposes | 741 |
| Pages with `x-litespeed-cache: hit` / `miss` / none | 45 / 535 / 75 |
| Wall time | ~9 h at concurrency 1 |
| Evidence size | 2.1 GB, 10,983 hashed files |

Key observations: most pages were served as MISS (regenerated at request time), yet HIT and MISS responses reference the same `yobazar` / `yobazar-child` theme; `/brochures/` returns HTTP 200 with an empty body; `/products/` filter views collapse to the filter sidebar only on mobile. All per-URL request histories are in `url-manifest.json` → `requests[]`.
