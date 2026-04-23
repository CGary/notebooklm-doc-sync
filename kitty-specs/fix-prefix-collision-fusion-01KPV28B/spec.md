# Specification: Fusión contra Colisión de Prefijos

**Status**: [DRAFT]
**Title**: Fusión de Mejoras en Bootstrap e Inteligencia de Bucketing
**Mission ID**: 01KPV28BT80159C5QQ15NMM1JG
**Created**: 2026-04-22

## 1. Objective and Success Criteria

### Objective
Erradicar el problema de las "reglas trampa" (como `/index.php`) que absorben injustificadamente múltiples URLs debido a una lógica de coincidencia demasiado permisiva y a una generación de configuración poco selectiva. Se implementará una solución dual: un generador de configuración más inteligente y un enrutador de tópicos más estricto.

### Success Criteria
1. **SC-001**: El comando `bootstrap` ignora segmentos genéricos de CMS (ej. `index.php`) al inferir reglas de tópicos.
2. **SC-002**: El enrutador de tópicos requiere coincidencia exacta o de subdirectorio, impidiendo que prefijos parciales (ej. `/factura`) atrapen rutas distintas (ej. `/facturacion`).
3. **SC-003**: Mejora en la distribución de URLs en contenedores, evitando archivos "agujero negro" y contenedores vacíos.
4. **SC-004**: Los archivos generados mantienen nombres semánticamente útiles basados en el contenido real.

## 2. User Scenarios & Testing

### Primary Scenario: Generación y Ejecución de Proyecto SIAT
1. **Actor**: Desarrollador/Operador.
2. **Trigger**: El operador ejecuta `doc-sync bootstrap` sobre una lista de URLs de un sitio Joomla.
3. **Behavior**: 
    - El sistema genera un YAML donde las reglas omiten `index.php` y se centran en los términos funcionales (ej. `facturacion-en-linea`).
    - Al ejecutar `doc-sync run`, el enrutador asigna cada URL a su tópico más específico de forma estricta.
4. **Success Outcome**: Las URLs se distribuyen correctamente entre múltiples contenedores específicos en lugar de concentrarse en uno solo.

## 3. Requirements

### Functional Requirements (FR)

| ID | Description | Status |
|---|---|---|
| **FR-001** | Mejorar `bootstrap_from_txt` para filtrar segmentos genéricos de rutas en el análisis de tópicos. | [REQUIRED] |
| **FR-002** | Implementar lógica de coincidencia estricta en `resolve_topic` (exacta o prefijo con separador `/`). | [REQUIRED] |
| **FR-003** | Asegurar que la raíz `/` siga funcionando como catch-all final. | [REQUIRED] |

### Non-Functional Requirements (NFR)

| ID | Description | Status |
|---|---|---|
| **NFR-001** | **Predictibilidad**: El destino de una URL debe ser intuitivo y coincidir con su estructura de directorios. | [REQUIRED] |

### Constraints (C)

| ID | Description | Status |
|---|---|---|
| **C-001** | No se debe alterar el formato del archivo YAML de salida. | [REQUIRED] |

## 4. Assumptions

1. Los sitios web objetivo siguen convenciones de rutas jerárquicas estándar (incluso si usan `index.php` como puente).
