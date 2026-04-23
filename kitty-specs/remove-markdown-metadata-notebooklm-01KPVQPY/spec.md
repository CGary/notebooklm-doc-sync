# Specification: Limpieza Total de Comentarios para NotebookLM

**Status**: [DRAFT]
**Title**: Eliminación de Comentarios HTML y Cabeceras de Origen en Markdown
**Mission ID**: 01KPVQPYAA4B0VD3WFSHSCB558
**Created**: 2026-04-22

## 1. Objective and Success Criteria

### Objective
Asegurar la compatibilidad total de los archivos generados con NotebookLM mediante la eliminación de todos los comentarios HTML (`<!-- ... -->`) y cabeceras que contienen metadatos técnicos (URLs de origen, hashes, IDs). El objetivo es que los archivos contengan únicamente el contenido técnico útil.

### Success Criteria
1. **SC-001**: Los archivos Markdown finales no contienen etiquetas `<!-- ... -->`.
2. **SC-002**: Se eliminan los encabezados `# URL` y las listas `- Fuente: ...` de cada unidad.
3. **SC-003**: El contenido del contenedor es una secuencia limpia de secciones de documentación.
4. **SC-004**: Los archivos son aceptados sin errores por NotebookLM.

## 2. User Scenarios & Testing

### Primary Scenario: Generación de Contenedor Minimalista
1. **Actor**: Operador de NotebookLM.
2. **Trigger**: El sistema ensambla múltiples unidades de documentación.
3. **Behavior**: 
    - El ensamblador concatena solo el cuerpo del Markdown extraído.
    - Se eliminan todas las marcas de anclaje (`unit:begin`, `unit:end`).
4. **Success Outcome**: Se genera un archivo `.md` que contiene solo el texto de la documentación técnica.

## 3. Requirements

### Functional Requirements (FR)

| ID | Description | Status |
|---|---|---|
| **FR-001** | Modificar `doc_sync/assemble.py` para no incluir cabeceras ni comentarios de anclaje. | [REQUIRED] |
| **FR-002** | Asegurar que el separador entre unidades sea un simple salto de línea o regla horizontal (`---`) sin comentarios. | [REQUIRED] |
| **FR-003** | Mantener la integridad de los datos en la base de datos a pesar de no estar en el archivo físico. | [REQUIRED] |

### Non-Functional Requirements (NFR)

| ID | Description | Status |
|---|---|---|
| **NFR-001** | **Compatibilidad**: Cumplimiento estricto de las restricciones de formato de NotebookLM. | [REQUIRED] |

## 4. Assumptions

1. NotebookLM puede identificar el contexto basándose únicamente en el contenido de los encabezados internos de la documentación (H1, H2, etc.).
2. No se requiere trazabilidad física dentro del archivo `.md` (toda la trazabilidad vive en `state.db`).
