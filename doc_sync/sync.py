import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from .db import Database
from .fetch import Fetcher
from .extract import Extractor
from .normalize import Normalizer
from .config import ProjectConfig

class SyncEngine:
    def __init__(self, db: Database, config: ProjectConfig):
        self.db = db
        self.config = config
        self.fetcher = Fetcher(config)
        self.extractor = Extractor(config)
        self.normalizer = Normalizer(config.word_count_inflation_factor)

    def process_url(self, url: str, project_id: str):
        """
        Procesa una única URL: fetch, extract, hash y update DB.
        """
        # 1. Obtener estado previo de la DB
        source_data = self._get_source_state(url, project_id)
        etag = source_data.get('http_etag') if source_data else None
        
        # 2. Verificar robots.txt
        if not self.fetcher.can_fetch(url):
            self._update_source_state(url, project_id, state='BLOCKED_BY_ROBOTS')
            return

        try:
            # 3. HTTP Fetch
            response = self.fetcher.fetch(url, etag=etag)
            
            if response.status_code == 304:
                self._update_source_state(url, project_id, state='UNCHANGED')
                return
            
            if response.status_code != 200:
                self._update_source_state(url, project_id, state='FAILED', error_code=f'HTTP_{response.status_code}')
                return

            # 4. Extraction
            html = response.text
            markdown, confidence = self.extractor.extract(html)
            
            # En modo YOLO, si no hay markdown, usamos un placeholder para debug
            if not markdown:
                markdown = f"# Error de Extracción\nURL: {url}\nContenido no detectado semánticamente."
                state = 'FAILED'
            else:
                state = 'CHANGED' if self.normalizer.compute_hash(markdown) != (source_data.get('content_hash_sha256') if source_data else None) else 'UNCHANGED'

            # 5. Normalization & Hashing
            new_hash = self.normalizer.compute_hash(markdown)
            word_count = self.normalizer.estimate_word_count(markdown)
            
            # 6. Update DB e Save Markdown
            source_id = source_data.get('source_id') or str(uuid.uuid4())
            markdown_path = Path(f"cache/markdown/{source_id}.md")
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(markdown)

            self._update_source_state(
                url, project_id, 
                source_id=source_id,
                state=state, 
                content_hash=new_hash, 
                word_count=word_count,
                etag=response.headers.get('ETag')
            )

        except Exception as e:
            self._update_source_state(url, project_id, state='FAILED', error_code='EXCEPTION')

    def _get_source_state(self, url: str, project_id: str):
        with self.db.session() as conn:
            row = conn.execute(
                "SELECT * FROM sources WHERE url_original = ? AND project_id = ?", 
                (url, project_id)
            ).fetchone()
            return dict(row) if row else {}

    def _update_source_state(self, url: str, project_id: str, state: str, **kwargs):
        with self.db.session() as conn:
            source_id = kwargs.get('source_id') or str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            # Usar INSERT OR REPLACE para un upsert real en SQLite
            conn.execute("""
                INSERT INTO sources (
                    source_id, project_id, url_original, url_normalized, 
                    state, content_hash_sha256, word_count, http_etag, 
                    last_error_code, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url_original) DO UPDATE SET
                    state = excluded.state,
                    content_hash_sha256 = excluded.content_hash_sha256,
                    word_count = excluded.word_count,
                    http_etag = excluded.http_etag,
                    last_error_code = excluded.last_error_code,
                    updated_at = excluded.updated_at
            """, (
                source_id, project_id, url, url, state, 
                kwargs.get('content_hash'), kwargs.get('word_count', 0),
                kwargs.get('etag'), kwargs.get('error_code'), now, now
            ))
