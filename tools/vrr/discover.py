"""Passive URL discovery: seeds, robots.txt, XML sitemaps and internal links.

Read-only: plain GET requests with an ordinary browser user agent, one at a time,
with a delay between requests. No cache-busting parameters or headers are ever sent.
"""
from __future__ import annotations

import gzip
import re
import urllib.error
import urllib.request
from collections import deque
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from .common import (Log, classify, ensure_dirs, is_allowed, is_excluded, load_manifest,
                     normalize_url, polite_sleep, save_manifest, slugify, utc_now, write_json)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def fetch(url: str, cfg: dict, max_hops: int = 8) -> dict:
    """GET `url`, following redirects manually so the chain is recorded."""
    opener = urllib.request.build_opener(NoRedirect)
    chain: list[dict] = []
    current = url
    for _ in range(max_hops):
        req = urllib.request.Request(current, headers={
            "User-Agent": cfg["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            resp = opener.open(req, timeout=45)
            status = resp.status
            headers = {k.lower(): v for k, v in resp.getheaders()}
            body = b""
            ct = headers.get("content-type", "")
            if any(t in ct for t in ("html", "xml", "text/plain")) or ct == "":
                body = resp.read(6_000_000)
                if headers.get("content-encoding") == "gzip":
                    body = gzip.decompress(body)
            resp.close()
        except urllib.error.HTTPError as e:
            status = e.code
            headers = {k.lower(): v for k, v in e.headers.items()}
            body = b""
            if 300 <= status < 400 and headers.get("location"):
                nxt = normalize_url(headers["location"], cfg, base=current)
                chain.append({"url": current, "status": status, "location": nxt})
                current = nxt
                polite_sleep(cfg["crawl"]["delay_seconds"])
                continue
            try:
                body = e.read(2_000_000)
            except Exception:
                pass
        except Exception as e:  # network failure
            return {"url": url, "final_url": current, "status": 0, "headers": {}, "body": b"",
                    "chain": chain, "error": repr(e)}
        return {"url": url, "final_url": current, "status": status, "headers": headers,
                "body": body, "chain": chain, "error": ""}
    return {"url": url, "final_url": current, "status": 0, "headers": {}, "body": b"",
            "chain": chain, "error": "too many redirects"}


def parse_sitemap(body: bytes) -> tuple[list[str], list[str]]:
    """Return (sitemap_urls, page_urls) from a sitemap or sitemap index."""
    soup = BeautifulSoup(body, "xml")
    sitemaps = [s.get_text(strip=True) for s in soup.select("sitemapindex > sitemap > loc")]
    pages = [s.get_text(strip=True) for s in soup.select("urlset > url > loc")]
    return sitemaps, pages


def extract_links(html: bytes, base: str, cfg: dict) -> dict:
    soup = BeautifulSoup(html, "lxml")
    internal, external, docs, anchors = [], [], [], []
    canonical = None
    lang = (soup.html.get("lang") if soup.html else None) or ""
    title = soup.title.get_text(strip=True) if soup.title else ""
    alternates = []
    for link in soup.find_all("link"):
        rel = [r.lower() for r in (link.get("rel") or [])]
        href = link.get("href")
        if not href:
            continue
        if "canonical" in rel:
            canonical = normalize_url(href, cfg, base)
        if "alternate" in rel and link.get("hreflang"):
            alternates.append({"hreflang": link["hreflang"], "url": normalize_url(href, cfg, base)})
        if ("next" in rel or "prev" in rel) and is_allowed(normalize_url(href, cfg, base), cfg):
            internal.append(normalize_url(href, cfg, base))
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "whatsapp:", "sms:", "#")):
            if href.startswith("#") and len(href) > 1:
                anchors.append(href)
            continue
        try:
            n = normalize_url(href, cfg, base)
        except Exception:
            continue
        if not urlsplit(n).scheme.startswith("http"):
            continue
        if is_allowed(n, cfg):
            if classify(n, None) == "document":
                docs.append(n)
            else:
                internal.append(n)
        else:
            external.append(n)
    # documents referenced by iframe/embed/object (flipbooks, PDF viewers)
    for tag in soup.find_all(["iframe", "embed", "object"]):
        src = tag.get("src") or tag.get("data") or ""
        m = re.search(r"(https?://[^\s\"'<>]+\.pdf)", src, re.I)
        if m:
            n = normalize_url(m.group(1), cfg, base)
            if is_allowed(n, cfg):
                docs.append(n)
    for m in re.finditer(r"https?://[^\s\"'<>\\]+\.pdf", html.decode("utf-8", "ignore"), re.I):
        n = normalize_url(m.group(0), cfg, base)
        if is_allowed(n, cfg):
            docs.append(n)
    dedupe = lambda xs: list(dict.fromkeys(xs))
    return {"title": title, "lang": lang, "canonical": canonical, "alternates": alternates,
            "internal": dedupe(internal), "external": dedupe(external),
            "documents": dedupe(docs), "anchors": dedupe(anchors)}


def run_discovery(cfg: dict, limit: int | None = None, only: list[str] | None = None) -> list[dict]:
    d = ensure_dirs(cfg)
    log = Log(cfg)
    delay = cfg["crawl"]["delay_seconds"]
    existing = load_manifest(cfg)
    by_norm = {r["normalized_url"]: r for r in existing}
    next_id = max([int(r["ref_id"][1:]) for r in existing] + [0]) + 1

    def entry(url: str, source: str) -> dict:
        nonlocal next_id
        n = normalize_url(url, cfg)
        if n in by_norm:
            row = by_norm[n]
            if source not in row["discovery_source"]:
                row["discovery_source"].append(source)
            return row
        row = {
            "ref_id": f"P{next_id:04d}", "discovered_url": url, "normalized_url": n,
            "final_url": "", "discovery_source": [source], "page_title": "", "language": "",
            "content_type": classify(n, None), "http_status": None, "redirect_chain": [],
            "capture_status": "pending", "screenshots": [], "notes": "",
            "slug": slugify(n), "discovered_at": utc_now(), "in_sitemap": False,
            "linked_from": [],
        }
        if is_excluded(n, cfg):
            row["capture_status"] = "excluded"
            row["notes"] = cfg["excluded_reason"]
        next_id += 1
        by_norm[n] = row
        existing.append(row)
        return row

    queue: deque[str] = deque()
    seen_fetch: set[str] = set()
    sitemap_urls: list[str] = []
    requests_made = 0
    stats = {"start": utc_now(), "requests": 0, "sitemaps": [], "errors": []}

    if only:
        for u in only:
            entry(u, "client_url_list")
            queue.append(normalize_url(u, cfg))
    else:
        for s in cfg["seeds"]:
            if s.endswith("robots.txt"):
                r = fetch(s, cfg); requests_made += 1; polite_sleep(delay)
                for m in re.finditer(r"(?im)^sitemap:\s*(\S+)", r["body"].decode("utf-8", "ignore")):
                    sitemap_urls.append(m.group(1))
                write_json(d["coverage"] / "robots.txt.json",
                           {"status": r["status"], "headers": r["headers"], "body": r["body"].decode("utf-8", "ignore")})
            elif s.endswith(".xml"):
                sitemap_urls.append(s)
            else:
                entry(s, "seed"); queue.append(normalize_url(s, cfg))
        for u in cfg.get("client_url_list", []):
            entry(u, "client_url_list"); queue.append(normalize_url(u, cfg))

        seen_sm: set[str] = set()
        sm_queue = deque(dict.fromkeys(sitemap_urls))
        while sm_queue:
            sm = sm_queue.popleft()
            if sm in seen_sm:
                continue
            seen_sm.add(sm)
            r = fetch(sm, cfg); requests_made += 1; polite_sleep(delay)
            log("INFO", f"sitemap {sm} -> {r['status']}")
            stats["sitemaps"].append({"url": sm, "status": r["status"], "cache": r["headers"].get("x-litespeed-cache")})
            (d["coverage"] / (slugify(sm) + ".xml")).write_bytes(r["body"])
            if r["status"] != 200:
                continue
            subs, pages = parse_sitemap(r["body"])
            sm_queue.extend(subs)
            for p in pages:
                n = normalize_url(p, cfg)
                if not is_allowed(n, cfg):
                    continue
                row = entry(p, f"sitemap:{sm}")
                row["in_sitemap"] = True
                queue.append(n)

    # BFS over internal links (HTML pages only; documents are recorded, not parsed)
    while queue:
        if limit and len(seen_fetch) >= limit:
            log("WARN", f"discovery limit {limit} reached; queue has {len(queue)} more URLs")
            break
        if requests_made >= cfg["crawl"]["max_requests"]:
            log("WARN", "max_requests reached during discovery"); break
        n = queue.popleft()
        if n in seen_fetch:
            continue
        seen_fetch.add(n)
        row = by_norm[n]
        if row["capture_status"] == "excluded" or row["content_type"] in ("document", "image"):
            continue
        r = fetch(n, cfg); requests_made += 1
        row["http_status"] = r["status"]
        row["final_url"] = r["final_url"]
        row["redirect_chain"] = [f"{c['url']} -> {c['status']} -> {c['location']}" for c in r["chain"]]
        ct = r["headers"].get("content-type", "")
        row["content_type"] = classify(r["final_url"], ct)
        if r["error"]:
            row["notes"] = (row["notes"] + " " + r["error"]).strip()
            stats["errors"].append({"url": n, "error": r["error"]})
        log("INFO", f"discover {row['ref_id']} {n} -> {r['status']} {row['content_type']} "
                    f"cache={r['headers'].get('x-litespeed-cache', '-')}")
        if r["status"] == 429:
            log("STOP", "HTTP 429 received - halting discovery per safety rules"); break
        if r["final_url"] != n and is_allowed(r["final_url"], cfg):
            # redirect target becomes its own manifest row so the destination is captured once
            tgt = entry(r["final_url"], f"redirect:{n}")
            if tgt["normalized_url"] not in seen_fetch:
                queue.append(tgt["normalized_url"])
            row["notes"] = (row["notes"] + f" redirects to {tgt['ref_id']}").strip()
        if row["content_type"] == "html" and r["body"]:
            links = extract_links(r["body"], r["final_url"], cfg)
            row["page_title"] = links["title"]
            row["language"] = links["lang"] or "und"
            write_json(d["links"] / f"{row['ref_id']}_{row['slug']}.links.json",
                       {"ref_id": row["ref_id"], "url": n, "fetched_at": utc_now(), **links})
            candidates = list(links["internal"])
            if links["canonical"]:
                candidates.append(links["canonical"])
            candidates += [a["url"] for a in links["alternates"]]
            for u in candidates:
                if not is_allowed(u, cfg):
                    continue
                child = entry(u, f"link:{row['ref_id']}")
                if row["ref_id"] not in child["linked_from"] and child is not row:
                    child["linked_from"].append(row["ref_id"])
                if child["normalized_url"] not in seen_fetch and child["capture_status"] != "excluded":
                    queue.append(child["normalized_url"])
            for u in links["documents"]:
                child = entry(u, f"document-link:{row['ref_id']}")
                if row["ref_id"] not in child["linked_from"]:
                    child["linked_from"].append(row["ref_id"])
        save_manifest(cfg, existing)
        polite_sleep(delay)

    stats["end"] = utc_now()
    stats["requests"] = requests_made
    stats["urls_total"] = len(existing)
    stats["by_status"] = {}
    for r in existing:
        stats["by_status"][r["capture_status"]] = stats["by_status"].get(r["capture_status"], 0) + 1
    write_json(d["coverage"] / "discovery-run.json", stats)
    save_manifest(cfg, existing)
    log("INFO", f"discovery complete: {len(existing)} URLs, {requests_made} requests")
    return existing
