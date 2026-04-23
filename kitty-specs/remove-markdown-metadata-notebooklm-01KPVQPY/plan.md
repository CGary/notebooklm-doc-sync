# Implementation Plan: Limpieza Total de Comentarios para NotebookLM

**Mission ID**: 01KPVQPYAA4B0VD3WFSHSCB558
**Status**: [DRAFT]
**Feature**: [spec.md](./spec.md)

## 1. Technical Architecture

El cambio se centraliza exclusivamente en `doc_sync/assemble.py`.

### Pipeline de Ensamblado (Simplificado):
1. Leer unidades de la DB asignadas al contenedor.
2. Leer archivo markdown de la caché.
3. Concatenar los cuerpos **sin** el bloque de comentarios `<!-- unit:begin ... -->` ni el encabezado `# URL`.
4. Usar `\n\n---\n\n` como separador visual y estructural entre unidades.

## 2. Technical Decisions

- **Eliminación de Metadatos**: Se eliminará el código que genera las variables `header` y `footer` dentro del bucle de ensamblado.
- **Separador**: Se mantendrá la regla horizontal Markdown (`---`) para que NotebookLM sepa que termina una sección y empieza otra, pero sin comentarios HTML asociados.

## 3. Verification Plan

### Manual Verification (Fast Review):
1. Crear una configuración de prueba `projects/test_no_comments.yaml` con 2 URLs.
2. Ejecutar `run`.
3. Abrir el archivo en `output/` y buscar literalmente `<!--` o `# https://`. No debe existir ninguno.
