import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from .db import Database
from .config import ProjectConfig

class Assembler:
    def __init__(self, db: Database, config: ProjectConfig, output_dir: Path):
        self.db = db
        self.config = config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assemble_container(self, container_id: str) -> bool:
        """
        Ensambla un contenedor físico (.md). Retorna True si el archivo cambió.
        """
        with self.db.session() as conn:
            container = conn.execute("SELECT * FROM containers WHERE container_id = ?", (container_id,)).fetchone()
            # Quitar el filtro state != 'FAILED' para debuggear (aunque en prod es útil)
            sources = conn.execute(
                "SELECT * FROM sources WHERE container_id = ? ORDER BY url_normalized",
                (container_id,)
            ).fetchall()
            
            content_blocks = []
            total_words = 0
            
            for src in sources:
                markdown_path = Path(f"cache/markdown/{src['source_id']}.md")
                if not markdown_path.exists():
                    continue
                
                with open(markdown_path, 'r', encoding='utf-8') as f:
                    body = f.read()
                
                content_blocks.append(body)
                total_words += src['word_count']
            
            if not content_blocks:
                return False

            full_content = "\n\n---\n\n".join(content_blocks)
            new_hash = hashlib.sha256(full_content.encode('utf-8')).hexdigest()
            
            if new_hash == container['assembly_hash_sha256']:
                return False
            
            # Escribir archivo
            file_path = self.output_dir / container['file_name']
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            # Actualizar metadatos
            conn.execute(
                "UPDATE containers SET assembly_hash_sha256 = ?, current_words = ?, last_assembled_at = ? WHERE container_id = ?",
                (new_hash, total_words, datetime.utcnow().isoformat(), container_id)
            )
            return True

    def generate_manifest(self, run_id: str, containers_affected: List[str]):
        manifest = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "project_id": self.config.project_id,
            "actions_required": []
        }
        
        with self.db.session() as conn:
            for c_id in containers_affected:
                c = conn.execute("SELECT file_name, state FROM containers WHERE container_id = ?", (c_id,)).fetchone()
                manifest["actions_required"].append({
                    "file_name": c["file_name"],
                    "action": "REPLACE_IN_NOTEBOOKLM" if c["state"] != "ACTIVE" else "ADD_OR_REPLACE"
                })
        
        with open(self.output_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
