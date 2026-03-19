import requests
from bs4 import BeautifulSoup
import re
import time

headers = {
    "User-Agent": "Mozilla/5.0"
}

def load_english_words():
    words = []
    try:
        with open("english_words.txt", "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    words.append(word)
    except:
        pass
    return words


ENGLISH_WORDS = load_english_words()

def detect_english(text):
    count = 0
    for word in ENGLISH_WORDS:
        if word in text:
            count += 1
    return count

def normalize_text(text):
    text = text.lower()
    text = text.replace(",", " ")
    text = text.replace("/", " ")
    text = text.replace("|", " ")
    return text


def contains_skill(text, skill):
    return re.search(rf"\b{re.escape(skill.lower())}\b", text)


def extract_skills(text, skills_list):
    found = []
    for skill in skills_list:
        if contains_skill(text, skill):
            found.append(skill)
    return found


def get_job_description(job_id):
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    try:
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            return ""

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
    remote,
    english
):

    if not location:
        location = "Brazil"

    if not period:
        period = "24h"

    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    jobs = {}
    pages = 2

    ALL_KNOWN_SKILLS = list(set(include_skills + exclude_skills))

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

        if r.status_code != 200:
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
            link = link_tag.get("href", "")

            if not link:
                continue

            company = company_tag.text.strip() if company_tag else ""

            company_lower = company.lower()
            if any(c.lower() in company_lower for c in exclude_companies):
                continue

            job_id_match = re.search(r"\d+", link)
            if not job_id_match:
                continue

            job_id = job_id_match.group()

            if job_id in jobs:
                continue

            desc = get_job_description(job_id)

            text = normalize_text(f"{title} {desc}")

            english_score = detect_english(text)

            if english == "only" and english_score < 2:
                continue

            if english == "exclude" and english_score >= 2:
                continue

            if any(contains_skill(text, skill) for skill in exclude_skills):
                continue

            matched_skills = extract_skills(text, include_skills)
            all_skills = extract_skills(text, ALL_KNOWN_SKILLS)

            if include_skills:
                match_percentage = (len(matched_skills) / len(include_skills)) * 100
            else:
                match_percentage = 0

            jobs[job_id] = {
                "external_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "job_url": link,
                "description": desc,
                "matched_skills": matched_skills,
                "all_skills": all_skills,
                "match_count": len(matched_skills),
                "match_percentage": round(match_percentage, 1),
                "is_remote": remote == "remote",
                "is_english": english_score >= 2,
                "posted_at": None
            }

        time.sleep(0.3)

    jobs_list = list(jobs.values())
    jobs_list.sort(
        key=lambda x: (x["match_percentage"], x["match_count"]),
        reverse=True
    )

    return jobs_list