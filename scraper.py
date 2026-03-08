import requests
from bs4 import BeautifulSoup
import re
import time

headers = {
    "User-Agent": "Mozilla/5.0"
}

# tecnologias que aumentam score
TECH_SCORE = {
    "php": 3,
    "laravel": 3,
    "node": 3,
    "node.js": 3,
    "javascript": 2,
    "typescript": 2,
    "angular": 2,
    "python": 2,
    "mysql": 1,
    "postgresql": 1,
}

# empresas ignoradas
EXCLUDE_COMPANIES = [
    "bairesdev",
    "turing",
    "toptal",
    "crossover"
]


# ============================
# CALCULAR SCORE
# ============================

def calculate_score(text, include_skills):

    text = text.lower()
    score = 0

    for tech, value in TECH_SCORE.items():
        if tech in text:
            score += value

    for skill in include_skills:
        if skill.lower() in text:
            score += 2

    return score


# ============================
# BUSCAR VAGAS
# ============================

def search_jobs(
    query="",
    include_skills=None,
    exclude_skills=None,
    location="Brazil",
    period="24h",
    remote="remote"
):

    if include_skills is None:
        include_skills = []

    if exclude_skills is None:
        exclude_skills = []

    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    jobs = {}

    pages = 3

    for page in range(pages):

        params = {
            "keywords": query,
            "location": location,
            "start": page * 25
        }

        # filtro tempo
        if period == "24h":
            params["f_TPR"] = "r86400"
        elif period == "7d":
            params["f_TPR"] = "r604800"

        # filtro remoto
        if remote == "remote":
            params["f_WT"] = "2"
        elif remote == "hybrid":
            params["f_WT"] = "3"
        elif remote == "onsite":
            params["f_WT"] = "1"

        r = requests.get(base_url, params=params, headers=headers)

        soup = BeautifulSoup(r.text, "html.parser")

        listings = soup.find_all("li")

        for job in listings:

            title_tag = job.find("h3")
            company_tag = job.find("h4")
            link_tag = job.find("a")

            if not title_tag or not link_tag:
                continue

            title = title_tag.text.strip()
            title_lower = title.lower()

            link = link_tag["href"]

            company = ""
            if company_tag:
                company = company_tag.text.strip()

            company_lower = company.lower()

            # filtrar empresas
            if any(c in company_lower for c in EXCLUDE_COMPANIES):
                continue

            # id da vaga
            job_id_match = re.search(r"\d+", link)

            if not job_id_match:
                continue

            job_id = job_id_match.group()

            # excluir tecnologias
            if any(skill.lower() in title_lower for skill in exclude_skills):
                continue

            score = calculate_score(title, include_skills)

            jobs[job_id] = {
                "id": job_id,
                "title": title,
                "company": company,
                "link": link,
                "score": score
            }

        time.sleep(0.3)

    return list(jobs.values())