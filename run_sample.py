"""
Run harness against local sample job postings (no web scraping).
"""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from agents.scraper import RawJobPosting
from extractors.job_extractor import JobExtractor
from matchers.resume_matcher import ResumeMatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    with open("resume/resume.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()

    matcher = ResumeMatcher(resume_text)
    extractor = JobExtractor()

    raw_jobs = []
    with open("data/sample_jobs.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            raw_jobs.append(
                RawJobPosting(
                    title=data["title"],
                    company=data["company"],
                    location="",
                    url="",
                    raw_text=data["raw_text"],
                    source="sample",
                )
            )

    jobs = extractor.extract_many(raw_jobs)
    results = matcher.match_many(jobs)

    print("\n=== Ranked Job Matches ===\n")
    for idx, r in enumerate(results[:10], 1):
        print(f"{idx}. {r.job_title} at {r.company}")
        print(f"   Location: {r.location}")
        print(f"   Match: {r.match_score * 100:.1f}%")
        print(f"   Matched: {', '.join(r.matched_skills) or 'None'}")
        print(f"   Missing: {', '.join(r.missing_skills) or 'None'}")
        print(f"   Deadline: {r.deadline}")
        print(f"   Gap: {r.experience_gap}")
        print()


if __name__ == "__main__":
    main()
