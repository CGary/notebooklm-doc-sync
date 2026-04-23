from typing import List, Optional
from .config import ProjectConfig, TopicRule
from .db import Database

class Bucketer:
    def __init__(self, db: Database, config: ProjectConfig):
        self.db = db
        self.config = config

    def resolve_topic(self, url: str) -> str:
        """
        Resuelve el tópico de una URL basado en las reglas del proyecto.
        Evaluación estricta: Coincidencia exacta o subdirectorio (para evitar colisiones de prefijo parcial).
        """
        from urllib.parse import urlparse
        path = urlparse(url).path.rstrip('/')
        if not path: path = "/"
        
        # Ordenar reglas por prioridad (orden definido en config)
        for rule in self.config.topic_rules:
            prefix = rule.path_prefix.rstrip('/')
            if not prefix: prefix = "/"
            
            # 1. Coincidencia exacta
            if path == prefix:
                return rule.topic_slug
            
            # 2. Coincidencia de subdirectorio (el prefijo debe terminar en / o el path debe seguir con /)
            if prefix != "/" and path.startswith(prefix + "/"):
                return rule.topic_slug
        
        return "otros"

    def assign_container(self, source_id: str, topic_slug: str) -> str:
        """
        Asigna o recupera un contenedor para una fuente, respetando límites.
        """
        with self.db.session() as conn:
            # 1. Buscar contenedor ACTIVE para este tópico
            container = conn.execute(
                "SELECT container_id, current_words FROM containers WHERE topic_slug = ? AND state = 'ACTIVE' ORDER BY volume_number DESC LIMIT 1",
                (topic_slug,)
            ).fetchone()
            
            if container:
                # Si el contenedor tiene espacio, usarlo
                if container['current_words'] < self.config.container_target_words:
                    return container['container_id']
                else:
                    # Marcar como WARM y crear uno nuevo
                    conn.execute("UPDATE containers SET state = 'WARM' WHERE container_id = ?", (container['container_id'],))
            
            # 2. Crear nuevo contenedor (Nuevo volumen)
            import uuid
            new_id = str(uuid.uuid4())
            last_vol = conn.execute(
                "SELECT MAX(volume_number) as last_vol FROM containers WHERE topic_slug = ?",
                (topic_slug,)
            ).fetchone()
            vol_num = (last_vol['last_vol'] or 0) + 1
            file_name = f"{self.config.project_id}_{topic_slug}_vol_{vol_num:02d}.md"
            
            conn.execute(
                "INSERT INTO containers (container_id, project_id, topic_slug, volume_number, file_name, state) VALUES (?, ?, ?, ?, ?, ?)",
                (new_id, self.config.project_id, topic_slug, vol_num, file_name, 'ACTIVE')
            )
            return new_id
