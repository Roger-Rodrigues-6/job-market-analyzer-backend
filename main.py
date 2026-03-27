from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from collections import Counter
import hashlib

from database import get_db, init_db
from services.scraper import search_jobs
from services.save_jobs import normalize, save_jobs
from models.role import Role
from models.skill import Skill
from models.company import Company
from models.search import Search
from models.search_log import SearchLog
from models.search_skill_link import SearchSkillLink
from models.search_excluded_company import SearchExcludedCompany

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


def generate_hash(text: str):
    return hashlib.md5(text.encode()).hexdigest()


def _as_csv(value: str | list) -> str:
    """Query params repetidos ou JSON podem vir como lista; o model grava string CSV."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ",".join(str(x).strip() for x in value if str(x).strip())
    return str(value)


def ensure_skills_from_filters(db: Session, include_skills: list[str], exclude_skills: list[str]) -> None:
    """Garante uma linha em `skills` para cada skill citada em include/exclude (nome normalizado)."""
    names = {normalize(s) for s in include_skills + exclude_skills if normalize(s)}
    for name in names:
        if db.query(Skill).filter(Skill.name == name).first():
            continue
        db.add(Skill(name=name[:100]))


def get_or_create_company(db: Session, raw: str) -> Company | None:
    name = normalize(raw)
    if not name:
        return None
    name = name[:255]
    row = db.query(Company).filter(Company.name == name).first()
    if row:
        return row
    row = Company(name=name)
    db.add(row)
    db.flush()
    return row


def _link_search_skills(
    db: Session,
    search_id: int,
    include_skills: list[str],
    exclude_skills: list[str],
) -> None:
    seen_inc: set[int] = set()
    for raw in include_skills:
        n = normalize(raw)
        if not n:
            continue
        skill = db.query(Skill).filter(Skill.name == n).first()
        if not skill or skill.id in seen_inc:
            continue
        seen_inc.add(skill.id)
        db.add(SearchSkillLink(search_id=search_id, skill_id=skill.id, kind="include"))
    seen_exc: set[int] = set()
    for raw in exclude_skills:
        n = normalize(raw)
        if not n:
            continue
        skill = db.query(Skill).filter(Skill.name == n).first()
        if not skill or skill.id in seen_exc:
            continue
        seen_exc.add(skill.id)
        db.add(SearchSkillLink(search_id=search_id, skill_id=skill.id, kind="exclude"))


def _link_search_excluded_companies(
    db: Session, search_id: int, exclude_companies_list: list[str]
) -> None:
    seen: set[int] = set()
    for raw in exclude_companies_list:
        company = get_or_create_company(db, raw)
        if not company or company.id in seen:
            continue
        seen.add(company.id)
        db.add(SearchExcludedCompany(search_id=search_id, company_id=company.id))


@app.get("/search")
def search(
    request: Request,
    q: str = "",
    include: str = "",
    exclude: str = "",
    exclude_companies: str = "",
    location: str = "",
    period: str = "24h",
    remote: str = "",
    english: str = "include",
    db: Session = Depends(get_db)
):

    include_skills = [s.strip() for s in _as_csv(include).split(",") if s.strip()]
    exclude_skills = [s.strip() for s in _as_csv(exclude).split(",") if s.strip()]
    exclude_companies_csv = _as_csv(exclude_companies)
    exclude_companies_list = [
        s.strip() for s in exclude_companies_csv.split(",") if s.strip()
    ]

    jobs = search_jobs(
        query=q,
        include_skills=include_skills,
        exclude_skills=exclude_skills,
        exclude_companies=exclude_companies_list,
        location=location,
        period=period,
        remote=remote,
        english=english
    )

    # ===== ROLE =====
    role_name = (q or "").lower().strip()

    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        db.add(role)
        db.flush()

    ensure_skills_from_filters(db, include_skills, exclude_skills)

    # ===== SEARCH (formulário → raspagem) + LOG =====
    search_hash = generate_hash(
        f"{q}|{include}|{exclude}|{exclude_companies_csv}|{location}|{remote}|{period}|{english}"
    )

    search_row = Search(
        role_id=role.id,
        query=q,
        location=location,
        remote=remote,
        period=period,
        english=english,
        filters_hash=search_hash,
        ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add(search_row)
    db.flush()

    _link_search_skills(db, search_row.id, include_skills, exclude_skills)
    _link_search_excluded_companies(db, search_row.id, exclude_companies_list)

    db.add(SearchLog(
        role_id=role.id,
        search_id=search_row.id,
        filters_hash=search_hash,
        location=location,
        remote=remote,
        period=period,
        ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", "")
    ))

    # ===== SAVE JOBS + SKILLS =====
    saved_count = save_jobs(db, jobs, role.id)

    # ===== SUMMARY =====
    skills_counter = Counter()

    for job in jobs:
        for skill in job.get("matched_skills", []):
            skills_counter[skill] += 1

    top_skills = [
        {"name": skill, "count": count}
        for skill, count in skills_counter.most_common(10)
    ]

    summary = (
        f"Foram analisadas {len(jobs)} vagas. "
        "As habilidades mais presentes foram: "
        + ", ".join([s["name"] for s in top_skills[:5]])
    )

    db.commit()

    return {
        "total_jobs": len(jobs),
        "saved_jobs": saved_count,
        "jobs": jobs,
        "skills": top_skills,
        "summary": summary
    }