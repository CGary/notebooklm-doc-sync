# Implementation Plan: Fusión contra Colisión de Prefijos (Final)

**Mission ID**: 01KPV3H4K8CWCAK995EGHAFRMM
**Status**: [DRAFT]
**Feature**: [spec.md](./spec.md)

## 1. Technical Architecture

El cambio se implementará en dos módulos clave:

### Ingesta Inteligente (`doc_sync/bootstrap.py`)
Modificaremos el bucle de extracción de segmentos para que ignore una "lista negra" de segmentos genéricos (ej. `index.php`, `wp-content`). Al encontrar un segmento prohibido, el algoritmo tomará el siguiente segmento de la ruta como base para la regla de tópico.

### Enrutamiento Estricto (`doc_sync/bucketing.py`)
Cambiamos la comprobación `.startswith(prefix)` por una lógica que requiera coincidencia exacta o de subdirectorio completo.

## 2. Technical Decisions

- **Lista Genérica**: `{'index.php', 'wp-content', 'wp-includes', 'templates', 'images', 'archivos_tecnicos'}`.
- **Lógica Estricta**: `path == prefix` o `path.startswith(prefix + '/')`.

## 3. Verification Plan

### Manual Verification (Fast):
1. Crear `debug_links.txt` con URLs que simulen colisiones.
2. Ejecutar `bootstrap` y verificar el YAML.
3. Ejecutar `run` y verificar la base de datos `state.db`.
