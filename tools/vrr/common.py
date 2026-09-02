"""Shared helpers: configuration, URL normalisation, logging, manifest persistence."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlsplit, urlunsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_VERSION = "vrr 1.0.0"

MANIFEST_FIELDS = [
    "ref_id", "discovered_url", "normalized_url", "final_url", "discovery_source",
    "page_title", "language", "content_type", "http_status", "redirect_chain",
    "capture_status", "screenshots", "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else REPO_ROOT / "capture.config.json"
    with open(p, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["_config_path"] = str(p)
    out = Path(cfg["output_dir"])
    cfg["_out"] = out if out.is_absolute() else REPO_ROOT / out
    return cfg


def out_dirs(cfg: dict) -> dict[str, Path]:
    o = cfg["_out"]
    d = {
        "root": o,
        "shots": o / "screenshots",
        "interactive": o / "screenshots" / "interactive-states",
        "html_response": o / "html" / "response",
        "html_rendered": o / "html" / "rendered",
        "assets": o / "assets",
        "headers": o / "metadata" / "headers",
        "redirects": o / "metadata" / "redirects",
        "links": o / "metadata" / "links",
        "page_data": o / "metadata" / "page-data",
        "contact": o / "reports" / "visual-contact-sheets",
        "broken": o / "reports" / "broken-pages",
        "coverage": o / "reports" / "crawl-coverage",
        "integrity": o / "integrity",
        "state": o / ".state",
    }
    for vp in cfg["viewports"]:
        d[f"shots_{vp}_full"] = o / "screenshots" / vp / "full-page"
        d[f"shots_{vp}_fold"] = o / "screenshots" / vp / "above-fold"
    for sub in ("images", "styles", "scripts", "fonts", "documents", "other"):
        d[f"assets_{sub}"] = o / "assets" / sub
    return d


def ensure_dirs(cfg: dict) -> dict[str, Path]:
    d = out_dirs(cfg)
    for p in d.values():
        p.mkdir(parents=True, exist_ok=True)
    return d


class Log:
    """Append-only capture log (integrity/capture-log.txt) that also echoes to stdout."""

    def __init__(self, cfg: dict):
        self.path = out_dirs(cfg)["integrity"] / "capture-log.txt"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, level: str, msg: str) -> None:
        line = f"{utc_now()} [{level}] {msg}"
        print(line, flush=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


# ---------------------------------------------------------------- URL helpers

def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def is_allowed(url: str, cfg: dict) -> bool:
    return host_of(url) in {h.lower() for h in cfg["allowed_hosts"]}


def normalize_url(url: str, cfg: dict, base: str | None = None) -> str:
    """Resolve relative links, drop fragments and tracking params, canonicalise host/scheme."""
    if base:
        url = urljoin(base, url)
    parts = urlsplit(url.strip())
    scheme = "https" if parts.scheme in ("http", "https") else parts.scheme
    host = (parts.hostname or "").lower()
    if host.startswith("www.") and host[4:] in [h.lower() for h in cfg["allowed_hosts"]]:
        host = host[4:]
    path = parts.path or "/"
    # keep unicode paths readable but consistently percent-encoded
    path = quote(unquote(path), safe="/%:@!$&'()*+,;=-._~")
    tracking = set(cfg.get("tracking_params", []))
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in tracking]
    query = urlencode(sorted(q), doseq=True)
    return urlunsplit((scheme, host, path, query, ""))


def is_excluded(url: str, cfg: dict) -> bool:
    parts = urlsplit(url)
    target = parts.path + ("?" + parts.query if parts.query else "")
    return any(re.search(pat, target) for pat in cfg["exclude_path_patterns"])


def classify(url: str, content_type_header: str | None) -> str:
    path = urlsplit(url).path.lower()
    ct = (content_type_header or "").lower()
    if any(path.endswith(e) for e in (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip")) or "application/pdf" in ct:
        return "document"
    if path.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico")) or ct.startswith("image/"):
        return "image"
    if path.endswith(".xml") or "xml" in ct and "html" not in ct:
        return "xml"
    if "text/html" in ct or ct == "" or path.endswith((".html", "/")) or "." not in path.rsplit("/", 1)[-1]:
        return "html"
    return "other"


def slugify(url: str, max_len: int = 60) -> str:
    parts = urlsplit(url)
    raw = unquote(parts.path).strip("/") or "home"
    if parts.query:
        raw += "_" + parts.query
    raw = unicodedata.normalize("NFKD", raw)
    raw = re.sub(r"[^\w\-]+", "_", raw, flags=re.UNICODE).strip("_").lower()
    raw = re.sub(r"_+", "_", raw)
    return raw[:max_len] or "page"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def short_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]


# ------------------------------------------------------------ manifest I/O

def manifest_paths(cfg: dict) -> tuple[Path, Path]:
    o = cfg["_out"]
    return o / "url-manifest.json", o / "url-manifest.csv"


def load_manifest(cfg: dict) -> list[dict]:
    jp, _ = manifest_paths(cfg)
    if jp.exists():
        with open(jp, encoding="utf-8") as fh:
            return json.load(fh)
    return []


def save_manifest(cfg: dict, rows: list[dict]) -> None:
    jp, cp = manifest_paths(cfg)
    jp.parent.mkdir(parents=True, exist_ok=True)
    tmp = jp.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, jp)
    with open(cp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            rr = dict(r)
            for k in ("redirect_chain", "screenshots", "discovery_source"):
                v = rr.get(k)
                if isinstance(v, list):
                    rr[k] = " | ".join(str(x) for x in v)
            w.writerow(rr)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, default=str)


def polite_sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)
