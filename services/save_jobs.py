import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import select

from models.company import Company
from models.job import Job
from models.skill import Skill
from models.job_skill import JobSkill


def normalize(text):
    return (text or "").lower().strip()


def _job_hash(title: str, company: str, location: str) -> str:
    raw = f"{title}|{company}|{location}".lower()
    return hashlib.md5(raw.encode()).hexdigest()


def save_jobs(db: Session, jobs_data: list, role_id: int):

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

    new_companies = [
        Company(name=name) for name in company_names if name not in company_cache
    ]

    db.add_all(new_companies)
    db.flush()

    for c in new_companies:
        company_cache[c.name] = c

    all_skills_set = set()

    for job in jobs_data:
        all_skills_set.update(job.get("all_skills", []))

    existing_skills = db.execute(
        select(Skill).where(Skill.name.in_(all_skills_set))
    ).scalars().all()

    for s in existing_skills:
        skill_cache[s.name] = s

    new_skills = [
        Skill(name=normalize(name))
        for name in all_skills_set
        if normalize(name) not in skill_cache
    ]

    db.add_all(new_skills)
    db.flush()

    for s in new_skills:
        skill_cache[s.name] = s

    # =============================
    # JOBS (SEM FLUSH NO LOOP)
    # =============================

    jobs_to_insert = []
    job_skill_map = []

    for job in jobs_data:

        if job["external_id"] in existing_jobs:
            continue

        company_obj = company_cache.get(job["company"])

        db_job = Job(
            job_hash=_job_hash(
                job.get("title") or "",
                job.get("company") or "",
                job.get("location") or "",
            ),
            external_id=job["external_id"],
            role_id=role_id,
            title=job["title"],
            location=job.get("location"),
            is_remote=job.get("is_remote"),
            job_url=job.get("job_url"),
            posted_at=job.get("posted_at"),
            company_id=company_obj.id if company_obj else None
        )

        jobs_to_insert.append((db_job, job))

    db.add_all([j[0] for j in jobs_to_insert])
    db.flush()

    # =============================
    # JOB SKILLS (BATCH)
    # =============================

    job_skills_to_insert = []

    for db_job, job in jobs_to_insert:

        for skill_name in job.get("all_skills", []):
            skill_obj = skill_cache.get(normalize(skill_name))

            if skill_obj:
                job_skills_to_insert.append({
                    "job_id": db_job.id,
                    "skill_id": skill_obj.id
                })

    if job_skills_to_insert:
        db.bulk_insert_mappings(JobSkill, job_skills_to_insert)

    return len(jobs_to_insert)