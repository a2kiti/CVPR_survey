#!/usr/bin/env python3
"""Step 2: Extract affiliation candidates from downloaded CVPR PDFs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_text_with_pdftotext(pdf_path: Path) -> str:
    try:
        proc = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", str(pdf_path), "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return ""
    if proc.returncode != 0:
        return ""
    return normalize_space(proc.stdout)


def infer_affiliations_from_text(first_page_text: str) -> list[str]:
    if not first_page_text:
        return []
    candidates = set()
    for match in re.finditer(
        r"([A-Z][A-Za-z&\-\. ]{2,}(University|Institute|College|Inc\.?|Corp\.?|Corporation|Ltd\.?|LLC|GmbH|Laboratories|Labs|Research|Technologies))",
        first_page_text,
    ):
        candidates.add(normalize_space(match.group(1)))
    return sorted(candidates)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", type=Path, default=Path("data/cvpr2025/downloaded_papers.json"))
    parser.add_argument("--out-json", type=Path, default=Path("data/cvpr2025/papers_with_affiliations.json"))
    args = parser.parse_args()

    papers = json.loads(args.in_json.read_text(encoding="utf-8"))
    results = []
    for paper in papers:
        pdf_path = Path(paper.get("pdf_path", ""))
        first_page_text = ""
        if paper.get("download_ok") and str(pdf_path):
            first_page_text = extract_text_with_pdftotext(pdf_path)

        affiliations = infer_affiliations_from_text(first_page_text)
        results.append(
            {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "affiliations": affiliations,
                "pdf_path": paper.get("pdf_path", ""),
                "paper_url": paper.get("paper_url", ""),
                "pdf_url": paper.get("pdf_url", ""),
            }
        )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted affiliations for {len(results)} papers -> {args.out_json}")


if __name__ == "__main__":
    main()
