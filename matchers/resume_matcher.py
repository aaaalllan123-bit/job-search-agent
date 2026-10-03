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
            "mechanical": {
                "cad": ["solidworks", "autocad", "catia", "nx", "inventor", "fusion 360"],
                "analysis": ["fea", "finite element analysis", "cfd", "computational fluid dynamics", "gd&t", "tolerance analysis"],
                "core": ["mechanical design", "thermodynamics", "fluid mechanics", "heat transfer", "materials science", "manufacturing"],
                "tools": ["matlab", "python", "labview", "arduino", "plc", "3d printing", "cnc", "machining"],
            },
            "electrical": {
                "design": ["circuit design", "pcb design", "altium", "eagle", "kicad", "orcad"],
                "digital": ["verilog", "vhdl", "fpga", "asic", "embedded systems", "microcontrollers", "arm", "stm32"],
                "core": ["signal processing", "control systems", "power electronics", "rf", "wireless"],
                "tools": ["matlab", "simulink", "python", "c", "c++", "labview", "arduino", "raspberry pi"],
            },
            "civil": {
                "software": ["autocad", "civil 3d", "revit", "bentley", "microstation", "bim", "etabs", "sap2000", "safe"],
                "core": ["structural analysis", "structural design", "concrete", "steel", "timber", "geotechnical", "transportation", "water resources"],
                "practice": ["surveying", "construction management", "project scheduling", "rs means"],
                "tools": ["matlab", "python", "excel"],
            },
            "chemical": {
                "software": ["aspen plus", "hysys", "chemcad", "process simulation"],
                "core": ["process design", "reactor design", "separation processes", "thermodynamics", "transport phenomena", "process control", "mass balance", "energy balance"],
                "domains": ["polymer", "catalysis", "petrochemicals", "pharmaceuticals"],
                "tools": ["matlab", "python", "excel", "labview", "six sigma", "lean"],
            },
            "aerospace": {
                "core": ["aerodynamics", "propulsion", "flight mechanics", "orbital mechanics", "systems engineering"],
                "materials/structures": ["structural analysis", "composite materials", "fea", "finite element analysis"],
                "software": ["catia", "nx", "solidworks", "cfd", "computational fluid dynamics"],
                "tools": ["matlab", "simulink", "python", "c", "c++", "arduino", "gnc", "guidance navigation control"],
            },
            "industrial": {
                "core": ["operations research", "optimization", "linear programming", "supply chain", "logistics", "inventory management", "production planning", "scheduling"],
                "quality": ["lean manufacturing", "six sigma", "process improvement", "quality control", "statistical process control"],
                "ergonomics": ["ergonomics", "simulation"],
                "tools": ["excel", "python", "r", "sql", "matlab", "arena", "anylogic"],
            },
            "materials": {
                "characterization": ["materials characterization", "microscopy", "sem", "tem", "xrd", "imagej"],
                "testing": ["mechanical testing", "tensile testing", "hardness testing", "fatigue"],
                "domains": ["metallurgy", "polymers", "ceramics", "composites", "nanomaterials"],
                "core/tools": ["thermodynamics", "phase diagrams", "materials selection", "matlab", "python", "origin"],
            },
            "environmental": {
                "core": ["environmental science", "water quality", "air quality", "soil remediation", "wastewater treatment", "solid waste management", "sustainability"],
                "assessment": ["environmental impact assessment", "eia", "life cycle assessment", "lca"],
                "geospatial": ["gis", "arcgis", "qgis", "remote sensing", "hydrology", "hydrogeology"],
                "tools": ["python", "r", "matlab", "excel"],
            },
            "math": {
                "core": ["mathematics", "statistics", "probability", "linear algebra", "calculus", "differential equations", "numerical analysis", "optimization", "modeling"],
                "data": ["python", "r", "matlab", "sas", "stata", "spss", "sql", "excel", "tableau", "power bi", "data analysis"],
                "ml": ["machine learning"],
            },
            "physics": {
                "core": ["physics", "mechanics", "electromagnetism", "quantum mechanics", "thermodynamics", "optics", "condensed matter", "particle physics", "astrophysics"],
                "methods": ["experimental design", "data analysis", "scientific computing"],
                "tools": ["python", "matlab", "mathematica", "c", "c++", "root", "labview"],
            },
            "chemistry": {
                "core": ["organic chemistry", "inorganic chemistry", "analytical chemistry", "physical chemistry", "biochemistry", "synthesis"],
                "analytical": ["chromatography", "spectroscopy", "nmr", "mass spectrometry", "hplc", "gc-ms", "wet lab"],
                "practice": ["chemical safety", "quality control"],
                "tools": ["python", "r", "matlab", "origin", "chemdraw"],
            },
            "medicine": {
                "clinical": ["clinical research", "patient care", "medical terminology", "anatomy", "physiology", "medical imaging"],
                "public health": ["biostatistics", "epidemiology", "public health"],
                "systems": ["emr", "electronic medical records", "hipaa", "clinical trials"],
                "tools": ["python", "r", "spss", "sas", "excel"],
            },
            "law": {
                "core": ["legal research", "legal writing", "case law", "contracts", "litigation", "due diligence", "regulatory compliance", "corporate law", "intellectual property"],
                "tools": ["westlaw", "lexisnexis", "bluebook", "brief writing"],
                "soft skills": ["negotiation"],
                "data": ["excel", "python", "sql", "data analysis", "document review"],
            },
            "architecture": {
                "design": ["architectural design", "space planning", "3d modeling", "rendering"],
                "software": ["revit", "autocad", "sketchup", "rhino", "grasshopper", "bim"],
                "rendering": ["v-ray", "lumion", "enscape"],
                "docs/presentation": ["building codes", "construction documents", "adobe creative suite", "photoshop", "illustrator", "indesign"],
            },
            "supply_chain": {
                "core": ["supply chain management", "logistics", "procurement", "inventory management", "demand planning", "warehouse management", "transportation", "distribution"],
                "systems": ["erp", "sap", "oracle", "netsuite"],
                "quality": ["six sigma", "lean"],
                "data": ["excel", "python", "sql", "tableau", "power bi", "data analysis"],
            },
            "hr": {
                "core": ["human resources", "recruiting", "talent acquisition", "onboarding", "employee relations", "performance management", "compensation", "benefits"],
                "systems": ["hris", "workday"],
                "analytics": ["people analytics", "diversity and inclusion", "training and development"],
                "data": ["excel", "python", "sql", "tableau", "power bi", "data analysis"],
            },
            "media": {
                "journalism": ["journalism", "reporting", "news writing", "feature writing", "editing"],
                "production": ["broadcasting", "video production", "audio production", "podcasting"],
                "digital": ["social media", "content creation", "seo", "digital storytelling"],
                "tools": ["adobe creative suite", "premiere", "after effects", "audition", "photoshop", "excel", "python", "data journalism"],
            },
            "policy": {
                "core": ["public policy", "policy analysis", "program evaluation", "legislative analysis", "stakeholder engagement", "grant writing", "budget analysis"],
                "methods": ["economics", "econometrics", "statistics", "research methods"],
                "data": ["python", "r", "stata", "spss", "excel", "tableau"],
                "geospatial": ["gis", "arcgis"],
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
