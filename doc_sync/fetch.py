import httpx
import time
from typing import Optional, Dict
from urllib.robotparser import RobotFileParser
from .config import ProjectConfig

class Fetcher:
    def __init__(self, config: ProjectConfig):
        self.config = config
        self.client = httpx.Client(
            headers={"User-Agent": config.user_agent},
            verify=config.ssl_verify,
            timeout=config.request_timeout_seconds
        )
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.last_request_time: Dict[str, float] = {}

    def _get_robots(self, url: str) -> RobotFileParser:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if base_url not in self.robots_cache:
            rp = RobotFileParser()
            try:
                response = self.client.get(f"{base_url}/robots.txt")
                if response.status_code == 200:
                    rp.parse(response.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception:
                rp.allow_all = True
            self.robots_cache[base_url] = rp
        return self.robots_cache[base_url]

    def can_fetch(self, url: str) -> bool:
        rp = self._get_robots(url)
        return rp.can_fetch(self.config.user_agent, url)

    def fetch(self, url: str, etag: Optional[str] = None) -> httpx.Response:
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        
        # Simple rate limiting
        now = time.time()
        if host in self.last_request_time:
            elapsed = now - self.last_request_time[host]
            wait = (1.0 / self.config.rate_limit_per_host_rps) - elapsed
            if wait > 0:
                time.sleep(wait)
        
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
            
        # IMPORTANTE: Usar verify=self.config.ssl_verify para permitir sitios con certificados inválidos
        response = self.client.get(url, headers=headers, follow_redirects=True)
        self.last_request_time[host] = time.time()
        return response

    def close(self):
        self.client.close()
