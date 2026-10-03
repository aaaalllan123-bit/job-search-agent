"""
Flask web UI for the Job Search Agent Harness.
"""

import logging
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, os.path.dirname(__file__))

from agents.scraper import JobScraper
from extractors.job_extractor import JobExtractor
from matchers.resume_matcher import ResumeMatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
DEFAULT_RESUME_PATH = BASE_DIR / "resume" / "resume.txt"
DEFAULT_MOCK_PATH = BASE_DIR / "data" / "mock_careers.html"

PRESET_SOURCES = {
    "mock": {
        "name": "Mock Tech Careers",
        "url": "file://" + str(DEFAULT_MOCK_PATH.resolve()),
        "type": "static",
        "selectors": {
            "container": "article.job-card",
            "title": "h2.job-title",
            "link": "a",
        },
    },
    "geotab": {
        "name": "Geotab Internships",
        "url": "https://job-boards.greenhouse.io/internshiplist2000/jobs/4969991008",
        "type": "static",
        "follow_links": True,
        "selectors": {
            "container": ".job-post",
            "title": "a",
            "link": "a",
        },
    },
}

FIELD_RESUME_FILES = {
    "cs": BASE_DIR / "resume" / "resume_cs.txt",
    "finance": BASE_DIR / "resume" / "resume_finance.txt",
    "marketing": BASE_DIR / "resume" / "resume_marketing.txt",
    "design": BASE_DIR / "resume" / "resume_design.txt",
    "biomed": BASE_DIR / "resume" / "resume_biomed.txt",
    "social": BASE_DIR / "resume" / "resume_social.txt",
    "mechanical": BASE_DIR / "resume" / "resume_mechanical.txt",
    "electrical": BASE_DIR / "resume" / "resume_electrical.txt",
    "civil": BASE_DIR / "resume" / "resume_civil.txt",
    "chemical": BASE_DIR / "resume" / "resume_chemical.txt",
    "aerospace": BASE_DIR / "resume" / "resume_aerospace.txt",
    "industrial": BASE_DIR / "resume" / "resume_industrial.txt",
    "materials": BASE_DIR / "resume" / "resume_materials.txt",
    "environmental": BASE_DIR / "resume" / "resume_environmental.txt",
    "math": BASE_DIR / "resume" / "resume_math.txt",
    "physics": BASE_DIR / "resume" / "resume_physics.txt",
    "chemistry": BASE_DIR / "resume" / "resume_chemistry.txt",
    "medicine": BASE_DIR / "resume" / "resume_medicine.txt",
    "law": BASE_DIR / "resume" / "resume_law.txt",
    "architecture": BASE_DIR / "resume" / "resume_architecture.txt",
    "supply_chain": BASE_DIR / "resume" / "resume_supply_chain.txt",
    "hr": BASE_DIR / "resume" / "resume_hr.txt",
    "media": BASE_DIR / "resume" / "resume_media.txt",
    "policy": BASE_DIR / "resume" / "resume_policy.txt",
}


def load_resume_text(field: str) -> str:
    path = FIELD_RESUME_FILES.get(field, DEFAULT_RESUME_PATH)
    if not path.exists():
        path = DEFAULT_RESUME_PATH
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def run_pipeline(source: dict, field: str = "cs"):
    scraper = JobScraper(max_retries=2, backoff_seconds=1.0)
    extractor = JobExtractor(field=field)
    matcher = ResumeMatcher(load_resume_text(field), field=field)

    raw_jobs = scraper.scrape_source(source)
    jobs = extractor.extract_many(raw_jobs)
    results = matcher.match_many(jobs)
    return [r.to_dict() for r in results]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/presets")
def presets():
    return jsonify({"presets": list(PRESET_SOURCES.keys())})


@app.route("/api/match", methods=["POST"])
def match_jobs():
    data = request.get_json(silent=True) or {}
    source_type = data.get("source", "mock")

    if source_type in PRESET_SOURCES:
        source = PRESET_SOURCES[source_type]
    elif source_type == "custom":
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "URL is required for custom sources."}), 400
        source = {
            "name": data.get("name", "Custom Source") or "Custom Source",
            "url": url,
            "type": data.get("type", "static"),
            "selectors": {
                "container": data.get("container", "").strip() or "article, .job-card, .job-listing",
                "title": data.get("title", "").strip() or "h2, h3, .job-title",
                "link": data.get("link", "").strip() or "a",
            },
        }
    else:
        return jsonify({"error": f"Unknown source: {source_type}"}), 400

    field = data.get("field", "cs").strip().lower()
    try:
        results = run_pipeline(source, field=field)
        return jsonify({"jobs": results})
    except Exception as exc:
        logging.exception("Pipeline failed")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
