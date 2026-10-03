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
    "mechanical": [
        "solidworks", "autocad", "catia", "nx", "inventor", "fusion 360",
        "fea", "finite element analysis", "cfd", "computational fluid dynamics",
        "mechanical design", "thermodynamics", "fluid mechanics", "heat transfer",
        "materials science", "manufacturing", "cnc", "machining", "3d printing",
        "gd&t", "tolerance analysis", "ansys", "abaqus", "comsol",
        "matlab", "python", "labview", "arduino", "plc",
    ],
    "electrical": [
        "circuit design", "pcb design", "altium", "eagle", "kicad", "orcad",
        "verilog", "vhdl", "fpga", "asic", "embedded systems",
        "microcontrollers", "arduino", "raspberry pi", "stm32", "arm",
        "signal processing", "control systems", "power electronics",
        "matlab", "simulink", "python", "c", "c++", "labview",
        "oscilloscope", "multimeter", "soldering", "rf", "wireless",
    ],
    "civil": [
        "autocad", "civil 3d", "revit", "bentley", "microstation",
        "structural analysis", "structural design", "concrete", "steel", "timber",
        "geotechnical", "transportation", "water resources", "environmental engineering",
        "surveying", "construction management", "project scheduling", "bim",
        "matlab", "python", "excel", "rs means", "etabs", "sap2000", "safe",
    ],
    "chemical": [
        "process design", "process simulation", "aspen plus", "hysys", "chemcad",
        "reactor design", "separation processes", "thermodynamics", "transport phenomena",
        "process control", "p&id", "pfd", "mass balance", "energy balance",
        "polymer", "catalysis", "petrochemicals", "pharmaceuticals",
        "matlab", "python", "excel", "labview", "six sigma", "lean",
    ],
    "aerospace": [
        "aerodynamics", "propulsion", "flight mechanics", "orbital mechanics",
        "structural analysis", "composite materials", "cfd", "computational fluid dynamics",
        "fea", "finite element analysis", "catia", "nx", "solidworks",
        "avionics", "gnc", "guidance navigation control", "systems engineering",
        "matlab", "simulink", "python", "c", "c++", "arduino",
    ],
    "industrial": [
        "operations research", "optimization", "linear programming", "supply chain",
        "logistics", "inventory management", "production planning", "scheduling",
        "lean manufacturing", "six sigma", "process improvement", "ergonomics",
        "quality control", "statistical process control", "simulation",
        "excel", "python", "r", "sql", "matlab", "arena", "anylogic",
    ],
    "materials": [
        "materials characterization", "microscopy", "sem", "tem", "xrd",
        "mechanical testing", "tensile testing", "hardness testing", "fatigue",
        "metallurgy", "polymers", "ceramics", "composites", "nanomaterials",
        "thermodynamics", "phase diagrams", "materials selection",
        "matlab", "python", "origin", "imagej",
    ],
    "environmental": [
        "environmental science", "water quality", "air quality", "soil remediation",
        "environmental impact assessment", "eia", "life cycle assessment", "lca",
        "gis", "arcgis", "qgis", "remote sensing", "hydrology", "hydrogeology",
        "wastewater treatment", "solid waste management", "sustainability",
        "python", "r", "matlab", "excel",
    ],
    "math": [
        "mathematics", "statistics", "probability", "linear algebra", "calculus",
        "differential equations", "numerical analysis", "optimization", "modeling",
        "python", "r", "matlab", "mathematica", "sas", "stata", "spss",
        "sql", "excel", "tableau", "power bi", "machine learning", "data analysis",
    ],
    "physics": [
        "physics", "mechanics", "electromagnetism", "quantum mechanics", "thermodynamics",
        "optics", "condensed matter", "particle physics", "astrophysics",
        "experimental design", "data analysis", "scientific computing",
        "python", "matlab", "mathematica", "c", "c++", "root", "labview",
    ],
    "chemistry": [
        "organic chemistry", "inorganic chemistry", "analytical chemistry", "physical chemistry",
        "biochemistry", "synthesis", "chromatography", "spectroscopy", "nmr", "mass spectrometry",
        "hplc", "gc-ms", "wet lab", "chemical safety", "quality control",
        "python", "r", "matlab", "origin", "chemdraw",
    ],
    "medicine": [
        "clinical research", "patient care", "medical terminology", "anatomy", "physiology",
        "biostatistics", "epidemiology", "public health", "health informatics",
        "emr", "electronic medical records", "hipaa", "clinical trials",
        "python", "r", "spss", "sas", "excel", "medical imaging",
    ],
    "law": [
        "legal research", "legal writing", "case law", "contracts", "litigation",
        "due diligence", "regulatory compliance", "corporate law", "intellectual property",
        "westlaw", "lexisnexis", "bluebook", "brief writing", "negotiation",
        "excel", "python", "sql", "data analysis", "document review",
    ],
    "architecture": [
        "architectural design", "space planning", "building codes", "construction documents",
        "revit", "autocad", "sketchup", "rhino", "grasshopper", "bim",
        "3d modeling", "rendering", "v-ray", "lumion", "enscape",
        "adobe creative suite", "photoshop", "illustrator", "indesign",
    ],
    "supply_chain": [
        "supply chain management", "logistics", "procurement", "inventory management",
        "demand planning", "warehouse management", "transportation", "distribution",
        "erp", "sap", "oracle", "netsuite", "six sigma", "lean",
        "excel", "python", "sql", "tableau", "power bi", "data analysis",
    ],
    "hr": [
        "human resources", "recruiting", "talent acquisition", "onboarding", "employee relations",
        "performance management", "compensation", "benefits", "hris", "workday",
        "people analytics", "diversity and inclusion", "training and development",
        "excel", "python", "sql", "tableau", "power bi", "data analysis",
    ],
    "media": [
        "journalism", "reporting", "news writing", "feature writing", "editing",
        "broadcasting", "video production", "audio production", "podcasting",
        "adobe creative suite", "premiere", "after effects", "audition", "photoshop",
        "social media", "content creation", "seo", "digital storytelling",
        "excel", "python", "data journalism",
    ],
    "policy": [
        "public policy", "policy analysis", "program evaluation", "legislative analysis",
        "economics", "econometrics", "statistics", "research methods",
        "stakeholder engagement", "grant writing", "budget analysis",
        "python", "r", "stata", "spss", "excel", "tableau", "gis", "arcgis",
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
