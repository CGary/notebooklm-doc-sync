import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class TopicRule(BaseModel):
    path_prefix: str
    topic_slug: str
    section_priority: int = 100

class ProjectConfig(BaseModel):
    project_id: str
    name: str
    primary_domain: str
    user_agent: str
    contact_url: str
    rate_limit_per_host_rps: float = 1.0
    ssl_verify: bool = True
    request_timeout_seconds: int = 30
    max_retries: int = 3
    min_confidence: float = 0.70
    min_words: int = 100
    word_count_inflation_factor: float = 1.15
    container_target_words: int = 200000
    container_warm_words: int = 250000
    container_near_limit_words: int = 320000
    container_split_pending_words: int = 380000
    container_critical_words: int = 430000
    oversized_unit_words: int = 80000
    topic_rules: List[TopicRule] = []
    seed_urls: List[str] = []

def load_config(path: Path) -> ProjectConfig:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return ProjectConfig(**data)
