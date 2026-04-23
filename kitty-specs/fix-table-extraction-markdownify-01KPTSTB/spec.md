# Specification: Mejora de Extracción de Tablas (Markdownify)

**Status**: [DRAFT]
**Title**: Mejora de Extracción de Tablas mediante Enfoque Híbrido Trafilatura + Markdownify
**Mission ID**: 01KPTSTBNGK69FJCFYG0QT1HBA
**Created**: 2026-04-22

## 1. Objective and Success Criteria

### Objective
Corregir la legibilidad de las tablas en los archivos Markdown generados. Actualmente, `trafilatura` aplana las tablas, destruyendo la estructura de filas y columnas, lo que degrada la calidad del RAG en NotebookLM. Se implementará un enfoque híbrido que utilice `trafilatura` para la limpieza de HTML y `markdownify` para la conversión a Markdown de alta fidelidad.

### Success Criteria
1. **SC-001**: Las tablas HTML se representan como tablas Markdown bidimensionales válidas (`| celda | celda |`).
2. **SC-002**: Se mantiene la capacidad de filtrado de ruido (menús, pies de página) de `trafilatura`.
3. **SC-003**: El sistema es capaz de procesar las URLs existentes sin romper el flujo determinista.
4. **SC-004**: Reducción del error de interpretación de datos tabulares en NotebookLM.

## 2. User Scenarios & Testing

### Primary Scenario: Extracción de Diccionario de Datos
1. **Actor**: Operador de NotebookLM.
2. **Trigger**: El sistema procesa una página con tablas técnicas (ej. estructura de registros de compras).
3. **Behavior**: 
    - `trafilatura` extrae el HTML limpio del cuerpo de la página.
    - `markdownify` convierte ese HTML a Markdown preservando la geometría de la tabla.
4. **Success Outcome**: El archivo `.md` resultante contiene tablas legibles que permiten a NotebookLM responder preguntas específicas sobre columnas y tipos de datos.

## 3. Requirements

### Functional Requirements (FR)

| ID | Description | Status |
|---|---|---|
| **FR-001** | Integrar la librería `markdownify` en el proyecto. | [REQUIRED] |
| **FR-002** | Modificar `doc_sync/extract.py` para solicitar salida en formato HTML a `trafilatura`. | [REQUIRED] |
| **FR-003** | Implementar la conversión de HTML limpio a Markdown usando `markdownify` con soporte para tablas. | [REQUIRED] |
| **FR-004** | Asegurar que la normalización y el hashing sigan funcionando sobre el nuevo formato de salida. | [REQUIRED] |

### Non-Functional Requirements (NFR)

| ID | Description | Status |
|---|---|---|
| **NFR-001** | **Fidelidad**: Las tablas deben mantener la relación fila/columna original del HTML. | [REQUIRED] |

### Constraints (C)

| ID | Description | Status |
|---|---|---|
| **C-001** | No se debe perder la funcionalidad de selectores CSS (`include`/`exclude`) ya implementada. | [REQUIRED] |

## 4. Assumptions

1. `trafilatura` es capaz de devolver el fragmento de HTML limpio del contenido principal.
2. `markdownify` maneja correctamente las tablas complejas presentes en el sitio del SIAT.
