# Intelligent Resume Analyzer

Shortlist is a local Streamlit application for consistent, explainable resume screening. It extracts contact details, skills, experience, and education from candidate resumes, compares them with a job brief, and produces a weighted match score plus a hiring recommendation.

## Installation

```sh
pip install -r requirements.txt
streamlit run app.py
```

Upload `.txt`, `.pdf`, or `.docx` resumes, or paste a resume directly into the workspace. Job descriptions work best when they include a `Required` section, an optional `Preferred` section, and an experience threshold such as `At least 3 years experience`.

Scoring is intentionally transparent: required skills are 70% of the score, experience is 20%, and preferred skills are 10%. The parser runs locally with deterministic rules; it does not send resume data to an external service.
