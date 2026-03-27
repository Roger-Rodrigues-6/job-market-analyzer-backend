from __future__ import annotations

"""
Agregação diária (D−1): pensado para rodar ~1h da manhã no fuso STATS_TIMEZONE,
fechando o dia civil anterior (até a meia-noite local).

No Render (cron em UTC), 01:00 em São Paulo (UTC−3) ≈ 04:00 UTC:
  Schedule: 0 4 * * *
  Command:  python -m services.daily_stats
"""

import os
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import SessionLocal, init_db
from models.job import Job
from models.job_skill import JobSkill
from models.market_snapshot import MarketSnapshot
from models.market_snapshot_skill import MarketSnapshotSkill

DAILY_JOBS_PERIOD = "daily_jobs"
DAILY_JOBS_LOCATION = "*"
DAILY_JOBS_REMOTE = "*"


def _stats_timezone() -> str:
    return os.getenv("STATS_TIMEZONE", "America/Sao_Paulo")


def _day_bounds_naive_utc(report_date: date, tz_name: str) -> tuple[datetime, datetime]:
    """Intervalo [início, fim) em UTC naive, alinhado ao dia civil em `tz_name`."""
    tz = ZoneInfo(tz_name)
    start_local = datetime.combine(report_date, time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


def aggregate_for_date(db: Session, report_date: date) -> dict:
    removed = _clear_existing_for_date(db, report_date)
    snap_rows = _aggregate_market_from_jobs(db, report_date)
    db.commit()
    return {
        "report_date": report_date.isoformat(),
        "cleared_rows": removed,
        "market_snapshot_rows": snap_rows,
    }


def _clear_existing_for_date(db: Session, report_date: date) -> dict:
    snap_ids = [
        r[0]
        for r in db.query(MarketSnapshot.id)
        .filter(MarketSnapshot.report_date == report_date)
        .all()
    ]
    mss_deleted = 0
    if snap_ids:
        mss_deleted = (
            db.query(MarketSnapshotSkill)
            .filter(MarketSnapshotSkill.snapshot_id.in_(snap_ids))
            .delete(synchronize_session=False)
        )
    ms_deleted = (
        db.query(MarketSnapshot).filter(MarketSnapshot.report_date == report_date).delete()
    )

    return {
        "market_snapshot_skills": mss_deleted,
        "market_snapshots": ms_deleted,
    }


def _aggregate_market_from_jobs(db: Session, report_date: date) -> int:
    start_utc, end_utc = _day_bounds_naive_utc(report_date, _stats_timezone())
    role_ids = [
        r[0]
        for r in db.query(Job.role_id)
        .filter(
            Job.collected_at >= start_utc,
            Job.collected_at < end_utc,
        )
        .distinct()
        .all()
    ]

    n_snapshots = 0
    for role_id in role_ids:
        if role_id is None:
            continue

        job_ids = [
            r[0]
            for r in db.query(Job.id)
            .filter(
                Job.role_id == role_id,
                Job.collected_at >= start_utc,
                Job.collected_at < end_utc,
            )
            .all()
        ]
        if not job_ids:
            continue

        total = len(job_ids)

        snap = MarketSnapshot(
            role_id=role_id,
            location=DAILY_JOBS_LOCATION,
            remote=DAILY_JOBS_REMOTE,
            period=DAILY_JOBS_PERIOD,
            total_jobs=total,
            report_date=report_date,
            created_at=datetime.utcnow(),
        )
        db.add(snap)
        db.flush()

        rows = (
            db.query(JobSkill.skill_id, func.count(JobSkill.id))
            .filter(JobSkill.job_id.in_(job_ids))
            .group_by(JobSkill.skill_id)
            .all()
        )
        for skill_id, cnt in rows:
            db.add(
                MarketSnapshotSkill(
                    snapshot_id=snap.id,
                    skill_id=skill_id,
                    count=int(cnt),
                )
            )
        n_snapshots += 1

    return n_snapshots


def resolve_report_date() -> date:
    override = os.getenv("STATS_REPORT_DATE", "").strip()
    if override:
        return date.fromisoformat(override)
    # Ontem no fuso de stats: se o job roda ~1h após a meia-noite local, isso é o dia que acabou de fechar.
    tz = ZoneInfo(_stats_timezone())
    today_local = datetime.now(tz).date()
    return today_local - timedelta(days=1)


def run() -> dict:
    init_db()
    report_date = resolve_report_date()
    db = SessionLocal()
    try:
        return aggregate_for_date(db, report_date)
    finally:
        db.close()


if __name__ == "__main__":
    import json

    print(json.dumps(run(), indent=2, default=str))
