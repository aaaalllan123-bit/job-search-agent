"""
Unit tests for resume matching.
"""

import pytest

from extractors.job_extractor import JobPosting
from matchers.resume_matcher import ResumeMatcher


@pytest.fixture
def matcher():
    resume = "Python, Flask, SQL, JavaScript, HTML, Git, Linux"
    return ResumeMatcher(resume)


def test_perfect_match(matcher):
    job = JobPosting(
        title="Backend Intern",
        company="TestCo",
        location="Remote",
        url="",
        tech_stack=["python", "flask", "sql"],
        experience_required="Internship",
        deadline=None,
        raw_text="",
        source="test",
    )
    result = matcher.match(job)
    assert result.match_score == 1.0
    assert not result.missing_skills


def test_partial_match(matcher):
    job = JobPosting(
        title="Full Stack Intern",
        company="TestCo",
        location="Remote",
        url="",
        tech_stack=["python", "react", "aws"],
        experience_required="New grad",
        deadline=None,
        raw_text="",
        source="test",
    )
    result = matcher.match(job)
    assert result.match_score == pytest.approx(0.333, abs=0.01)
    assert "react" in result.missing_skills
    assert "aws" in result.missing_skills


def test_learning_plan_generated(matcher):
    job = JobPosting(
        title="ML Engineer",
        company="TestCo",
        location="Remote",
        url="",
        tech_stack=["python", "tensorflow", "pandas"],
        experience_required="Entry-level",
        deadline=None,
        raw_text="",
        source="test",
    )
    result = matcher.match(job)
    assert any("tensorflow" in item.lower() for item in result.learning_plan)
