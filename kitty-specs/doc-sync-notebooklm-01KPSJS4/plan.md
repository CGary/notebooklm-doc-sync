# Implementation Plan: Doc-Sync para NotebookLM

**Mission ID**: 01KPSJS4QQ51Y63X34Q925KMMH
**Status**: [DRAFT]
**Feature**: [spec.md](./spec.md)

## 1. Technical Architecture

El sistema se construirá como una aplicación CLI en Python, estructurada en módulos independientes para facilitar la prueba y el mantenimiento.

### Module Structure
- `doc_sync/cli.py`: Punto de entrada, gestión de comandos y argumentos.
- `doc_sync/config.py`: Gestión de archivos YAML de proyecto y validación de esquemas.
- `doc_sync/db.py`: Capa de persistencia SQLite. Implementará migraciones automáticas y modo WAL.
- `doc_sync/fetch.py`: Cliente HTTP basado en `httpx`. Manejará reintentos, rate-limiting y cumplimiento de `robots.txt`.
- `doc_sync/extract.py`: Integración con `trafilatura` y lógica de selectores CSS (via `selectolax`).
- `doc_sync/normalize.py`: Limpieza de Markdown, normalización de líneas y cálculo de hashes SHA-256.
- `doc_sync/bucketing.py`: Lógica de asignación de fuentes a contenedores y detección de overflow.
- `doc_sync/assemble.py`: Escritura de archivos Markdown consolidados y generación de manifiestos.

## 2. Data Model (SQLite)

Se implementará el esquema detallado en la especificación técnica con las siguientes tablas principales:
- `projects`: Configuración global por sitio.
- `sources`: Estado de cada URL (hash, última extracción, errores).
- `containers`: Metadatos de los archivos Markdown generados.
- `runs`: Historial de ejecuciones y métricas.
- `review_queue`: URLs que requieren intervención manual por baja confianza.

## 3. Core Workflows

### Extraction Pipeline
1. Carga de configuración y `robots.txt`.
2. Selección de URLs activas.
3. Petición condicional (`If-None-Match`).
4. Extracción semántica y cálculo de hash de contenido.
5. Clasificación (`UNCHANGED`, `CHANGED`, `FAILED`).

### Assembly and Bucketing
1. Evaluación de volumen de palabras por tópico.
2. Detección de contenedores `SPLIT_PENDING`.
3. Aplicación del algoritmo "Deterministic Greedy" para rebalanceo si es necesario.
4. Escritura física de archivos `.md` solo si su hash de ensamblado ha cambiado.

## 4. Technical Decisions & Trade-offs

- **SQLite WAL**: Elegido para permitir lecturas concurrentes mientras se escribe el estado de la extracción.
- **Httpx**: Preferido sobre `requests` por su soporte nativo de `asyncio`, aunque el MVP operará principalmente de forma síncrona/secuencial por dominio.
- **Trafilatura**: Seleccionado por su alta precisión en la extracción de contenido principal frente a alternativas como `BeautifulSoup` pura.
- **Markdown Comments as Anchors**: Uso de comentarios HTML para marcar unidades dentro de los contenedores, facilitando el parseo sin romper la legibilidad en NotebookLM.

## 5. Verification Plan

### Automated Testing
- Tests unitarios para el normalizador de Markdown y el generador de hashes.
- Tests de integración para la capa de base de datos (migraciones y CRUD).
- Mocks para el fetcher HTTP para probar casos de error (404, 500, 429).

### Manual Acceptance
- Ejecución de un "Dry Run" contra el sitio SIAT.
- Verificación manual de la legibilidad de un contenedor generado en NotebookLM.
- Verificación del manifiesto de salida.
