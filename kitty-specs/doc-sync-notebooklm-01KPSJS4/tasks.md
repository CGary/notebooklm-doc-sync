# Tasks: Doc-Sync para NotebookLM

**Mission ID**: 01KPSJS4QQ51Y63X34Q925KMMH
**Status**: [PLANNED]

## Work Packages (WPs)

### WP01: Foundation & Persistence
- [ ] Configurar entorno Python y dependencias (`httpx`, `trafilatura`, `pyyaml`).
- [ ] Implementar `doc_sync/config.py` para cargar archivos `.yaml`.
- [ ] Implementar `doc_sync/db.py` con el esquema SQLite y migraciones.
- [ ] **Verification**: Tests unitarios de carga de config y creación de DB.

### WP02: Fetching & Extraction
- [ ] Implementar `doc_sync/fetch.py` con soporte para `robots.txt` y rate-limiting.
- [ ] Implementar `doc_sync/extract.py` integrando `trafilatura` y selectores CSS.
- [ ] Manejar peticiones condicionales (ETag).
- [ ] **Verification**: Script de prueba que extraiga una URL de SIAT y genere Markdown crudo.

### WP03: Sync Logic & Normalization
- [ ] Implementar `doc_sync/normalize.py` para limpieza de Markdown y hashing SHA-256.
- [ ] Implementar el ciclo de detección de cambios (Changed/Unchanged).
- [ ] Implementar la taxonomía de errores y política de borrado conservadora.
- [ ] **Verification**: Test que valide que el hash no cambia si el contenido es idéntico tras normalización.

### WP04: Bucketing & Assembly
- [ ] Implementar `doc_sync/bucketing.py` con reglas de tópicos y límites de palabras.
- [ ] Implementar algoritmo de rebalanceo determinista.
- [ ] Implementar `doc_sync/assemble.py` para escribir archivos `.md` consolidados.
- [ ] Generar el archivo `manifest.json`.
- [ ] **Verification**: Generación de dos contenedores a partir de un set de datos de prueba.

### WP05: CLI & Final Integration
- [ ] Implementar `doc_sync/cli.py` con comandos `run`, `dry-run` y `report`.
- [ ] Generar reporte humano en texto plano.
- [ ] Pruebas de integración finales contra el sitio SIAT (o mock completo).
- [ ] **Verification**: Ejecución completa del pipeline y validación del manifiesto.
