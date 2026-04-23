# Implementation Plan: Fusión contra Colisión de Prefijos

**Mission ID**: 01KPV28BT80159C5QQ15NMM1JG
**Status**: [DRAFT]
**Feature**: [spec.md](./spec.md)

## 1. Technical Architecture

El cambio es quirúrgico y afecta a dos capas: **Ingesta** (`bootstrap.py`) y **Enrutamiento** (`bucketing.py`).

### Cambio 1: `bootstrap_from_txt` en `doc_sync/bootstrap.py`
Se modificará el bucle de extracción de segmentos para que ignore una "lista negra" de segmentos genéricos (ej. `index.php`). Al encontrar un segmento prohibido, el algoritmo tomará el siguiente segmento de la ruta como base para la regla.

### Cambio 2: `resolve_topic` en `doc_sync/bucketing.py`
Se cambiará el uso de `.startswith(prefix)` por una comprobación dual:
`path == prefix` OR `path.startswith(prefix + '/')`.

## 2. Technical Decisions

- **Lista de segmentos prohibidos**: `['index.php', 'wp-content', 'wp-includes', 'templates']`.
- **Estandarización de rutas**: Todas las comparaciones se harán con el prefijo normalizado (sin `/` al final).

## 3. Verification Plan

### Manual Verification (Fast Review):
1. Crear un archivo `mini_links.txt` con 3 URLs:
    - `https://site.com/index.php/tema-a`
    - `https://site.com/index.php/tema-a/sub-1`
    - `https://site.com/index.php/tema-b`
2. Ejecutar `bootstrap` y verificar que el YAML no tenga la regla `/index.php` sino `/index.php/tema-a` y `/index.php/tema-b`.
3. Ejecutar `run` y verificar que cada una vaya a su contenedor correcto.
