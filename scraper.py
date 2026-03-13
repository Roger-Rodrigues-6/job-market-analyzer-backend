import requests
from bs4 import BeautifulSoup
import re
import time

headers = {
    "User-Agent": "Mozilla/5.0"
}


def get_job_description(job_id):

    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    try:

        r = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        desc = soup.find("div", class_="show-more-less-html__markup")

        if desc:
            return desc.get_text(" ").strip()

    except:
        pass

    return ""


def search_jobs(
    query,
    include_skills,
    exclude_skills,
    exclude_companies,
    location,
    period,
    remote
):

    if not location:
        location = "Brazil"

    if not period:
        period = "24h"

    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    jobs = {}

    pages = 2

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

            r = requests.get(base_url, params=params, headers=headers, timeout=10)

        except:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        listings = soup.find_all("li")

        for job in listings:

            title_tag = job.find("h3")
            company_tag = job.find("h4")
            link_tag = job.find("a")

            if not title_tag or not link_tag:
                continue

            title = title_tag.text.strip()

            link = link_tag["href"]

            company = ""

            if company_tag:
                company = company_tag.text.strip()

            company_lower = company.lower()

            if any(c.lower() in company_lower for c in exclude_companies):
                continue

            job_id_match = re.search(r"\d+", link)

            if not job_id_match:
                continue

            job_id = job_id_match.group()

            desc = get_job_description(job_id)

            text = f"{title} {desc}".lower()

            if any(skill.lower() in text for skill in exclude_skills):
                continue

            matched_skills = []

            for skill in include_skills:

                if skill.lower() in text:
                    matched_skills.append(skill)

            match_count = len(matched_skills)

            jobs[job_id] = {
                "id": job_id,
                "title": title,
                "company": company,
                "link": link,
                "description": desc,
                "matched_skills": matched_skills,
                "match_count": match_count
            }

        time.sleep(0.3)

    jobs_list = list(jobs.values())

    jobs_list.sort(key=lambda x: x["match_count"], reverse=True)

    return jobs_list