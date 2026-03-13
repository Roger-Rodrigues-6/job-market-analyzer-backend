from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import search_jobs
from collections import Counter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/search")
def search(
    q: str = "",
    include: str = "",
    exclude: str = "",
    exclude_companies: str = "",
    location: str = "",
    period: str = "24h",
    remote: str = "",
    english: str = "include"
):

    include_skills = [s.strip() for s in include.split(",") if s.strip()]
    exclude_skills = [s.strip() for s in exclude.split(",") if s.strip()]
    exclude_companies = [s.strip() for s in exclude_companies.split(",") if s.strip()]

    jobs = search_jobs(
        query=q,
        include_skills=include_skills,
        exclude_skills=exclude_skills,
        exclude_companies=exclude_companies,
        location=location,
        period=period,
        remote=remote,
        english=english
    )

    # =========================
    # MARKET ANALYSIS
    # =========================

    skills_counter = Counter()

    for job in jobs:

        for skill in job["matched_skills"]:
            skills_counter[skill] += 1

    top_skills = []

    for skill, count in skills_counter.most_common(10):
        top_skills.append({
            "name": skill,
            "count": count
        })

    summary = (
        f"Foram analisadas {len(jobs)} vagas. "
        "As habilidades mais presentes entre as vagas analisadas foram: "
        + ", ".join([s["name"] for s in top_skills[:5]])
    )

    return {
        "total_jobs": len(jobs),
        "jobs": jobs,
        "skills": top_skills,
        "summary": summary
    }