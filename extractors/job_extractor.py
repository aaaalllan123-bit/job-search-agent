"""
Job posting extractor: parse structured fields from raw job text.
Extracts location, tech stack, experience requirements, and deadline.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dateutil import parser as date_parser


@dataclass
class JobPosting:
    title: str
    company: str
    location: str
    url: str
    tech_stack: List[str]
    experience_required: str
    deadline: Optional[str]
    raw_text: str
    source: str


# Skills by major/field. Extractor uses the union; matcher uses a per-field resume.
SKILL_KEYWORDS = {
    "cs": [
        "python", "c", "c++", "java", "javascript", "typescript", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
        "html", "css", "react", "vue", "angular", "svelte", "node.js", "nodejs",
        "django", "flask", "fastapi", "spring", "express", "rails",
        "sql", "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        "git", "linux", "unix", "bash", "shell", "powershell",
        "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", "numpy",
        "spark", "hadoop", "kafka", "airflow",
        "rest", "graphql", "grpc", "api", "microservices",
    ],
    "finance": [
        "excel", "financial modeling", "valuation", "dcf", "lbo", "npv", "irr",
        "accounting", "bookkeeping", "quickbooks", "sap", "erp",
        "bloomberg", "bloomberg terminal", "capital iq", "factset", "refinitiv",
        "investment", "investment banking", "asset management", "portfolio management",
        "trading", "equity research", "credit analysis", "risk management",
        "python", "sql", "vba", "r", "stata", "sas", "tableau", "power bi",
        "statistics", "econometrics", "forecasting",
    ],
    "marketing": [
        "marketing", "digital marketing", "content marketing", "email marketing",
        "seo", "sem", "google analytics", "google ads", "facebook ads", "meta ads",
        "social media", "content creation", "copywriting", "brand management",
        "market research", "survey design", "customer segmentation",
        "salesforce", "hubspot", "mailchimp", "hootsuite", "canva",
        "python", "sql", "excel", "tableau", "power bi", "google sheets",
        "adobe creative suite", "photoshop", "illustrator", "premiere",
    ],
    "design": [
        "ui", "ux", "ui/ux", "user research", "wireframing", "prototyping",
        "figma", "sketch", "adobe xd", "invision", "balsamiq",
        "photoshop", "illustrator", "indesign", "after effects", "premiere",
        "typography", "color theory", "design systems", "accessibility", "wcag",
        "html", "css", "javascript", "react", "web design", "responsive design",
        "motion graphics", "3d modeling", "blender", "cinema 4d",
    ],
    "biomed": [
        "lab techniques", "cell culture", "pcr", "gel electrophoresis", "western blot",
        "microscopy", "flow cytometry", "immunohistochemistry", "elisa",
        "clinical research", "clinical trials", "gcp", "regulatory affairs",
        "matlab", "r", "python", "spss", "sas", "graphpad prism",
        "biostatistics", "bioinformatics", "genomics", "proteomics",
        "medical devices", "fda", "iso 13485", "quality assurance",
    ],
    "social": [
        "research", "qualitative research", "quantitative research", "survey design",
        "spss", "r", "stata", "python", "excel", "statistics",
        "academic writing", "apa", "literature review", "data collection",
        "interviewing", "focus groups", "ethnography", "case study",
        "policy analysis", "program evaluation", "social impact",
        "teaching", "tutoring", "curriculum design", "classroom management",
    ],
}

# Backwards-compatible alias.
TECH_KEYWORDS = []
for _keywords in SKILL_KEYWORDS.values():
    TECH_KEYWORDS.extend(_keywords)


class JobExtractor:
    def __init__(self, field: str = "cs"):
        self.field = (field or "cs").lower()
        self.keywords = SKILL_KEYWORDS.get(self.field, SKILL_KEYWORDS["cs"])
        self.tech_pattern = re.compile(
            r"\b(" + "|".join(re.escape(k) for k in self.keywords) + r")\b",
            re.IGNORECASE,
        )

    def extract_tech_stack(self, text: str) -> List[str]:
        found = set()
        for match in self.tech_pattern.finditer(text.lower()):
            found.add(match.group(0).lower())
        return sorted(found)

    def extract_location(self, text: str, title: str = "") -> str:
        # Greenhouse-style titles often embed location after the job title.
        # e.g. "Software Developer Intern (Winter/January 2027, 4-8 Months)Oakville, Ontario - Canada; Waterloo, Ontario - Canada"
        if title:
            m = re.search(r"[)\]]([A-Z][A-Za-z\s,./\-]+(?:;\s*[A-Z][A-Za-z\s,./\-]+)*)", title)
            if m:
                return m.group(1).strip()

        # Common patterns: "Location: City, ST" or "City, ST / Remote"
        patterns = [
            r"Location\s*[:\-]\s*([A-Za-z][A-Za-z\s,./\-]+?)(?:\.|\n|$)",
            r"(?:based in|office in|site:)\s*([A-Za-z][A-Za-z\s,./\-]+?)(?:\.|\n|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Unknown"

    def clean_title(self, title: str) -> str:
        # Strip trailing location segment from Greenhouse-style titles.
        m = re.search(r"(.+?[)\]])\s*[A-Z][A-Za-z\s,./\-]+(?:;\s*[A-Z][A-Za-z\s,./\-]+)*$", title)
        if m:
            return m.group(1).strip()
        return title.strip()

    def extract_experience(self, text: str) -> str:
        patterns = [
            r"(\d\+?\s*(?:-\s*\d\+?)?\s*years?(?:\s*of)?\s*(?:experience|exp))",
            r"(new grad|new graduate|internship|co-op|entry[-\s]?level|junior|senior)",
            r"(bachelor'?s?|master'?s?|ph\.?d\.?|undergraduate|graduate)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Not specified"

    def extract_deadline(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:deadline|apply by|closing date|applications close)[:\s]+([^\n]+)",
            r"(?:apply before|closing|closes on)[:\s]+([^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw = match.group(1).strip()
                try:
                    parsed = date_parser.parse(raw, fuzzy=True)
                    return parsed.strftime("%Y-%m-%d")
                except Exception:
                    return raw
        return None

    def extract(self, raw_posting) -> JobPosting:
        text = raw_posting.raw_text
        cleaned_title = self.clean_title(raw_posting.title)
        return JobPosting(
            title=cleaned_title,
            company=raw_posting.company,
            location=self.extract_location(text, raw_posting.title),
            url=raw_posting.url,
            tech_stack=self.extract_tech_stack(text),
            experience_required=self.extract_experience(text),
            deadline=self.extract_deadline(text),
            raw_text=text,
            source=raw_posting.source,
        )

    def extract_many(self, raw_postings: list) -> List[JobPosting]:
        return [self.extract(p) for p in raw_postings]
