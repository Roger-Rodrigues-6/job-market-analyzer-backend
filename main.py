from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import search_jobs

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
    location: str = "Brazil",
    period: str = "24h",
    remote: str = "remote",
):

    include_list = include.split(",") if include else []
    exclude_list = exclude.split(",") if exclude else []

    jobs = search_jobs(
        query=q,
        include_skills=include_list,
        exclude_skills=exclude_list,
        location=location,
        period=period,
        remote=remote
    )

    return {
        "total_jobs": len(jobs),
        "jobs": jobs,
        "summary": "Análise inicial do mercado baseada nas vagas encontradas",
        "skills": []
    }