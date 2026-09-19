"""Explainable resume parsing and job-fit scoring utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


DEFAULT_SKILLS = (
    "python", "java", "javascript", "typescript", "sql", "excel", "aws",
    "azure", "docker", "kubernetes", "git", "linux", "react", "django",
    "flask", "fastapi", "pandas", "numpy", "machine learning", "nlp",
    "communication", "leadership", "project management", "agile", "scrum",
)


@dataclass
class ResumeProfile:
    name: str = "Unknown candidate"
    email: str = "Not found"
    phone: str = "Not found"
    skills: list[str] = field(default_factory=list)
    years_experience: float = 0.0
    education: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class MatchReport:
    profile: ResumeProfile
    required_matches: list[str]
    required_gaps: list[str]
    preferred_matches: list[str]
    matched_evidence: dict[str, str]
    score: int
    recommendation: str
    rationale: list[str]


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _terms(values: Iterable[str]) -> list[str]:
    return [_clean(value).lower() for value in values if _clean(value)]


def extract_profile(text: str, known_skills: Iterable[str] = DEFAULT_SKILLS) -> ResumeProfile:
    """Extract high-signal resume fields using deterministic, inspectable rules."""
    lines = [_clean(line) for line in text.splitlines() if _clean(line)]
    email_match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text)
    name = next(
        (line for line in lines[:5] if "@" not in line and not re.search(r"\d", line)
         and len(line.split()) <= 5),
        "Unknown candidate",
    )
    lowered = text.lower()
    skills = [skill for skill in _terms(known_skills) if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", lowered)]
    experience_matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", lowered)
    years = max((float(value) for value in experience_matches), default=0.0)
    education = [line for line in lines if re.search(r"\b(bachelor|master|ph\.d|doctorate|degree|university|college)\b", line, re.I)]
    summary = next((line for line in lines if len(line) >= 80), " ".join(lines[:2]))
    return ResumeProfile(
        name=name,
        email=email_match.group(0) if email_match else "Not found",
        phone=phone_match.group(0) if phone_match else "Not found",
        skills=skills,
        years_experience=years,
        education=education[:4],
        summary=summary,
    )


def parse_job_requirements(job_text: str, known_skills: Iterable[str] = DEFAULT_SKILLS) -> tuple[list[str], list[str], float]:
    """Parse required/preferred skills and minimum experience from job text."""
    lines = [_clean(line) for line in job_text.splitlines() if _clean(line)]
    required: list[str] = []
    preferred: list[str] = []
    in_preferred = False
    skill_terms = _terms(known_skills)
    for line in lines:
        if re.search(r"preferred|nice to have|bonus", line, re.I):
            in_preferred = True
        for skill in skill_terms:
            if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", line.lower()):
                (preferred if in_preferred else required).append(skill)
    minimum = re.search(r"(?:at least|minimum of|required)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", job_text, re.I)
    return list(dict.fromkeys(required)), list(dict.fromkeys(preferred)), float(minimum.group(1)) if minimum else 0.0


def analyze_resume(resume_text: str, job_text: str, known_skills: Iterable[str] = DEFAULT_SKILLS) -> MatchReport:
    profile = extract_profile(resume_text, known_skills)
    required, preferred, minimum_years = parse_job_requirements(job_text, known_skills)
    resume_lower = resume_text.lower()
    required_matches = [item for item in required if item in resume_lower]
    required_gaps = [item for item in required if item not in resume_lower]
    preferred_matches = [item for item in preferred if item in resume_lower]
    evidence = {item: f"Found '{item}' in resume text" for item in required_matches + preferred_matches}
    skill_score = (len(required_matches) / len(required) * 70) if required else 70
    experience_score = 20 if not minimum_years else min(profile.years_experience / minimum_years, 1) * 20
    preferred_score = (len(preferred_matches) / len(preferred) * 10) if preferred else 10
    score = round(skill_score + experience_score + preferred_score)
    if score >= 80 and not required_gaps:
        recommendation = "Strong match"
    elif score >= 60:
        recommendation = "Review"
    else:
        recommendation = "Do not advance"
    rationale = [
        f"Matches {len(required_matches)} of {len(required)} required criteria.",
        f"Shows {profile.years_experience:g} years of experience" + (f" against {minimum_years:g} required." if minimum_years else "."),
    ]
    if required_gaps:
        rationale.append("Missing: " + ", ".join(required_gaps[:5]) + ".")
    return MatchReport(profile, required_matches, required_gaps, preferred_matches, evidence, score, recommendation, rationale)