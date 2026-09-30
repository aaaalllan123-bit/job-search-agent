"""
Run harness against a local mock career page (no external network needed).
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agents.scraper import JobScraper
from extractors.job_extractor import JobExtractor
from matchers.resume_matcher import ResumeMatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    scraper = JobScraper(max_retries=1, backoff_seconds=0.1)
    extractor = JobExtractor()

    with open("resume/resume.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    matcher = ResumeMatcher(resume_text)

    source = {
        "name": "Mock Tech Careers",
        "url": "file://" + os.path.abspath("data/mock_careers.html"),
        "type": "static",
        "selectors": {
            "container": "article.job-card",
            "title": "h2.job-title",
            "link": "a",
        },
    }

    raw_jobs = scraper.scrape_source(source)
    print(f"Scraped {len(raw_jobs)} raw postings\n")

    jobs = extractor.extract_many(raw_jobs)
    results = matcher.match_many(jobs)

    print("=== Ranked Job Matches ===\n")
    for idx, r in enumerate(results, 1):
        print(f"{idx}. {r.job_title}")
        print(f"   Location: {r.location}")
        print(f"   Match: {r.match_score * 100:.1f}%")
        print(f"   Matched: {', '.join(r.matched_skills) or 'None'}")
        print(f"   Missing: {', '.join(r.missing_skills) or 'None'}")
        print(f"   Experience: {r.experience_gap}")
        print(f"   Deadline: {r.deadline}")
        print("   Learning Plan:")
        for item in r.learning_plan:
            print(f"      - {item}")
        print()


if __name__ == "__main__":
    main()
