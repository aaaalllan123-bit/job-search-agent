"""
Unit tests for scraper retry logic.
"""

import pytest

from agents.scraper import JobScraper


def test_retry_on_invalid_url():
    scraper = JobScraper(max_retries=2, backoff_seconds=0.1)
    with pytest.raises(Exception):
        scraper.fetch_static("http://localhost:9/invalid")
