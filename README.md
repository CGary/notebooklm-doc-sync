# NotebookLM Doc-Sync 🚀

Sincronizador inteligente de documentación técnica diseñado para optimizar el uso de **NotebookLM** como motor de RAG.

Esta herramienta automatiza la extracción, normalización y consolidación de cientos de URLs en un número reducido de archivos Markdown, respetando los límites de fuentes de NotebookLM y mejorando la precisión de las citas.

## ✨ Características

- **Extracción de Alta Fidelidad**: Preserva tablas técnicas y estructuras complejas usando un motor híbrido (`selectolax` + `markdownify`).
- **Limpieza de Datos Inteligente**: Erradica imágenes y aplanado de enlaces automáticamente para ahorrar hasta un 20% de tokens de contexto.
- **Detección de Cambios**: Solo procesa lo que ha cambiado en la web mediante hashes SHA-256.
- **Bucketing Coherente**: Agrupa contenido por tópicos y volumen (límite de 250k palabras por archivo).
- **Cortesía Web**: Respeta `robots.txt` y aplica rate-limiting automático.
- **Bootstrap Automático**: Genera configuraciones de proyecto (.yaml) a partir de listas de URLs.

Para más detalles sobre la arquitectura y los principios de diseño, consulta la [Especificación Técnica Completa](./Technical_Specification.md).

## 🛠️ Instalación

Asegúrate de tener [uv](https://github.com/astral-sh/uv) instalado:

```bash
# Clonar el repositorio
git clone https://github.com/CGary/notebooklm-doc-sync.git
cd notebooklm-doc-sync

# Instalar dependencias y paquete en modo editable
uv pip install -e .
```

## 🕹️ Guía de Comandos

### 1. Descubrimiento de URLs
Si no tienes una lista de enlaces, búscalos automáticamente:
```bash
uv run doc-sync discover https://siatinfo.impuestos.gob.bo
```

### 2. Creación Automática de Proyecto (Bootstrap)
Crea una configuración basada en una lista de URLs en texto plano:
```bash
uv run doc-sync bootstrap projects/mis-links.txt
```
*Esto filtrará archivos no-HTML (PDF, Videos) y generará un archivo `.yaml` con reglas de tópicos inferidas.*

### 3. Ejecución de Sincronización
Procesa las URLs y genera los archivos para NotebookLM:
```bash
uv run doc-sync run projects/siat.yaml
```

## 📂 Estructura de Salida

- **`output/`**: Contiene los archivos `.md` consolidados listos para subir.
- **`output/manifest.json`**: Instrucciones para el operador sobre qué archivos subir o reemplazar.
- **`state.db`**: Base de datos SQLite que mantiene la memoria del sistema.

## 🏗️ Flujo de Trabajo Recomendado

1. **Obtener Links**: Usa `discover` o guarda tus URLs en un archivo `.txt`.
2. **Inicializar**: Usa `bootstrap` para generar el archivo de configuración `.yaml`.
3. **Personalizar**: Edita el `.yaml` para ajustar nombres de temas o límites.
4. **Sincronizar**: Ejecuta `run` periódicamente.
5. **Ingestar**: Sube los archivos de `output/` a tu cuaderno de NotebookLM.

---
Desarrollado con arquitectura sólida para el manejo masivo de documentación técnica.
