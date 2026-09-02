"""Playwright-based read-only page capture (screenshots, HTML, headers, assets, metadata)."""
from __future__ import annotations

import hashlib
import json
import mimetypes
import platform
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import Error as PWError, Page, TimeoutError as PWTimeout, sync_playwright

from .common import (Log, TOOL_VERSION, ensure_dirs, is_allowed, load_manifest, normalize_url,
                     polite_sleep, save_manifest, short_hash, utc_now, write_json)

CACHE_HEADERS = ["x-litespeed-cache", "x-litespeed-cache-control", "x-litespeed-tag", "x-lsadc-cache",
                 "x-qc-cache", "x-qc-pop", "cf-cache-status", "cf-ray", "x-cache", "x-cache-status",
                 "age", "cache-control", "expires", "etag", "last-modified", "via", "server",
                 "platform", "x-powered-by", "vary", "x-turbo-charged-by", "x-proxy-cache"]

MAX_SHOT_HEIGHT = 16000  # Chromium's practical full-page capture ceiling


class Evidence:
    """Append-only evidence ledger; hashing happens later in the integrity step."""

    def __init__(self, cfg: dict):
        self.path = ensure_dirs(cfg)["state"] / "evidence.jsonl"

    def add(self, ref_id: str, path: Path, url: str, profile: str, kind: str, cfg: dict) -> None:
        rel = str(path.relative_to(cfg["_out"]))
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ref_id": ref_id, "relative_path": rel, "source_url": url,
                                 "capture_profile": profile, "kind": kind,
                                 "captured_at": utc_now(), "tool": TOOL_VERSION}) + "\n")


def asset_bucket(ct: str, url: str) -> str:
    p = urlsplit(url).path.lower()
    if ct.startswith("image/") or p.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".avif")):
        return "images"
    if "css" in ct or p.endswith(".css"):
        return "styles"
    if "javascript" in ct or p.endswith((".js", ".mjs")):
        return "scripts"
    if "font" in ct or p.endswith((".woff", ".woff2", ".ttf", ".otf", ".eot")):
        return "fonts"
    if "pdf" in ct or p.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")):
        return "documents"
    return "other"


def asset_filename(url: str, ct: str) -> str:
    p = unquote(urlsplit(url).path)
    name = Path(p).name or "index"
    if "." not in name:
        ext = mimetypes.guess_extension(ct.split(";")[0].strip()) or ""
        name += ext
    name = re.sub(r"[^\w.\-]+", "_", name)[:120]
    return f"{short_hash(url)}_{name}"


def scroll_through(page: Page, step: int, pause_ms: int, max_steps: int = 400) -> int:
    """Scroll to the bottom in steps so lazy-loaded media renders, then return to the top."""
    height = page.evaluate("() => document.documentElement.scrollHeight")
    pos, steps = 0, 0
    while pos < height and steps < max_steps:
        pos += step
        page.evaluate(f"() => window.scrollTo(0, {pos})")
        page.wait_for_timeout(pause_ms)
        height = page.evaluate("() => document.documentElement.scrollHeight")
        steps += 1
    # entrance-animation gates (Elementor, WOW.js, AOS) hide content until scrolled into view;
    # give them time to release before returning to the top
    for _ in range(12):
        pending = page.evaluate(
            "() => document.querySelectorAll('.elementor-invisible, .wow:not(.animated), [data-aos]:not(.aos-animate)').length")
        if not pending:
            break
        page.wait_for_timeout(500)
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(pause_ms * 2)
    return height


PAGE_DATA_JS = """
() => {
  const q = (s) => Array.from(document.querySelectorAll(s));
  const meta = (n) => (document.querySelector(`meta[name="${n}"]`) || document.querySelector(`meta[property="${n}"]`) || {}).content || null;
  const og = {};
  q('meta[property^="og:"]').forEach(m => { og[m.getAttribute('property')] = m.content; });
  const ld = q('script[type="application/ld+json"]').map(s => { try { return JSON.parse(s.textContent); } catch (e) { return {"_unparsed": s.textContent.slice(0, 2000)}; } });
  const imgs = q('img');
  const broken = imgs.filter(i => i.complete && i.naturalWidth === 0 && i.getAttribute('src')).map(i => i.currentSrc || i.src).slice(0, 200);
  const links = q('a[href]').map(a => a.href);
  const host = location.hostname.replace(/^www\\./, '');
  const internal = links.filter(h => { try { return new URL(h).hostname.replace(/^www\\./, '') === host; } catch (e) { return false; } });
  const external = links.filter(h => { try { const u = new URL(h); return u.protocol.startsWith('http') && u.hostname.replace(/^www\\./, '') !== host; } catch (e) { return false; } });
  return {
    title: document.title, lang: document.documentElement.lang || null,
    canonical: (document.querySelector('link[rel="canonical"]') || {}).href || null,
    meta_description: meta('description'), robots: meta('robots'), generator: meta('generator'),
    open_graph: og, twitter_card: meta('twitter:card'), json_ld: ld,
    hreflang: q('link[rel="alternate"][hreflang]').map(l => ({hreflang: l.hreflang, href: l.href})),
    image_count: imgs.length, broken_images: broken,
    iframes: q('iframe').map(f => f.src).filter(Boolean).slice(0, 50),
    videos: q('video, video source').map(v => v.src || v.currentSrc).filter(Boolean).slice(0, 50),
    forms: q('form').map(f => ({action: f.action, method: f.method, fields: Array.from(f.elements).map(e => e.name || e.id || e.type).slice(0, 40)})).slice(0, 20),
    internal_links: Array.from(new Set(internal)), external_links: Array.from(new Set(external)),
    body_text_length: (document.body && document.body.innerText || '').length,
    body_text_excerpt: (document.body && document.body.innerText || '').replace(/\\s+/g, ' ').slice(0, 600),
    page_height: document.documentElement.scrollHeight, page_width: document.documentElement.scrollWidth,
    has_horizontal_overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
    visible_error_text: (document.body && /fatal error|warning:|notice:|there has been a critical error|database error/i.test(document.body.innerText)) || false,
    wp_theme: (q('link[href*="/wp-content/themes/"]').map(l => (l.href.match(/themes\\/([^\\/]+)/) || [])[1]).filter(Boolean)),
    wp_plugins: Array.from(new Set(q('link[href*="/wp-content/plugins/"], script[src*="/wp-content/plugins/"]').map(l => ((l.href || l.src).match(/plugins\\/([^\\/]+)/) || [])[1]).filter(Boolean))),
  };
}
"""


def first_visible(page: Page, selectors: list[str]):
    for sel in selectors:
        try:
            loc = page.locator(sel)
            for i in range(min(loc.count(), 6)):
                if loc.nth(i).is_visible(timeout=800):
                    return sel, loc.nth(i)
        except PWError:
            continue
    return None, None


def capture_page(pw_browser, row: dict, vp_name: str, vp: dict, cfg: dict, d: dict, log: Log,
                 ev: Evidence, asset_index: dict, save_assets: bool) -> dict:
    """Capture one manifest row at one viewport in a fresh, unauthenticated context."""
    crawl = cfg["crawl"]
    url = row["normalized_url"]
    ref, slug = row["ref_id"], row["slug"]
    lang = (row.get("language") or "und").split("-")[0].lower() or "und"
    base = f"{ref}_{slug}_{lang}_{vp_name}"
    result = {"viewport": vp_name, "started_at": utc_now(), "status": "pending", "files": [], "notes": []}

    ctx = pw_browser.new_context(viewport={"width": vp["width"], "height": vp["height"]},
                                 device_scale_factor=vp["device_scale_factor"],
                                 user_agent=cfg["user_agent"], locale="en-US",
                                 ignore_https_errors=False, java_script_enabled=True)
    page = ctx.new_page()
    page.set_default_timeout(crawl["page_timeout_ms"])
    main_resp = {}
    seen_responses: list[dict] = []

    def on_response(resp):
        try:
            rurl = resp.url
            if not is_allowed(rurl, cfg):
                seen_responses.append({"url": rurl, "status": resp.status, "first_party": False})
                return
            ct = (resp.headers.get("content-type") or "").split(";")[0].strip()
            rec = {"url": rurl, "status": resp.status, "content_type": ct, "first_party": True}
            seen_responses.append(rec)
            if not (save_assets and resp.ok and resp.request.resource_type != "document"):
                return
            n = normalize_url(rurl, cfg)
            if n in asset_index:
                return
            body = resp.body()
            if len(body) > cfg["asset_max_bytes"]:
                asset_index[n] = {"skipped": "too large", "bytes": len(body)}
                return
            bucket = asset_bucket(ct, rurl)
            fn = asset_filename(rurl, ct)
            dest = d[f"assets_{bucket}"] / fn
            dest.write_bytes(body)
            asset_index[n] = {"path": str(dest.relative_to(cfg["_out"])), "content_type": ct,
                              "bytes": len(body), "status": resp.status, "first_seen_on": ref,
                              "captured_at": utc_now()}
            ev.add(ref, dest, rurl, "asset", bucket, cfg)
        except PWError:
            pass
        except Exception as e:  # never let asset saving break a capture
            result["notes"].append(f"asset save error: {e!r}")

    page.on("response", on_response)

    try:
        try:
            resp = page.goto(url, wait_until="load")
        except PWTimeout:
            result["notes"].append("load event timeout; continuing with partially loaded page")
            resp = None
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PWTimeout:
            result["notes"].append("networkidle not reached within 15s (likely long-polling/analytics)")
        page.wait_for_timeout(crawl["settle_wait_ms"])

        if resp is not None:
            chain = []
            req = resp.request
            while req.redirected_from is not None:
                prev = req.redirected_from
                pr = prev.response()
                chain.insert(0, {"url": prev.url, "status": pr.status if pr else None,
                                 "location": (pr.headers.get("location") if pr else None)})
                req = prev
            main_resp = {"url": resp.url, "status": resp.status, "status_text": resp.status_text,
                         "headers": dict(resp.headers), "redirect_chain": chain,
                         "cache_headers": {k: v for k, v in resp.headers.items() if k.lower() in CACHE_HEADERS}}
            try:
                body = resp.body()
                body_sha = hashlib.sha256(body).hexdigest()
                main_resp["response_body_sha256"] = body_sha
                main_resp["response_body_bytes"] = len(body)
                # identical response bodies across viewports are stored once; the hash proves equality
                existing = row.get("_response_body_hashes", {})
                dup = next((v for v, h in existing.items() if h == body_sha), None)
                if dup:
                    main_resp["response_body_identical_to"] = dup
                    result["notes"].append(f"response HTML identical to {dup} capture (sha256 match); not stored twice")
                else:
                    p = d["html_response"] / f"{base}.html"
                    p.write_bytes(body)
                    ev.add(ref, p, url, vp_name, "html_response", cfg)
                    result["files"].append(str(p.relative_to(cfg["_out"])))
                existing[vp_name] = body_sha
                row["_response_body_hashes"] = existing
            except PWError as e:
                result["notes"].append(f"response body unavailable: {e}")
            write_json(d["headers"] / f"{base}.headers.json", {"ref_id": ref, "url": url, "viewport": vp_name,
                                                               "captured_at": utc_now(), **main_resp})
            if chain:
                write_json(d["redirects"] / f"{base}.redirects.json", {"ref_id": ref, "url": url, "chain": chain,
                                                                       "final_url": resp.url})
            if resp.status == 429:
                result["status"] = "halt-429"
            elif resp.status >= 500:
                result["notes"].append(f"server error {resp.status}")

        # Cookie banner: capture initial state first, then dismiss only if necessary
        cb = cfg.get("cookie_banner", {})
        sel, loc = first_visible(page, cb.get("dismiss_selectors", []))
        if sel:
            p = d["interactive"] / f"{base}_cookie_banner_initial.png"
            page.screenshot(path=str(p), full_page=False)
            ev.add(ref, p, url, vp_name, "interactive", cfg)
            result["files"].append(str(p.relative_to(cfg["_out"])))
            loc.click()
            page.wait_for_timeout(800)
            result["notes"].append(f"cookie banner dismissed via {sel}")
            log("MANUAL", f"{ref} {vp_name}: cookie banner dismissed via selector {sel}")

        # Above-the-fold (initial state)
        p_fold = d[f"shots_{vp_name}_fold"] / f"{base}_fold.png"
        page.screenshot(path=str(p_fold), full_page=False)
        ev.add(ref, p_fold, url, vp_name, "screenshot_fold", cfg)
        result["files"].append(str(p_fold.relative_to(cfg["_out"])))

        # Lazy-load pass, then full page
        height = scroll_through(page, crawl["scroll_step_px"], crawl["scroll_pause_ms"])
        page.wait_for_timeout(crawl["settle_wait_ms"] // 2)
        p_full = d[f"shots_{vp_name}_full"] / f"{base}_full.png"
        try:
            if height > MAX_SHOT_HEIGHT:
                page.screenshot(path=str(p_full), clip={"x": 0, "y": 0, "width": vp["width"], "height": MAX_SHOT_HEIGHT},
                                full_page=True, animations="disabled")
                result["notes"].append(f"page height {height}px exceeds {MAX_SHOT_HEIGHT}px; full-page capture clipped")
            else:
                page.screenshot(path=str(p_full), full_page=True, timeout=90000, animations="disabled")
        except PWError as e:
            result["notes"].append(f"full-page screenshot failed: {str(e)[:200]}")
            page.screenshot(path=str(p_full), full_page=False)
            result["notes"].append("fallback: viewport-only image saved as *_full.png")
        ev.add(ref, p_full, url, vp_name, "screenshot_full", cfg)
        result["files"].append(str(p_full.relative_to(cfg["_out"])))

        # Rendered DOM + page data
        rendered = page.content()
        p_r = d["html_rendered"] / f"{base}.html"
        p_r.write_text(rendered, encoding="utf-8")
        ev.add(ref, p_r, url, vp_name, "html_rendered", cfg)
        result["files"].append(str(p_r.relative_to(cfg["_out"])))
        data = page.evaluate(PAGE_DATA_JS)
        data.update({"ref_id": ref, "url": url, "final_url": page.url, "viewport": vp_name,
                     "viewport_size": vp, "captured_at": utc_now(),
                     "http_status": main_resp.get("status"), "cache_headers": main_resp.get("cache_headers"),
                     "first_party_responses": len([r for r in seen_responses if r["first_party"]]),
                     "third_party_hosts": sorted({urlsplit(r["url"]).hostname for r in seen_responses if not r["first_party"] and urlsplit(r["url"]).hostname}),
                     "failed_subresources": [r for r in seen_responses if r["first_party"] and r["status"] >= 400][:100]})
        write_json(d["page_data"] / f"{base}.json", data)
        result.update({"title": data["title"], "lang": data["lang"], "final_url": page.url,
                       "http_status": main_resp.get("status"), "page_height": height,
                       "broken_images": len(data["broken_images"]), "visible_error_text": data["visible_error_text"],
                       "horizontal_overflow": data["has_horizontal_overflow"]})

        # Interactive states (safe, non-submitting)
        for st in cfg.get("interactive_states", []):
            if st["viewport"] != vp_name:
                continue
            pages = st.get("pages", "all")
            if pages != "all" and ref not in pages:
                continue
            try:
                if "click_any" in st:
                    sel, loc = first_visible(page, st["click_any"])
                    if not sel:
                        continue
                    loc.click(timeout=5000)
                elif "hover_any" in st:
                    sel, loc = first_visible(page, st["hover_any"])
                    if not sel:
                        continue
                    loc.hover(timeout=5000)
                else:
                    continue
                page.wait_for_timeout(1000)
                p = d["interactive"] / f"{base}_{st['name']}.png"
                page.screenshot(path=str(p), full_page=False)
                ev.add(ref, p, url, vp_name, f"interactive:{st['name']}", cfg)
                result["files"].append(str(p.relative_to(cfg["_out"])))
                result["notes"].append(f"interactive state {st['name']} via {sel}")
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            except PWError as e:
                result["notes"].append(f"interactive state {st['name']} failed: {str(e)[:120]}")

        if result["status"] == "pending":
            result["status"] = "captured" if (main_resp.get("status") or 0) < 400 else f"captured-http-{main_resp.get('status')}"
    except PWError as e:
        result["status"] = "failed"
        result["notes"].append(f"playwright error: {str(e)[:300]}")
    finally:
        result["finished_at"] = utc_now()
        try:
            ctx.close()
        except PWError:
            pass
    return result


def download_document(row: dict, cfg: dict, d: dict, ev: Evidence, log: Log) -> dict:
    url = row["normalized_url"]
    req = urllib.request.Request(url, headers={"User-Agent": cfg["user_agent"]})
    res = {"started_at": utc_now(), "status": "pending", "files": [], "notes": []}
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            headers = {k.lower(): v for k, v in resp.getheaders()}
            body = resp.read(cfg["asset_max_bytes"] + 1)
        if len(body) > cfg["asset_max_bytes"]:
            res["status"] = "skipped-too-large"; res["notes"].append("document exceeds asset_max_bytes")
            return res
        fn = f"{row['ref_id']}_{asset_filename(url, headers.get('content-type', ''))}"
        dest = d["assets_documents"] / fn
        dest.write_bytes(body)
        ev.add(row["ref_id"], dest, url, "document", "document", cfg)
        write_json(d["headers"] / f"{row['ref_id']}_{row['slug']}.headers.json",
                   {"ref_id": row["ref_id"], "url": url, "status": resp.status, "headers": headers,
                    "cache_headers": {k: v for k, v in headers.items() if k in CACHE_HEADERS}, "captured_at": utc_now()})
        res.update({"status": "captured", "http_status": resp.status, "bytes": len(body),
                    "files": [str(dest.relative_to(cfg["_out"]))], "content_type": headers.get("content-type")})
    except urllib.error.HTTPError as e:
        res.update({"status": f"captured-http-{e.code}", "http_status": e.code})
        res["notes"].append(f"HTTP {e.code}")
    except Exception as e:
        res["status"] = "failed"; res["notes"].append(repr(e))
    res["finished_at"] = utc_now()
    return res


def environment_record(pw, browser, cfg: dict) -> dict:
    from importlib.metadata import version
    return {
        "recorded_at": utc_now(), "tool": TOOL_VERSION,
        "browser_name": browser.browser_type.name, "browser_version": browser.version,
        "playwright_version": version("playwright"), "python_version": platform.python_version(),
        "operating_environment": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "user_agent": cfg["user_agent"], "viewports": cfg["viewports"], "crawl_settings": cfg["crawl"],
        "headless": True, "cache_bypass_headers_sent": False, "cache_busting_query_params": False,
        "authenticated": False, "config_file": cfg["_config_path"],
    }


def run_capture(cfg: dict, refs: list[str] | None = None, viewports: list[str] | None = None,
                max_pages: int | None = None, force: bool = False) -> None:
    d = ensure_dirs(cfg)
    log = Log(cfg)
    ev = Evidence(cfg)
    crawl = cfg["crawl"]
    rows = load_manifest(cfg)
    if not rows:
        raise SystemExit("manifest is empty - run discovery first")
    vps = {k: v for k, v in cfg["viewports"].items() if not viewports or k in viewports}
    asset_idx_path = d["assets"] / "asset-index.json"
    asset_index = json.load(open(asset_idx_path)) if asset_idx_path.exists() else {}

    todo = [r for r in rows if r["capture_status"] not in ("excluded",) and (not refs or r["ref_id"] in refs)]
    if max_pages:
        todo = [r for r in todo if r.get("capture_status") in ("pending", "partial", "failed")][:max_pages]

    consecutive_5xx = 0
    requests_made = 0
    halted = False
    log("INFO", f"capture run start: {len(todo)} manifest rows, viewports={list(vps)}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        env = environment_record(pw, browser, cfg)
        write_json(cfg["_out"] / "environment.json", env)
        log("INFO", f"browser {env['browser_name']} {env['browser_version']} playwright {env['playwright_version']}")
        try:
            for row in todo:
                if halted:
                    break
                caps = row.setdefault("captures", {})
                if row["content_type"] == "document":
                    if caps.get("document", {}).get("status", "").startswith("captured"):
                        continue
                    caps["document"] = download_document(row, cfg, d, ev, log)
                    row["http_status"] = caps["document"].get("http_status", row.get("http_status"))
                    row["final_url"] = row["final_url"] or row["normalized_url"]
                    row["capture_status"] = caps["document"]["status"]
                    row["screenshots"] = []
                    requests_made += 1
                    log("INFO", f"document {row['ref_id']} {row['normalized_url']} -> {caps['document']['status']}")
                    save_manifest(cfg, rows)
                    polite_sleep(crawl["delay_seconds"])
                    continue
                if row["content_type"] not in ("html",):
                    row["capture_status"] = "excluded"
                    row["notes"] = (row.get("notes", "") + f" non-HTML content type {row['content_type']} - recorded only").strip()
                    save_manifest(cfg, rows)
                    continue
                for vp_name, vp in vps.items():
                    prev = caps.get(vp_name)
                    if prev and prev.get("status", "").startswith("captured") and not force:
                        continue
                    if requests_made >= crawl["max_requests"]:
                        log("STOP", "max_requests reached"); halted = True; break
                    attempt, res = 0, None
                    while attempt <= crawl["max_retries"]:
                        attempt += 1
                        res = capture_page(browser, row, vp_name, vp, cfg, d, log, ev, asset_index,
                                           save_assets=cfg.get("capture_assets", True))
                        requests_made += 1
                        res["attempt"] = attempt
                        status = res.get("http_status") or 0
                        if res["status"] == "halt-429":
                            log("STOP", f"HTTP 429 on {row['ref_id']} - halting capture"); halted = True; break
                        if status >= 500:
                            consecutive_5xx += 1
                            if consecutive_5xx >= crawl["stop_after_consecutive_5xx"]:
                                log("STOP", f"{consecutive_5xx} consecutive 5xx responses - halting"); halted = True; break
                        else:
                            consecutive_5xx = 0
                        if res["status"] == "failed" and attempt <= crawl["max_retries"]:
                            log("RETRY", f"{row['ref_id']} {vp_name} attempt {attempt} failed: {res['notes'][-1] if res['notes'] else ''}; backing off")
                            polite_sleep(crawl["retry_backoff_seconds"] * attempt)
                            continue
                        break
                    caps[vp_name] = res
                    log("INFO", f"{row['ref_id']} {vp_name} {row['normalized_url']} -> {res['status']} "
                                f"http={res.get('http_status')} h={res.get('page_height')} notes={len(res['notes'])}")
                    if halted:
                        break
                    polite_sleep(crawl["delay_seconds"])
                # roll up row status
                statuses = [caps.get(v, {}).get("status", "pending") for v in cfg["viewports"]]
                if all(s.startswith("captured") for s in statuses):
                    row["capture_status"] = "captured" if all(s == "captured" for s in statuses) else "captured-with-http-error"
                elif any(s.startswith("captured") for s in statuses):
                    row["capture_status"] = "partial"
                elif any(s == "failed" for s in statuses):
                    row["capture_status"] = "failed"
                first = next((caps[v] for v in cfg["viewports"] if caps.get(v, {}).get("title") is not None), None)
                if first:
                    row["page_title"] = first["title"] or row.get("page_title", "")
                    row["language"] = first.get("lang") or row.get("language") or "und"
                    row["final_url"] = first.get("final_url") or row.get("final_url")
                    row["http_status"] = first.get("http_status") or row.get("http_status")
                row["screenshots"] = sorted({f for v in cfg["viewports"] for f in caps.get(v, {}).get("files", []) if f.endswith(".png")})
                save_manifest(cfg, rows)
                write_json(asset_idx_path, asset_index)
        finally:
            browser.close()
            write_json(asset_idx_path, asset_index)
            save_manifest(cfg, rows)
    log("INFO", f"capture run end: requests={requests_made} halted={halted}")
