"""CLI entry point: python -m tools.vrr <command> [options]."""
from __future__ import annotations

import argparse

from .common import load_config


def main() -> None:
    ap = argparse.ArgumentParser(prog="vrr", description="Visual Recovery Reference capture toolkit")
    ap.add_argument("--config", default=None, help="path to capture.config.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("discover", help="passive URL discovery (sitemaps, robots.txt, internal links)")
    p.add_argument("--limit", type=int, default=None, help="max HTML pages to fetch during discovery")
    p.add_argument("--only", nargs="*", default=None, help="discover only these URLs (pilot mode)")
    p.add_argument("--fetch-pages", action="store_true",
                   help="also GET HTML pages during discovery (adds a request per URL; off by default for LiteSpeed sites)")

    p = sub.add_parser("capture", help="rate-limited Playwright capture of manifest rows")
    p.add_argument("--refs", nargs="*", default=None, help="restrict to these reference IDs")
    p.add_argument("--viewports", nargs="*", default=None)
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--force", action="store_true", help="re-capture rows already marked captured (overwrites files)")
    p.add_argument("--no-expand", action="store_true", help="do not queue new URLs found in rendered pages")

    sub.add_parser("qa", help="automated quality assurance checks")
    sub.add_parser("integrity", help="SHA-256 hashing and evidence register")
    sub.add_parser("report", help="gallery, summaries, executive PDF")
    sub.add_parser("pdfbook", help="single PDF: current-state report + every screenshot embedded")
    sub.add_parser("all", help="discover -> capture -> qa -> integrity -> report")

    a = ap.parse_args()
    cfg = load_config(a.config)

    if a.cmd == "discover":
        from .discover import run_discovery
        run_discovery(cfg, limit=a.limit, only=a.only, fetch_pages=a.fetch_pages)
    elif a.cmd == "capture":
        from .capture import run_capture
        run_capture(cfg, refs=a.refs, viewports=a.viewports, max_pages=a.max_pages, force=a.force,
                    expand_links=not a.no_expand)
    elif a.cmd == "qa":
        from .qa import run_qa
        run_qa(cfg)
    elif a.cmd == "integrity":
        from .integrity import run_integrity
        run_integrity(cfg)
    elif a.cmd == "report":
        from .report import run_report
        run_report(cfg)
    elif a.cmd == "pdfbook":
        from .pdfbook import run_pdfbook
        run_pdfbook(cfg)
    elif a.cmd == "all":
        from .discover import run_discovery
        from .capture import run_capture
        from .qa import run_qa
        from .integrity import run_integrity
        from .report import run_report
        run_discovery(cfg)
        run_capture(cfg)
        run_qa(cfg)
        run_integrity(cfg)
        run_report(cfg)


if __name__ == "__main__":
    main()
