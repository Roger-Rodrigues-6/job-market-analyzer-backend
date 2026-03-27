"""
Adiciona colunas que existem nos models mas não na tabela (create_all não faz ALTER).

Uso (na pasta backend, com .env do banco carregado):
  python scripts/sync_mysql_schema.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from sqlalchemy import text

from database import engine


def _has_column(conn, table: str, column: str) -> bool:
    r = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
        ),
        {"t": table, "c": column},
    )
    return (r.scalar() or 0) > 0


def _has_index(conn, table: str, index_name: str) -> bool:
    r = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :n"
        ),
        {"t": table, "n": index_name},
    )
    return (r.scalar() or 0) > 0


def _has_table(conn, table: str) -> bool:
    r = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": table},
    )
    return (r.scalar() or 0) > 0


def _drop_column_if_exists(conn, table: str, column: str) -> None:
    if _has_column(conn, table, column):
        conn.execute(text(f"ALTER TABLE `{table}` DROP COLUMN `{column}`"))


def _drop_table_if_exists(conn, table: str) -> None:
    if _has_table(conn, table):
        conn.execute(text(f"DROP TABLE `{table}`"))


def main() -> None:
    with engine.begin() as conn:
        if not _has_table(conn, "searches"):
            conn.execute(
                text(
                    """
                    CREATE TABLE searches (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        role_id INT NOT NULL,
                        query VARCHAR(500) NOT NULL DEFAULT '',
                        location VARCHAR(255) NOT NULL DEFAULT '',
                        remote VARCHAR(50) NOT NULL DEFAULT '',
                        `period` VARCHAR(50) NOT NULL DEFAULT '24h',
                        english VARCHAR(50) NOT NULL DEFAULT 'include',
                        filters_hash VARCHAR(255) NULL,
                        ip VARCHAR(100) NOT NULL DEFAULT '',
                        user_agent VARCHAR(255) NOT NULL DEFAULT '',
                        created_at DATETIME NULL,
                        INDEX ix_searches_role_id (role_id),
                        INDEX ix_searches_filters_hash (filters_hash),
                        CONSTRAINT fk_searches_role FOREIGN KEY (role_id) REFERENCES roles (id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            )

        if not _has_table(conn, "search_skills"):
            conn.execute(
                text(
                    """
                    CREATE TABLE search_skills (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        search_id INT NOT NULL,
                        skill_id INT NOT NULL,
                        kind VARCHAR(10) NOT NULL,
                        CONSTRAINT uq_search_skill_kind UNIQUE (search_id, skill_id, kind),
                        INDEX ix_search_skills_search_id (search_id),
                        INDEX ix_search_skills_skill_id (skill_id),
                        CONSTRAINT fk_search_skills_search FOREIGN KEY (search_id)
                            REFERENCES searches (id) ON DELETE CASCADE,
                        CONSTRAINT fk_search_skills_skill FOREIGN KEY (skill_id)
                            REFERENCES skills (id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            )

        if not _has_table(conn, "search_excluded_companies"):
            conn.execute(
                text(
                    """
                    CREATE TABLE search_excluded_companies (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        search_id INT NOT NULL,
                        company_id INT NOT NULL,
                        CONSTRAINT uq_search_excluded_company UNIQUE (search_id, company_id),
                        INDEX ix_sec_search_id (search_id),
                        INDEX ix_sec_company_id (company_id),
                        CONSTRAINT fk_sec_search FOREIGN KEY (search_id)
                            REFERENCES searches (id) ON DELETE CASCADE,
                        CONSTRAINT fk_sec_company FOREIGN KEY (company_id)
                            REFERENCES companies (id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            )

        _drop_column_if_exists(conn, "searches", "include_skills")
        _drop_column_if_exists(conn, "searches", "exclude_skills")
        _drop_column_if_exists(conn, "searches", "exclude_companies")
        _drop_column_if_exists(conn, "search_logs", "include_skills")
        _drop_column_if_exists(conn, "search_logs", "exclude_skills")

        if not _has_column(conn, "search_logs", "search_id"):
            conn.execute(
                text(
                    """
                    ALTER TABLE search_logs
                    ADD COLUMN search_id INT NULL,
                    ADD INDEX ix_search_logs_search_id (search_id),
                    ADD CONSTRAINT fk_search_logs_search FOREIGN KEY (search_id) REFERENCES searches (id)
                    """
                )
            )

        if not _has_column(conn, "search_logs", "location"):
            conn.execute(
                text(
                    "ALTER TABLE search_logs ADD COLUMN location VARCHAR(255) NOT NULL DEFAULT ''"
                )
            )
        if not _has_column(conn, "search_logs", "remote"):
            conn.execute(
                text(
                    "ALTER TABLE search_logs ADD COLUMN remote VARCHAR(50) NOT NULL DEFAULT ''"
                )
            )
        if not _has_column(conn, "search_logs", "period"):
            conn.execute(
                text(
                    "ALTER TABLE search_logs ADD COLUMN `period` VARCHAR(50) NOT NULL DEFAULT ''"
                )
            )
        if not _has_column(conn, "search_logs", "include_skills"):
            conn.execute(
                text("ALTER TABLE search_logs ADD COLUMN include_skills TEXT NULL")
            )
        if not _has_column(conn, "search_logs", "exclude_skills"):
            conn.execute(
                text("ALTER TABLE search_logs ADD COLUMN exclude_skills TEXT NULL")
            )

        if not _has_column(conn, "market_snapshots", "report_date"):
            conn.execute(
                text("ALTER TABLE market_snapshots ADD COLUMN report_date DATE NULL")
            )
        if not _has_index(conn, "market_snapshots", "ix_market_snapshots_report_date"):
            conn.execute(
                text(
                    "CREATE INDEX ix_market_snapshots_report_date ON market_snapshots (report_date)"
                )
            )

        _drop_table_if_exists(conn, "search_skill_stats")

    print("Schema sincronizado.")


if __name__ == "__main__":
    main()
