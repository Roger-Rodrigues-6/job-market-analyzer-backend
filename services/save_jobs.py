from sqlalchemy.orm import Session
from sqlalchemy import select

from models.company import Company
from models.job import Job
from models.skill import Skill


def save_jobs(db: Session, jobs_data: list):

    if not jobs_data:
        return 0

    external_ids = [job["external_id"] for job in jobs_data]

    existing = db.execute(
        select(Job.external_id).where(Job.external_id.in_(external_ids))
    ).fetchall()

    existing_jobs = {e[0] for e in existing}

    company_cache = {}
    skill_cache = {}

    company_names = list({job["company"] for job in jobs_data if job["company"]})

    existing_companies = db.execute(
        select(Company).where(Company.name.in_(company_names))
    ).scalars().all()

    for c in existing_companies:
        company_cache[c.name] = c

    new_companies = []
    for name in company_names:
        if name not in company_cache:
            new_companies.append(Company(name=name))

    db.add_all(new_companies)
    db.flush()

    for c in new_companies:
        company_cache[c.name] = c

    all_skills_set = set()

    for job in jobs_data:
        all_skills_set.update(job.get("all_skills", []))

    if all_skills_set:

        existing_skills = db.execute(
            select(Skill).where(Skill.name.in_(all_skills_set))
        ).scalars().all()

        for s in existing_skills:
            skill_cache[s.name] = s

        new_skills = []
        for name in all_skills_set:
            name = name.lower().strip()

            if name not in skill_cache:
                new_skills.append(Skill(name=name))

        db.add_all(new_skills)
        db.flush()

        for s in new_skills:
            skill_cache[s.name] = s

    saved_count = 0

    for job in jobs_data:

        if job["external_id"] in existing_jobs:
            continue

        company_obj = company_cache.get(job["company"])

        db_job = Job(
            external_id=job["external_id"],
            title=job["title"],
            location=job.get("location"),
            is_remote=job.get("is_remote"),
            job_url=job.get("job_url"),
            posted_at=job.get("posted_at"),
            match_percentage=job.get("match_percentage", 0)
        )

        if company_obj:
            db_job.company_id = company_obj.id
        for skill_name in job.get("all_skills", []):
            skill_obj = skill_cache.get(skill_name.lower().strip())

        db.add(db_job)

        saved_count += 1

    db.commit()

    return saved_count