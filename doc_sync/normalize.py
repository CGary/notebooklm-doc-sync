import hashlib
import re
from typing import Tuple

class Normalizer:
    def __init__(self, inflation_factor: float = 1.15):
        self.inflation_factor = inflation_factor

    def normalize_markdown(self, text: str) -> str:
        """
        Normaliza el Markdown para que el hash sea determinista.
        """
        # Convertir finales de línea a \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Eliminar espacios al final de cada línea
        lines = [line.rstrip() for line in text.split('\n')]
        
        # Colapsar 3+ líneas en blanco en 2
        normalized_text = '\n'.join(lines)
        normalized_text = re.sub(r'\n{3,}', '\n\n', normalized_text)
        
        return normalized_text.strip()

    def compute_hash(self, text: str) -> str:
        """
        Calcula el hash SHA-256 del texto normalizado.
        """
        normalized = self.normalize_markdown(text)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def estimate_word_count(self, text: str) -> int:
        """
        Estima el conteo de palabras siguiendo la política de NotebookLM.
        """
        # Conteo simple por espacios
        words = len(re.findall(r'\w+', text))
        
        # Aplicar factor de inflación para sintaxis Markdown (tablas, código)
        # Este es un valor conservador para absorber la métrica de Google
        return int(words * self.inflation_factor)
