# Specification: Doc-Sync para NotebookLM

**Status**: [DRAFT]
**Title**: Doc-Sync para NotebookLM: Sistema de Sincronización y Consolidación de Documentación
**Mission ID**: 01KPSJS4QQ51Y63X34Q925KMMH
**Created**: 2026-04-22

## 1. Objective and Success Criteria

### Objective
Automatizar la extracción, normalización, consolidación y mantenimiento de sitios de documentación técnica estática en un número reducido de archivos Markdown de gran volumen, diseñados específicamente para su ingestión manual en NotebookLM.

### Success Criteria
1. **SC-001**: Todas las URLs proporcionadas se procesan exitosamente o se clasifican con un código de error conocido.
2. **SC-002**: Los contenedores generados se mantienen por debajo del umbral de seguridad de palabras (250,000 palabras) para garantizar la compatibilidad con NotebookLM.
3. **SC-003**: El sistema produce un manifiesto (`manifest.json`) que indica exactamente qué archivos deben ser reemplazados o añadidos manualmente.
4. **SC-004**: Una ejecución sin cambios en la fuente no produce actualizaciones en los archivos de salida (determinismo).
5. **SC-005**: El sistema respeta los límites de tasa y `robots.txt` del sitio fuente.

## 2. User Scenarios & Testing

### Primary Scenario: Actualización de Documentación SIAT
1. **Actor**: Operador de NotebookLM.
2. **Trigger**: El operador desea actualizar el corpus de conocimiento de su cuaderno SIAT.
3. **Flow**:
    - El operador ejecuta el script localmente.
    - El sistema identifica qué URLs han cambiado desde la última ejecución usando hashes SHA-256.
    - El sistema regenera solo los contenedores Markdown afectados.
    - El sistema genera un `manifest.json`.
4. **Success Outcome**: El operador recibe una lista de instrucciones claras en el manifiesto indicando qué archivos subir a NotebookLM.

### Edge Case: Fallo de Extracción por Cambio en DOM
1. **Scenario**: El sitio fuente cambia su estructura de HTML y el extractor pierde confianza.
2. **Behavior**: El sistema marca la URL como `NEEDS_REVIEW`, conserva el último contenido bueno conocido en el contenedor y registra el error para que el desarrollador actualice los selectores en el código.

## 3. Requirements

### Functional Requirements (FR)

| ID | Description | Status |
|---|---|---|
| **FR-001** | El sistema debe normalizar y procesar una lista curada de URLs. | [REQUIRED] |
| **FR-002** | Debe utilizar `httpx` para realizar peticiones condicionales (ETag/Last-Modified). | [REQUIRED] |
| **FR-003** | Debe extraer el contenido semántico usando `trafilatura` y convertirlo a Markdown. | [REQUIRED] |
| **FR-004** | Debe calcular un hash SHA-256 del cuerpo Markdown para detectar cambios reales de contenido. | [REQUIRED] |
| **FR-005** | Debe persistir el estado (URLs, hashes, metadatos, errores) en una base de datos SQLite en modo WAL. | [REQUIRED] |
| **FR-006** | Debe agrupar las unidades de documentación en contenedores basados en tópicos y límites de volumen (Bucketing). | [REQUIRED] |
| **FR-007** | Debe generar un `manifest.json` y un reporte humano con instrucciones para el operador. | [REQUIRED] |

### Non-Functional Requirements (NFR)

| ID | Description | Status |
|---|---|---|
| **NFR-001** | **Rendimiento**: Límite de tasa por dominio de 1 solicitud por segundo por defecto. | [REQUIRED] |
| **NFR-002** | **Capacidad**: El límite suave de palabras por contenedor es de 250,000 (máximo teórico 500,000). | [REQUIRED] |
| **NFR-003** | **Seguridad**: El sistema no debe requerir credenciales para acceder a documentación pública. | [REQUIRED] |
| **NFR-004** | **Polite**: Respeto obligatorio de `robots.txt`. | [REQUIRED] |

### Constraints (C)

| ID | Description | Status |
|---|---|---|
| **C-001** | El sistema debe ser una aplicación Python CLI de ejecución manual/local. | [REQUIRED] |
| **C-002** | No se permite el uso de navegadores headless (Playwright/Selenium) en el MVP. | [REQUIRED] |
| **C-003** | No hay sincronización automática con NotebookLM (carga manual obligatoria). | [REQUIRED] |

## 4. Domain Language (Optional)

- **Unidad de Documentación**: El contenido Markdown extraído de una única URL.
- **Contenedor**: Archivo Markdown consolidado que agrupa múltiples unidades.
- **Bucketing**: El proceso de asignar unidades a contenedores basándose en tópicos y tamaño.
- **Manifiesto**: Archivo JSON que describe las acciones requeridas por el operador.

## 5. Assumptions

1. Se asume que el sitio fuente es principalmente renderizado en servidor (SSR).
2. Se asume que el operador tiene acceso a internet y permisos para subir archivos a NotebookLM.
3. Se asume que la estructura de URLs del sitio fuente es estable.

## 6. Key Entities

- **Project**: Configuración global del sitio a sincronizar.
- **Source**: Representa una URL individual y su estado de extracción.
- **Container**: Archivo físico de salida que agrupa fuentes.
- **Run**: Registro de una ejecución del pipeline.
