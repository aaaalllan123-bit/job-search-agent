"""
Job Search Agent Harness main runner.

Usage:
    python run.py --config config.yaml
"""

import argparse
import csv
import logging
import os
import sys
from datetime import datetime

import yaml

sys.path.insert(0, os.path.dirname(__file__))

from agents.scraper import JobScraper
from extractors.job_extractor import JobExtractor
from matchers.resume_matcher import ResumeMatcher


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/run.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_resume(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_jobs_csv(jobs, path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "company", "location", "url", "tech_stack", "experience", "deadline", "source"])
        for job in jobs:
            writer.writerow([
                job.title,
                job.company,
                job.location,
                job.url,
                "; ".join(job.tech_stack),
                job.experience_required,
                job.deadline or "",
                job.source,
            ])
    logger.info("Saved %d jobs to %s", len(jobs), path)


def save_report(results, path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Job Search Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"Total matched jobs: {len(results)}\n\n")

        for idx, r in enumerate(results, 1):
            f.write(f"## {idx}. {r.job_title} at {r.company}\n")
            f.write(f"- **Location:** {r.location}\n")
            f.write(f"- **URL:** {r.url}\n")
            f.write(f"- **Match Score:** {r.match_score * 100:.1f}%\n")
            f.write(f"- **Matched Skills:** {', '.join(r.matched_skills) or 'None'}\n")
            f.write(f"- **Missing Skills:** {', '.join(r.missing_skills) or 'None'}\n")
            f.write(f"- **Experience Gap:** {r.experience_gap}\n")
            f.write(f"- **Deadline:** {r.deadline}\n")
            f.write("- **Learning Plan:**\n")
            for item in r.learning_plan:
                f.write(f"  - {item}\n")
            f.write("\n")
    logger.info("Saved report to %s", path)


def main():
    parser = argparse.ArgumentParser(description="Job Search Agent Harness")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    config = load_config(args.config)
    resume_text = load_resume(config["resume_path"])

    scraper = JobScraper(
        max_retries=config.get("retry", {}).get("max_attempts", 3),
        backoff_seconds=config.get("retry", {}).get("backoff_seconds", 2.0),
    )
    extractor = JobExtractor()
    matcher = ResumeMatcher(resume_text)

    all_raw_jobs = []
    for source in config.get("sources", []):
        try:
            raw_jobs = scraper.scrape_source(source)
            all_raw_jobs.extend(raw_jobs)
        except Exception as exc:
            logger.error("Failed to scrape %s: %s", source.get("url"), exc)

    jobs = extractor.extract_many(all_raw_jobs)
    results = matcher.match_many(jobs)

    min_score = config.get("matching", {}).get("min_match_score", 0.0)
    top_k = config.get("matching", {}).get("top_k", 100)
    filtered = [r for r in results if r.match_score >= min_score][:top_k]

    save_jobs_csv(jobs, config["output"]["jobs_csv"])
    save_report(filtered, config["output"]["report_md"])

    logger.info("Done. Matched %d jobs above threshold.", len(filtered))


if __name__ == "__main__":
    main()
