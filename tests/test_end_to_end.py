"""
End-to-end test with a sample job posting file.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from extractors.job_extractor import JobExtractor
from matchers.resume_matcher import ResumeMatcher


SAMPLE_RESUME = """
Technical Skills:
- Python
- Flask
- SQL
- JavaScript
- Git
- Linux
"""

SAMPLE_JOB_TEXT = """
Software Engineer Intern
Location: Toronto, ON
We are looking for a Software Engineer Intern with experience in Python,
Django, React, and AWS. This is an entry-level position. Apply by October 1, 2026.
"""


def test_end_to_end():
    extractor = JobExtractor()
    raw = type("RawJob", (), {
        "title": "Software Engineer Intern",
        "company": "Shopify",
        "location": "",
        "url": "https://example.com/job",
        "raw_text": SAMPLE_JOB_TEXT,
        "source": "test",
    })
    job = extractor.extract(raw)
    assert job.location == "Toronto, ON"
    assert "python" in job.tech_stack

    matcher = ResumeMatcher(SAMPLE_RESUME)
    result = matcher.match(job)
    assert result.match_score > 0
    assert "python" in result.matched_skills
    assert "aws" in result.missing_skills
