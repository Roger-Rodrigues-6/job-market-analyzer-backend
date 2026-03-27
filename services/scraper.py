import requests
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0"
}


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[,\|/]", " ", text)
    return text


def contains_skill(text, skill):
    return re.search(rf"\b{re.escape(skill.lower())}\b", text)


def extract_skills(text, skills_list):
    return [s for s in skills_list if contains_skill(text, s)]


def search_jobs(
    query,
    include_skills,
    exclude_skills,
    exclude_companies,
    location,
    period,
    remote,
    english
):

    if not location:
        location = "Brazil"

    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    jobs = {}
    pages = 1

    ALL_SKILLS = list(set(include_skills + exclude_skills))

    for page in range(pages):

        params = {
            "keywords": query,
            "location": location,
            "start": page * 25
        }

        if period == "24h":
            params["f_TPR"] = "r86400"
        elif period == "7d":
            params["f_TPR"] = "r604800"

        if remote == "remote":
            params["f_WT"] = "2"
        elif remote == "hybrid":
            params["f_WT"] = "3"
        elif remote == "onsite":
            params["f_WT"] = "1"

        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=5)
        except:
            continue

        if r.status_code != 200:
            continue

        soup = BeautifulSoup(r.text, "lxml")
        listings = soup.find_all("li")

        for job in listings:

            title_tag = job.find("h3")
            company_tag = job.find("h4")
            link_tag = job.find("a")

            if not title_tag or not link_tag:
                continue

            title = title_tag.text.strip()
            link = link_tag.get("href", "")

            if not link:
                continue

            company = company_tag.text.strip() if company_tag else ""

            if any(c.lower() in company.lower() for c in exclude_companies):
                continue

            job_id_match = re.search(r"\d+", link)
            if not job_id_match:
                continue

            job_id = job_id_match.group()

            if job_id in jobs:
                continue

            text = normalize_text(title)

            if any(contains_skill(text, skill) for skill in exclude_skills):
                continue

            matched = extract_skills(text, include_skills)
            all_skills = extract_skills(text, ALL_SKILLS)

            jobs[job_id] = {
                "external_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "job_url": link,
                "description": "",
                "matched_skills": matched,
                "all_skills": all_skills,
                "match_count": len(matched),
                "match_percentage": (len(matched) / len(include_skills) * 100) if include_skills else 0,
                "is_remote": remote == "remote",
                "is_english": False,
                "posted_at": None
            }

    jobs_list = list(jobs.values())

    jobs_list.sort(
        key=lambda x: (x["match_percentage"], x["match_count"]),
        reverse=True
    )

    return jobs_list