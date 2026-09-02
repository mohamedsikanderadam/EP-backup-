# Current-state report – Visual Recovery Reference

**Client:** Emirates Paints  
**Production website:** https://emiratespaints.com/  
**Capture window (UTC):** 2026-09-02T14:22:16Z → 2026-09-02T14:25:37Z  
**Report generated (UTC):** 2026-09-02T14:26:08Z  
**Tool:** vrr 1.0.0, Playwright 1.62.0, chromium 151.0.7922.34, Linux 5.15.200 (x86_64)

> This Visual Recovery Reference records the publicly visible state of the website during the stated capture period. It is intended to support visual and public-functionality comparison following recovery. It does not constitute a complete WordPress source-code, database or application backup, and it does not independently prove that the underlying website was secure or fully functional at the time of capture.

## 1. Scope

All publicly accessible first-party HTML pages and linked public documents on `emiratespaints.com, www.emiratespaints.com` discovered passively from the homepage, navigation, footer, `robots.txt`, XML sitemap(s) and internal links. Administrative, authenticated, cart/checkout, feed and state-changing URLs were recorded in the manifest but excluded from capture (see `exceptions.md`).

## 2. Methodology

1. Passive discovery with single-threaded, delayed HTTP GET requests using an ordinary browser user agent (no cache-busting parameters or headers).
2. Each HTML page rendered in a fresh, unauthenticated headless Chromium context at three viewports (desktop 1440×900, tablet 768×1024, mobile 390×844, DPR 1).
3. Per page and viewport: above-the-fold PNG, stepwise scroll for lazy-loaded media, return to top, full-page PNG, original response HTML, rendered DOM HTML, response headers, redirect chain, page metadata (title, description, canonical, Open Graph, JSON-LD, links, forms, iframes), first-party assets (deduplicated).
4. Safe interactive states captured where present: mobile menu, search panel, navigation hover, cookie banner (initial state first).
5. Rate limiting: concurrency 1, 2.5s delay, 2 retries with backoff, hard stop on HTTP 429 or 3 consecutive 5xx.
6. Automated QA (blank/short/duplicate screenshots via perceptual hash, viewport coverage, broken images, error text, title/URL sanity) followed by SHA-256 hashing of every evidence file.

## 3. Coverage statistics

| Metric | Value |
|---|---|
| URLs discovered (manifest rows) | 88 |
| HTML pages in scope | 86 |
| HTML pages fully captured (3 viewports) | 3 |
| Partially captured | 0 |
| Failed / not captured | 83 |
| Public documents discovered / archived | 0 / 0 |
| Excluded (out of scope) | 1 |
| Discovery HTTP requests | 3 |
| Evidence files hashed | 348 (25.5 MB) |

### Language coverage

- `und`: 83 pages
- `en-US`: 3 pages



### Viewport coverage

- desktop: 3 / 86 pages
- tablet: 3 / 86 pages
- mobile: 3 / 86 pages

## 4. Cache observations

See `cache-observations.md`. Summary: 3 pages served with a disclosed cache HIT, 0 with a MISS, 0 without a disclosed status. Apparent technology: LiteSpeed Cache (x-litespeed-*).

## 5. Current visible defects and observations (not fixed – recorded as-is)

- **LAYOUT_COLLAPSE** P0002: mobile page height 878px is far shorter than desktop 2480px - content may be missing at the mobile viewport
- **MISSING_VIEWPORT** P0004: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0004: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0004: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0005: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0005: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0005: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0006: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0006: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0006: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0007: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0007: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0007: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0008: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0008: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0008: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0009: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0009: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0009: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0010: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0010: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0010: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0011: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0011: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0011: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0012: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0012: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0012: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0013: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0013: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0013: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0015: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0015: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0015: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0016: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0016: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0016: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0017: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0017: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0017: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0018: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0018: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0018: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0019: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0019: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0019: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0020: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0020: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0020: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0021: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0021: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0021: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0022: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0022: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0022: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0023: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0023: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0023: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0024: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0024: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0024: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0025: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0025: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0025: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0026: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0026: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0026: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0027: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0027: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0027: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0028: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0028: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0028: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0029: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0029: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0029: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0030: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0030: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0030: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0031: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0031: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0031: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0032: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0032: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0032: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0033: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0033: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0033: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0034: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0034: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0034: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0035: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0035: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0035: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0036: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0036: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0036: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0037: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0037: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0037: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0038: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0038: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0038: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0039: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0039: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0039: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0040: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0040: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0040: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0041: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0041: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0041: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0042: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0042: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0042: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0043: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0043: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0043: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0044: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0044: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0044: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0045: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0045: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0045: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0046: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0046: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0046: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0047: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0047: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0047: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0048: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0048: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0048: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0049: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0049: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0049: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0050: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0050: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0050: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0051: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0051: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0051: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0052: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0052: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0052: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0053: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0053: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0053: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0054: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0054: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0054: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0055: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0055: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0055: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0056: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0056: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0056: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0057: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0057: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0057: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0058: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0058: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0058: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0059: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0059: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0059: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0060: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0060: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0060: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0061: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0061: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0061: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0062: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0062: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0062: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0063: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0063: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0063: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0064: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0064: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0064: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0065: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0065: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0065: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0066: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0066: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0066: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0067: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0067: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0067: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0068: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0068: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0068: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0069: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0069: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0069: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0070: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0070: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0070: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0071: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0071: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0071: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0072: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0072: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0072: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0073: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0073: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0073: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0074: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0074: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0074: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0075: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0075: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0075: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0076: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0076: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0076: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0077: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0077: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0077: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0078: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0078: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0078: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0079: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0079: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0079: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0080: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0080: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0080: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0081: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0081: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0081: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0082: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0082: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0082: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0084: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0084: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0084: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0085: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0085: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0085: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0086: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0086: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0086: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0087: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0087: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0087: no successful mobile capture (status=none)
- **MISSING_VIEWPORT** P0088: no successful desktop capture (status=none)
- **MISSING_VIEWPORT** P0088: no successful tablet capture (status=none)
- **MISSING_VIEWPORT** P0088: no successful mobile capture (status=none)

Full list (including low/info): `reports/crawl-coverage/qa-findings.json` (251 findings).

## 6. Limitations

- Evidence reflects what a first-time, unauthenticated visitor using headless Chromium received during the capture window; other visitors, devices or cache nodes may have received different content.
- Visiting an uncached page causes the server-side cache to store the backend's current render (normal visitor behaviour). MISS pages therefore document the current backend output, not a pre-existing cached copy.
- Third-party resources, server-side functionality, form submission, account areas and checkout were deliberately not exercised or archived.
- Full-page screenshots taller than 16,000 px are clipped and noted in the manifest.
- Animated or time-dependent content (sliders, WhatsApp widget, social embeds, dates) may legitimately differ between captures; these areas should be masked in later automated comparisons via a separate mask configuration – no masks were applied to the evidence.
- This package is not a WordPress backup: no theme/plugin source, uploads directory or database content is included (see README).

## 7. Exceptions

86 entries – see `exceptions.md`.

## 8. Recommended client sign-off procedure

1. Open `reports/visual-contact-sheets/index.html` and review every page card (desktop/tablet/mobile).
2. Confirm that the captured appearance matches the website the client expects to recover; note any page that already looks wrong in the `Notes` column of `url-manifest.csv` (as a client observation, without altering evidence files).
3. Verify integrity with `sha256sum -c integrity/SHA256SUMS.txt` from the package root.
4. Sign the approval block in `executive-summary.pdf`; the signed PDF plus the SHA256SUMS file constitute the approved baseline.
5. Re-run the same configuration against staging/production after recovery (see `README.md` → Rerun) and compare screenshots per reference ID.