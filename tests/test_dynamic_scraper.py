"""
Tests for dynamic scraper fallback.
"""

import pytest

from agents.scraper import JobScraper


def test_dynamic_fetch_uses_selenium(monkeypatch):
    calls = []

    def fake_driver(*args, **kwargs):
        class FakeDriver:
            def get(self, url):
                calls.append(("get", url))

            @property
            def page_source(self):
                return "<html><body><div class='job'><h2>Fake Job</h2><p>Python, AWS</p></div></body></html>"

            def quit(self):
                calls.append("quit")

        return FakeDriver()

    monkeypatch.setattr("agents.scraper._make_selenium_driver", fake_driver)
    scraper = JobScraper(max_retries=1, backoff_seconds=0.1)
    postings = scraper.scrape_source({"url": "https://example.com", "type": "dynamic", "name": "Example"})
    assert len(postings) == 1
    assert postings[0].title == "Fake Job"
    assert "quit" in calls
