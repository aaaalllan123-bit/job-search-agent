# Job Search Agent Harness

A Python-based agent harness for collecting, analyzing, and matching student internship opportunities.

## Features

1. **Scraper**: Fetches job postings from company career pages with retry logic.
2. **Extractor**: Parses location, tech stack, experience level, and deadline.
3. **Matcher**: Scores jobs against your resume and ranks them.
4. **Gap Analyzer**: Lists missing skills and generates a learning plan.
5. **Logging**: Structured run logs and JSON Lines execution records.
6. **Tests**: Unit and end-to-end tests to verify extraction and matching accuracy.

## Project Structure

```
job-search-agent/
├── agents/           # Scraper implementations
├── extractors/       # Job field extraction
├── matchers/         # Resume matching and gap analysis
├── tests/            # Unit and integration tests
├── data/             # Output CSV and reports
├── logs/             # Execution logs
├── resume/           # Your resume text
├── config.yaml       # Source URLs and settings
├── requirements.txt
└── run.py            # Main entry point
```

## Setup

```bash
cd job-search-agent
pip install -r requirements.txt
```

## Configure

Edit `config.yaml`:

```yaml
resume_path: "resume/resume.txt"
sources:
  - name: "Shopify Careers"
    url: "https://www.shopify.com/careers"
    type: "static"
```

Put your resume in `resume/resume.txt`.

## Run

```bash
python run.py --config config.yaml
```

Outputs:
- `data/jobs.csv` — all extracted jobs
- `data/report.md` — ranked jobs with match scores and learning plans
- `logs/run.log` — execution log

## Test

```bash
pytest tests/
```

## Extending

- Add new sources in `config.yaml`.
- Add new tech keywords in `extractors/job_extractor.py`.
- Adjust scoring weights in `matchers/resume_matcher.py`.
