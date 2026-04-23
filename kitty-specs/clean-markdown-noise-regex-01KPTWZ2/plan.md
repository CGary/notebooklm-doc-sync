# Implementation Plan: Limpieza de Ruido en Markdown (Regex)

**Mission ID**: 01KPTWZ2KN7PPYM6YFNPJWV8CA
**Status**: [DRAFT]
**Feature**: [spec.md](./spec.md)

## 1. Technical Architecture

El cambio se implementará como una etapa de post-procesamiento en `doc_sync/extract.py`.

### Flujo de Datos:
1. `HTML` -> `Limpieza (Selectolax)` -> `Conversion (Markdownify)`.
2. `Markdown Crudo` -> `Post-procesamiento (Regex)` -> `Markdown Limpio`.

## 2. Technical Decisions

- **Regex para Imágenes**: `r'!\[.*?\]\(.*?\)'`
    - Elimina la etiqueta completa.
- **Regex para Enlaces**: `r'\[(.*?)\]\(.*?\)'`
    - Sustituye por el primer grupo de captura (el texto entre corchetes).
- **Lugar de Ejecución**: Al final del método `extract()` antes del retorno.

## 3. Verification Plan

### Automated/Manual Check:
1. Ejecutar el sistema con una lista reducida de URLs críticas (ej. solo `/index.php` y una página con tablas).
2. Verificar que no existan secuencias `![]` ni `()` con URLs en el texto final.
