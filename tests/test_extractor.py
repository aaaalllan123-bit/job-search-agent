"""
Unit tests for job field extraction.
Run with: pytest tests/test_extractor.py
"""

import pytest

from extractors.job_extractor import JobExtractor, JobPosting


@pytest.fixture
def extractor():
    return JobExtractor()


def test_extract_tech_stack(extractor):
    text = "We are looking for a Python developer with React, Node.js, and SQL experience."
    skills = extractor.extract_tech_stack(text)
    assert "python" in skills
    assert "react" in skills
    assert "node.js" in skills
    assert "sql" in skills


def test_extract_location(extractor):
    assert extractor.extract_location("Location: Toronto, ON") == "Toronto, ON"
    assert extractor.extract_location("No location info") == "Unknown"


def test_extract_experience(extractor):
    assert extractor.extract_experience("2+ years experience required") == "2+ years experience"
    assert extractor.extract_experience("New grad opportunity") == "New grad"


def test_extract_deadline(extractor):
    assert extractor.extract_deadline("Deadline: October 15, 2026") == "2026-10-15"
    assert extractor.extract_deadline("Apply whenever") is None


def test_full_extraction(extractor):
    raw = type("RawJob", (), {
        "title": "Software Engineer Intern",
        "company": "Shopify",
        "location": "",
        "url": "https://example.com/job",
        "raw_text": "Location: Waterloo, ON. We use Python, Flask, and SQL. 0-2 years experience. Apply by Dec 1, 2026.",
        "source": "test",
    })
    job = extractor.extract(raw)
    assert job.title == "Software Engineer Intern"
    assert job.location == "Waterloo, ON"
    assert "python" in job.tech_stack
    assert "flask" in job.tech_stack
    assert "sql" in job.tech_stack
    assert "0-2 years experience" in job.experience_required
    assert job.deadline == "2026-12-01"
