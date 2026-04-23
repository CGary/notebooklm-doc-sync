import trafilatura
from selectolax.lexbor import LexborHTMLParser
from markdownify import markdownify as md
from typing import Optional, List, Tuple
from .config import ProjectConfig

class Extractor:
    def __init__(self, config: ProjectConfig):
        self.config = config

    def extract(self, html: str, include_selector: Optional[str] = None, exclude_selectors: Optional[List[str]] = None) -> Tuple[Optional[str], float]:
        """
        Extrae el contenido semántico del HTML con alta fidelidad para tablas.
        Usa Selectolax para limpieza y Markdownify para conversión.
        """
        parser = LexborHTMLParser(html)
        
        # 1. Limpieza agresiva de ruido
        noise = [
            'script', 'style', 'nav', 'footer', 'header', 'aside', 
            '.navbar', '.menu', '.ads', 'iframe', '.footer', '.header',
            '#header', '#footer', '.sidebar', '#sidebar'
        ]
        for selector in noise:
            for node in parser.css(selector):
                node.remove()
        
        # 2. Aplicar exclusiones personalizadas
        if exclude_selectors:
            for selector in exclude_selectors:
                for node in parser.css(selector):
                    node.remove()
        
        # 3. Identificar el contenedor de contenido principal
        # Si no hay selector, intentamos adivinar contenedores comunes de Joomla/CMS
        main_content = None
        if include_selector:
            main_content = parser.css_first(include_selector)
        
        if not main_content:
            # Intentar selectores comunes de contenido
            for common in ['.item-page', 'article', '[role="main"]', '.content', '#content']:
                main_content = parser.css_first(common)
                if main_content: break
        
        if main_content:
            target_html = main_content.html
        else:
            # Fallback 1: Trafilatura HTML
            target_html = trafilatura.extract(html, output_format='html', include_comments=False)
            
            # Fallback 2: Si trafilatura devuelve nada, usar el body completo del parser (Selectolax)
            if not target_html:
                body = parser.css_first('body')
                target_html = body.html if body else html

        if not target_html:
            return None, 0.0

        # 4. Conversión a Markdown con configuración GFM (GitHub Flavored Markdown)
        markdown = md(
            target_html,
            heading_style="ATX",
            bullets="-",
            strip=['script', 'style'],
            autolinks=False, # Desactivar autolinks para evitar URLs crudas
            default_title=False
        )
        
        # 5. Post-procesamiento agresivo de ruido semántico (Regex)
        import re
        
        # Erradicar Imágenes: ![alt](url)
        markdown = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)
        
        # Aplanar Enlaces: [texto](url) -> texto
        markdown = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', markdown)
        
        # Limpieza de saltos de línea excesivos y normalización
        markdown = re.sub(r'\n{3,}', '\n\n', markdown.strip())
        
        confidence = 1.0 if markdown else 0.0
        return markdown, confidence
