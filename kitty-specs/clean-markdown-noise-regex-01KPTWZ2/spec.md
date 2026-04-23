# Specification: Limpieza de Ruido en Markdown (Regex)

**Status**: [DRAFT]
**Title**: Erradicación de Imágenes y Aplanado de Enlaces en Salida Markdown
**Mission ID**: 01KPTWZ2KN7PPYM6YFNPJWV8CA
**Created**: 2026-04-22

## 1. Objective and Success Criteria

### Objective
Optimizar la salida Markdown para el RAG de NotebookLM mediante la eliminación de elementos que no aportan valor semántico y consumen tokens de contexto. Específicamente, se eliminarán todas las imágenes embedidas y se aplanarán los hipervínculos (conservando solo el texto visible y eliminando la URL).

### Success Criteria
1. **SC-001**: Los archivos Markdown finales no contienen el patrón `![alt](url)`.
2. **SC-002**: Los enlaces Markdown `[texto](url)` se transforman en texto plano `texto`.
3. **SC-003**: Reducción significativa en el conteo de tokens/palabras por archivo.
4. **SC-004**: Mejora en la precisión del RAG al eliminar distracciones (URLs largas, metadatos de imágenes).

## 2. User Scenarios & Testing

### Primary Scenario: Limpieza de Archivo de Índices
1. **Actor**: Operador de NotebookLM.
2. **Trigger**: El sistema procesa una página con múltiples enlaces a archivos externos (ej. `/index.php`).
3. **Behavior**: 
    - El sistema extrae el contenido.
    - Se aplican Regex para quitar las imágenes decorativas.
    - Los enlaces `[RND-1021](https://...)` se convierten en `RND-1021`.
4. **Success Outcome**: El operador recibe un archivo limpio y compacto que NotebookLM puede procesar eficientemente.

## 3. Requirements

### Functional Requirements (FR)

| ID | Description | Status |
|---|---|---|
| **FR-001** | Implementar Regex para eliminar imágenes: `!\[.*?\]\(.*?\)` | [REQUIRED] |
| **FR-002** | Implementar Regex para aplanar enlaces: `\[(.*?)\]\(.*?\)` -> `\1` | [REQUIRED] |
| **FR-003** | Aplicar estas transformaciones en el módulo `doc_sync/extract.py` tras la fase de `markdownify`. | [REQUIRED] |

### Non-Functional Requirements (NFR)

| ID | Description | Status |
|---|---|---|
| **NFR-001** | **Eficiencia de Tokens**: El ahorro de tokens debe ser de al menos un 10% en páginas con muchos enlaces. | [REQUIRED] |

### Constraints (C)

| ID | Description | Status |
|---|---|---|
| **C-001** | No se deben eliminar los comentarios HTML técnicos (`<!-- ... -->`) necesarios para el sistema. | [REQUIRED] |

## 4. Assumptions

1. El texto visible de los enlaces es suficiente para que NotebookLM identifique el tema.
2. Las imágenes en la documentación de SIAT son principalmente decorativas o diagramas que el modelo de texto no puede interpretar de todos modos.
