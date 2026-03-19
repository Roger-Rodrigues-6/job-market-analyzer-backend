from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
import hashlib

from models.role import Role
from models.skill import Skill
from models.company import Company
from models.market_snapshot import MarketSnapshot
from models.market_snapshot_skill import MarketSnapshotSkill
from models.search_skill_stat import SearchSkillStat
from models.search_log import SearchLog
from models.job import Job
from models.job_skill import JobSkill


# =============================
# HELPERS
# =============================

def normalize(text: str):
    return (text or "").strip().lower()


def generate_hash(text: str):
    return hashlib.md5(text.encode()).hexdigest()


def generate_job_hash(title: str, company: str, location: str):
    raw = f"{title}|{company}|{location}".lower()
    return generate_hash(raw)


def generate_search_hash(data: dict):
    raw = "|".join([str(v) for v in data.values()])
    return generate_hash(raw)


def get_or_create_role(db: Session, name: str):
    name = normalize(name)

    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        role = Role(name=name)
        db.add(role)
        db.commit()
        db.refresh(role)

    return role


def get_or_create_skill(db: Session, name: str):
    name = normalize(name)

    skill = db.query(Skill).filter(Skill.name == name).first()
    if not skill:
        skill = Skill(name=name)
        db.add(skill)
        db.commit()
        db.refresh(skill)

    return skill


def get_or_create_company(db: Session, name: str):
    name = normalize(name)

    company = db.query(Company).filter(Company.name == name).first()
    if not company:
        company = Company(name=name)
        db.add(company)
        db.commit()
        db.refresh(company)

    return company


# =============================
# FUNÇÃO PRINCIPAL
# =============================

def process_market_data(
    db: Session,
    query: str,
    include_skills: list[str],
    exclude_skills: list[str],
    jobs_data: list[dict],
    location: str,
    remote: str,
    period: str,
    ip: str,
    user_agent: str
):

    search_hash = generate_search_hash({
        "query": query,
        "include": ",".join(include_skills),
        "exclude": ",".join(exclude_skills),
        "location": location,
        "remote": remote,
        "period": period
    })

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    existing_search = db.query(SearchLog).filter(
        SearchLog.filters_hash == search_hash,
        SearchLog.ip == ip,
        SearchLog.created_at >= one_hour_ago
    ).first()

    if existing_search:
        print("Busca ignorada (duplicada recente)")
        return

    role = get_or_create_role(db, query)

    today = date.today()

    for skill_name in include_skills:
        skill = get_or_create_skill(db, skill_name)

        stat = db.query(SearchSkillStat).filter_by(
            role_id=role.id,
            skill_id=skill.id,
            type="include",
            date=today
        ).first()

        if stat:
            stat.count += 1
        else:
            db.add(SearchSkillStat(
                role_id=role.id,
                skill_id=skill.id,
                type="include",
                count=1,
                date=today
            ))

    for skill_name in exclude_skills:
        skill = get_or_create_skill(db, skill_name)

        stat = db.query(SearchSkillStat).filter_by(
            role_id=role.id,
            skill_id=skill.id,
            type="exclude",
            date=today
        ).first()

        if stat:
            stat.count += 1
        else:
            db.add(SearchSkillStat(
                role_id=role.id,
                skill_id=skill.id,
                type="exclude",
                count=1,
                date=today
            ))

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    snapshot = db.query(MarketSnapshot).filter(
        MarketSnapshot.role_id == role.id,
        MarketSnapshot.location == location,
        MarketSnapshot.remote == remote,
        MarketSnapshot.period == period,
        MarketSnapshot.created_at >= today_start
    ).first()

    if snapshot:
        snapshot.total_jobs += len(jobs_data)
        snapshot.search_count += 1
    else:
        snapshot = MarketSnapshot(
            role_id=role.id,
            location=location,
            remote=remote,
            period=period,
            total_jobs=len(jobs_data),
            search_count=1,
            created_at=datetime.utcnow()
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

    skill_counter = {}

    for job_data in jobs_data:

        title = job_data.get("title", "")
        company_name = job_data.get("company", "")
        link = job_data.get("link", "")
        description = job_data.get("description", "")
        external_id = job_data.get("id")

        is_remote = remote == "remote"

        posted_at = None  

        job_hash = generate_job_hash(title, company_name, location)

        job = db.query(Job).filter_by(job_hash=job_hash).first()

        if not job:
            company = get_or_create_company(db, company_name)

            job = Job(
                job_hash=job_hash,
                external_id=external_id,
                role_id=role.id,
                company_id=company.id,
                title=title,
                location=location,
                is_remote=is_remote,
                job_url=link,
                posted_at=posted_at
            )

            db.add(job)
            db.commit()
            db.refresh(job)

        text = f"{title} {description}".lower()

        for skill_name in include_skills:

            if skill_name.lower() in text:

                skill = get_or_create_skill(db, skill_name)

                skill_counter[skill.id] = skill_counter.get(skill.id, 0) + 1

                exists = db.query(JobSkill).filter_by(
                    job_id=job.id,
                    skill_id=skill.id
                ).first()

                if not exists:
                    db.add(JobSkill(
                        job_id=job.id,
                        skill_id=skill.id
                    ))

    for skill_id, count in skill_counter.items():

        existing = db.query(MarketSnapshotSkill).filter_by(
            snapshot_id=snapshot.id,
            skill_id=skill_id
        ).first()

        if existing:
            existing.count += count
        else:
            db.add(MarketSnapshotSkill(
                snapshot_id=snapshot.id,
                skill_id=skill_id,
                count=count
            ))

    db.add(SearchLog(
        role_id=role.id,
        filters_hash=search_hash,
        ip=ip,
        user_agent=user_agent
    ))

    db.commit()

    print("Pipeline completa executada 🚀")