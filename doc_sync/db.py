import sqlite3
from pathlib import Path
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            
            # Projects
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    primary_domain TEXT,
                    user_agent TEXT NOT NULL,
                    contact_url TEXT NOT NULL,
                    rate_limit_per_host_rps REAL NOT NULL DEFAULT 1.0,
                    word_count_inflation_factor REAL NOT NULL DEFAULT 1.15,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Topic Rules
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topic_rules (
                    rule_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    rule_order INTEGER NOT NULL,
                    path_prefix TEXT NOT NULL,
                    topic_slug TEXT NOT NULL,
                    section_priority INTEGER NOT NULL DEFAULT 100,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
            """)

            # Containers
            conn.execute("""
                CREATE TABLE IF NOT EXISTS containers (
                    container_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    topic_slug TEXT NOT NULL,
                    volume_number INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'ACTIVE',
                    current_words INTEGER NOT NULL DEFAULT 0,
                    assembly_hash_sha256 TEXT,
                    last_assembled_at DATETIME,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
            """)

            # Sources
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    container_id TEXT,
                    url_original TEXT NOT NULL UNIQUE,
                    url_normalized TEXT NOT NULL,
                    url_final TEXT,
                    canonical_url TEXT,
                    topic_slug TEXT,
                    state TEXT NOT NULL DEFAULT 'ACTIVE',
                    http_etag TEXT,
                    content_hash_sha256 TEXT,
                    word_count INTEGER NOT NULL DEFAULT 0,
                    last_success_at DATETIME,
                    last_error_code TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id),
                    FOREIGN KEY (container_id) REFERENCES containers(container_id)
                )
            """)

            # Runs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    project_id TEXT,
                    state TEXT NOT NULL,
                    urls_processed INTEGER DEFAULT 0,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    finished_at DATETIME,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
            """)
            conn.commit()

    @contextmanager
    def session(self):
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
