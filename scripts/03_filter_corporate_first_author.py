#!/usr/bin/env python3
"""Step 3: Filter papers with likely corporate first-author affiliation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CORPORATE_KEYWORDS = {
    "inc",
    "corp",
    "corporation",
    "company",
    "co.,",
    "co., ltd",
    "ltd",
    "llc",
    "gmbh",
    "limited",
    "technologies",
    "technology",
    "labs",
    "laboratories",
    "research",
    "google",
    "microsoft",
    "meta",
    "amazon",
    "apple",
    "nvidia",
    "adobe",
    "bytedance",
    "tencent",
    "huawei",
    "samsung",
    "sony",
    "intel",
    "qualcomm",
    "openai",
}

ACADEMIC_HINTS = {
    "university",
    "institute",
    "college",
    "school",
    "department",
    "faculty",
}


def is_corporate_affiliation(affiliation: str) -> bool:
    text = affiliation.lower()
    if any(h in text for h in ACADEMIC_HINTS):
        return False
    return any(k in text for k in CORPORATE_KEYWORDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", type=Path, default=Path("data/cvpr2025/papers_with_affiliations.json"))
    parser.add_argument(
        "--out-json", type=Path, default=Path("data/cvpr2025/papers_first_author_corporate.json")
    )
    args = parser.parse_args()

    papers = json.loads(args.in_json.read_text(encoding="utf-8"))
    corporate = []

    for paper in papers:
        first_author = paper.get("authors", [""])[0] if paper.get("authors") else ""
        first_affiliation = paper.get("affiliations", [""])[0] if paper.get("affiliations") else ""
        is_corporate = bool(first_affiliation) and is_corporate_affiliation(first_affiliation)
        if is_corporate:
            corporate.append(
                {
                    "title": paper.get("title", ""),
                    "first_author": first_author,
                    "first_author_affiliation": first_affiliation,
                    "authors": paper.get("authors", []),
                    "affiliations": paper.get("affiliations", []),
                    "pdf_path": paper.get("pdf_path", ""),
                    "paper_url": paper.get("paper_url", ""),
                }
            )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(corporate, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Corporate-first-author papers: {len(corporate)} -> {args.out_json}")


if __name__ == "__main__":
    main()
