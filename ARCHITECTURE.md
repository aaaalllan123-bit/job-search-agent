# Job Search Agent Harness — Architecture

## Components

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Sources    │────▶│   Scraper    │────▶│  Extractor   │────▶│   Matcher    │
│  (URLs/cfg)  │     │  + retry     │     │ (parse NLP)  │     │ (resume cmp) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                       │
                                                                       ▼
                                                               ┌──────────────┐
                                                               │  Gap Analyzer│
                                                               │ + learning   │
                                                               │   plan       │
                                                               └──────┬───────┘
                                                                      │
                                                                      ▼
                                                               ┌──────────────┐
                                                               │  Outputs     │
                                                               │ CSV + MD log │
                                                               └──────────────┘
```

## Data Flow

1. `run.py` reads `config.yaml` and loads resume.
2. `JobScraper` fetches each source with exponential backoff retries.
3. `JobExtractor` parses raw HTML into structured `JobPosting` objects.
4. `ResumeMatcher` compares each job's tech stack to resume skills.
5. `Gap Analyzer` (inside matcher) produces missing-skill learning plans.
6. Results saved to `data/jobs.csv` and `data/report.md`; logs go to `logs/run.log`.

## Extensibility

- Add new scraper backends (dynamic JS sites) under `agents/`.
- Extend keyword list in `extractors/job_extractor.py`.
- Customize scoring weights and experience heuristics in `matchers/resume_matcher.py`.
