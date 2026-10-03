"""
Resume matcher: compare job postings against a resume and compute match scores.
Also generates gap analysis and learning recommendations.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    job_title: str
    company: str
    location: str
    url: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_gap: str
    deadline: str
    learning_plan: List[str]

    def to_dict(self) -> Dict:
        return {
            "job_title": self.job_title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "match_score": self.match_score,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "experience_gap": self.experience_gap,
            "deadline": self.deadline,
            "learning_plan": self.learning_plan,
        }


class ResumeMatcher:
    def __init__(self, resume_text: str, field: str = "cs"):
        self.field = (field or "cs").lower()
        self.resume_text = resume_text.lower()
        self.resume_skills = self._extract_skills(resume_text)
        logger.info("Loaded %s resume with %d skills", self.field, len(self.resume_skills))

    def _extract_skills(self, text: str) -> set:
        from extractors.job_extractor import SKILL_KEYWORDS

        text = text.lower()
        keywords = SKILL_KEYWORDS.get(self.field, [])
        skills = set()
        for skill in keywords:
            if skill.lower() in text:
                skills.add(skill.lower())
        return skills

    def _compute_score(self, job_tech_stack: List[str]) -> float:
        if not job_tech_stack:
            return 0.0
        matched = [s for s in job_tech_stack if s.lower() in self.resume_skills]
        return round(len(matched) / len(job_tech_stack), 3)

    def _build_learning_plan(self, missing: List[str], title: str) -> List[str]:
        plan = []
        if not missing:
            return ["You already match the core skills. Focus on interview prep and portfolio projects."]

        # Group by category for nicer output; varies by field.
        categories = {
            "cs": {
                "programming": ["python", "c", "c++", "java", "javascript", "typescript", "go", "rust"],
                "web": ["html", "css", "react", "vue", "angular", "node.js", "flask", "django"],
                "data": ["sql", "postgresql", "mysql", "mongodb", "pandas", "numpy"],
                "cloud/devops": ["aws", "azure", "gcp", "docker", "kubernetes", "git", "linux"],
                "ml": ["machine learning", "deep learning", "tensorflow", "pytorch"],
            },
            "finance": {
                "modeling": ["financial modeling", "valuation", "dcf", "lbo", "npv", "irr"],
                "tools": ["excel", "bloomberg", "capital iq", "factset", "refinitiv", "quickbooks", "sap"],
                "analysis": ["accounting", "investment", "portfolio management", "risk management", "equity research"],
                "data": ["python", "sql", "r", "stata", "sas", "tableau", "power bi", "statistics"],
            },
            "marketing": {
                "channels": ["seo", "sem", "social media", "email marketing", "content marketing", "digital marketing"],
                "tools": ["google analytics", "google ads", "facebook ads", "meta ads", "salesforce", "hubspot", "mailchimp", "hootsuite", "canva"],
                "skills": ["content creation", "copywriting", "brand management", "market research", "customer segmentation"],
                "data": ["python", "sql", "excel", "tableau", "power bi"],
            },
            "design": {
                "ui/ux": ["ui", "ux", "ui/ux", "user research", "wireframing", "prototyping", "design systems", "accessibility"],
                "tools": ["figma", "sketch", "adobe xd", "photoshop", "illustrator", "indesign", "after effects", "premiere"],
                "dev": ["html", "css", "javascript", "react", "web design", "responsive design"],
                "motion/3d": ["motion graphics", "3d modeling", "blender", "cinema 4d"],
            },
            "biomed": {
                "lab": ["lab techniques", "cell culture", "pcr", "gel electrophoresis", "western blot", "microscopy", "flow cytometry", "immunohistochemistry", "elisa"],
                "research": ["clinical research", "clinical trials", "gcp", "regulatory affairs", "medical devices", "fda", "iso 13485", "quality assurance"],
                "data": ["matlab", "r", "python", "spss", "sas", "graphpad prism", "biostatistics", "bioinformatics", "genomics", "proteomics"],
            },
            "social": {
                "methods": ["research", "qualitative research", "quantitative research", "survey design", "interviewing", "focus groups", "ethnography", "case study"],
                "data": ["spss", "r", "stata", "python", "excel", "statistics"],
                "writing": ["academic writing", "apa", "literature review", "data collection"],
                "practice": ["policy analysis", "program evaluation", "social impact", "teaching", "tutoring", "curriculum design", "classroom management"],
            },
        }
        field_categories = categories.get(self.field, categories["cs"])

        grouped = {}
        for skill in missing:
            assigned = False
            for cat, items in field_categories.items():
                if skill.lower() in items:
                    grouped.setdefault(cat, []).append(skill)
                    assigned = True
                    break
            if not assigned:
                grouped.setdefault("other", []).append(skill)

        for cat, skills in grouped.items():
            plan.append(f"{cat.title()}: learn {', '.join(skills)} through small projects or tutorials.")

        plan.append(f"Build a mini project related to '{title}' that uses at least one missing skill.")
        return plan

    def match(self, job) -> MatchResult:
        job_skills = [s.lower() for s in job.tech_stack]
        matched = [s for s in job_skills if s in self.resume_skills]
        missing = [s for s in job_skills if s not in self.resume_skills]
        score = self._compute_score(job_skills)

        experience_gap = ""
        exp = job.experience_required.lower()
        if "senior" in exp or "5+" in exp or "5 years" in exp:
            experience_gap = "Senior-level role; may be difficult without prior internship experience."
        elif "new grad" in exp or "internship" in exp or "co-op" in exp or "entry" in exp:
            experience_gap = "Entry-level friendly; aligns with student experience."
        else:
            experience_gap = "Experience requirements not clearly matched; read full posting."

        return MatchResult(
            job_title=job.title,
            company=job.company,
            location=job.location,
            url=job.url,
            match_score=score,
            matched_skills=matched,
            missing_skills=missing,
            experience_gap=experience_gap,
            deadline=job.deadline or "Not listed",
            learning_plan=self._build_learning_plan(missing, job.title),
        )

    def match_many(self, jobs: list) -> List[MatchResult]:
        results = [self.match(job) for job in jobs]
        results.sort(key=lambda r: r.match_score, reverse=True)
        return results
