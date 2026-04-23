# Implementation Plan: Mejora de Extracción de Tablas (Markdownify)

**Mission ID**: 01KPTSTBNGK69FJCFYG0QT1HBA
**Status**: [DRAFT]
**Feature**: [spec.md](./spec.md)

## 1. Technical Architecture

El cambio se centrará principalmente en el módulo `doc_sync/extract.py`.

### Pipeline Actual (Legacy):
`HTML Original` -> `trafilatura (Markdown)` -> `Salida con tablas aplanadas`.

### Pipeline Propuesto (Híbrido):
1. `HTML Original` -> `trafilatura (HTML)` (Usa `output_format='xml'` o similar para obtener el fragmento limpio).
2. `HTML Limpio` -> `markdownify` -> `Markdown de alta fidelidad`.

## 2. Technical Decisions

- **Librería**: `markdownify` es la elegida por su capacidad de manejar etiquetas `<table>`, `<tr>`, `<td>` y convertirlas a tablas GFM (GitHub Flavored Markdown).
- **Configuración de Markdownify**: 
    - `heading_style="ATX"` (# Título).
    - `bullets="-"`.
    - `strip=['script', 'style', 'nav', 'footer']` (como respaldo).

## 3. Verification Plan

### Manual Verification:
1. Ejecutar `doc-sync run` sobre una URL con tablas (ej. `https://siatinfo.impuestos.gob.bo/index.php/registro-de-compras-y-ventas/confirmacion-y-registro-de-compras`).
2. Abrir el archivo en `output/` y verificar visualmente que las tablas tengan el formato `|---|---|`.
