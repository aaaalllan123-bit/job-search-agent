"""
Test scraper against local mock HTML file.
"""

import os

from agents.scraper import JobScraper
from extractors.job_extractor import JobExtractor


def test_mock_scraper_end_to_end():
    scraper = JobScraper(max_retries=1, backoff_seconds=0.1)
    source = {
        "name": "Mock Tech Careers",
        "url": "file://" + os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "mock_careers.html")),
        "type": "static",
        "selectors": {
            "container": "article.job-card",
            "title": "h2.job-title",
            "link": "a",
        },
    }
    raw_jobs = scraper.scrape_source(source)
    assert len(raw_jobs) >= 5

    extractor = JobExtractor()
    jobs = extractor.extract_many(raw_jobs)

    titles = {j.title for j in jobs}
    assert "Backend Engineering Intern" in titles
    assert "Frontend Developer Co-op" in titles
    assert "Mechanical Design Intern" in titles
    assert "Financial Analyst Intern" in titles

    backend = next(j for j in jobs if j.title == "Backend Engineering Intern")
    assert backend.location == "Toronto, ON"
    assert "python" in backend.tech_stack
    assert "flask" in backend.tech_stack
    assert backend.deadline == "2026-10-15"
