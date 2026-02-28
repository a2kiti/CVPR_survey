#!/usr/bin/env python3
"""Step 1: Download CVPR2025 PDFs from CVF Open Access with polite scraping."""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://openaccess.thecvf.com/"
LIST_URL = "https://openaccess.thecvf.com/CVPR2025?day=all"
USER_AGENT = "Mozilla/5.0 (compatible; CVPRSurveyBot/1.0; +polite-research)"


def fetch_text(url: str, timeout: int = 30, retries: int = 3, retry_wait: float = 2.0) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset, errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            last_error = e
            if attempt < retries:
                time.sleep(retry_wait * attempt)
    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to fetch: {url}")


def download_file(url: str, dst: Path, timeout: int = 60, retries: int = 3) -> bool:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urlopen(req, timeout=timeout) as resp, dst.open("wb") as wf:
                wf.write(resp.read())
            return True
        except (HTTPError, URLError, TimeoutError, OSError):
            if attempt < retries:
                time.sleep(1.5 * attempt)
    return False


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_listing_page(listing_html: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r'<dt class="ptitle">\s*<a href="(?P<paper>[^"]+)">(?P<title>.*?)</a>\s*</dt>.*?'
        r'<dd>\s*<a href="(?P<pdf>[^"]+)"[^>]*>pdf</a>',
        re.S | re.I,
    )
    items: list[dict[str, str]] = []
    for m in pattern.finditer(listing_html):
        title = normalize_space(html.unescape(re.sub(r"<[^>]+>", "", m.group("title"))))
        items.append(
            {
                "title": title,
                "paper_url": urljoin(BASE_URL, m.group("paper")),
                "pdf_url": urljoin(BASE_URL, m.group("pdf")),
            }
        )
    return items


def parse_authors_from_paper_page(paper_html: str) -> list[str]:
    m = re.search(r"<i>(.*?)</i>", paper_html, re.S | re.I)
    if not m:
        return []
    raw = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
    return [normalize_space(x) for x in raw.split(",") if normalize_space(x)]


def slugify_filename(name: str, max_len: int = 140) -> str:
    s = re.sub(r"[^\w\-. ]+", "", name)
    s = re.sub(r"\s+", "_", s).strip("._")
    if len(s) > max_len:
        s = s[:max_len].rstrip("._")
    return s or "paper"


def polite_sleep(base_delay: float) -> None:
    time.sleep(base_delay + random.uniform(0.2, 0.8))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("data/cvpr2025"))
    parser.add_argument("--delay-seconds", type=float, default=1.5)
    parser.add_argument("--max-papers", type=int, default=None)
    parser.add_argument("--listing-html-path", type=Path, default=None)
    args = parser.parse_args()

    out_dir = args.out_dir
    pdf_dir = out_dir / "pdfs"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    if args.listing_html_path:
        listing_html = args.listing_html_path.read_text(encoding="utf-8")
    else:
        listing_html = fetch_text(LIST_URL)

    entries = parse_listing_page(listing_html)
    if args.max_papers is not None:
        entries = entries[: args.max_papers]

    downloaded: list[dict] = []
    for idx, entry in enumerate(entries, 1):
        polite_sleep(args.delay_seconds)

        authors: list[str] = []
        try:
            paper_html = fetch_text(entry["paper_url"])
            authors = parse_authors_from_paper_page(paper_html)
        except Exception:
            pass

        file_name = f"{idx:04d}_{slugify_filename(entry['title'])}.pdf"
        pdf_path = pdf_dir / file_name
        if not pdf_path.exists():
            ok = download_file(entry["pdf_url"], pdf_path)
        else:
            ok = True

        downloaded.append(
            {
                "title": entry["title"],
                "paper_url": entry["paper_url"],
                "pdf_url": entry["pdf_url"],
                "authors": authors,
                "pdf_path": str(pdf_path) if ok else "",
                "download_ok": ok,
            }
        )

    output_path = out_dir / "downloaded_papers.json"
    output_path.write_text(json.dumps(downloaded, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Downloaded metadata for {len(downloaded)} papers -> {output_path}")


if __name__ == "__main__":
    main()
