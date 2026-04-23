import click
import uuid
from pathlib import Path
from .config import load_config
from .db import Database
from .sync import SyncEngine
from .bucketing import Bucketer
from .assemble import Assembler
from .bootstrap import bootstrap_from_txt

@click.group()
def main():
    """Doc-Sync para NotebookLM: Sincroniza documentación web en contenedores Markdown."""
    pass

@main.command()
@click.argument('txt_path', type=click.Path(exists=True))
@click.option('--output', '-o', default=None, help='Ruta del archivo YAML a generar.')
def bootstrap(txt_path, output):
    """Crea un archivo de proyecto (.yaml) a partir de una lista de URLs en texto."""
    txt_path = Path(txt_path)
    if output:
        output_yaml = Path(output)
    else:
        output_yaml = txt_path.with_suffix('.yaml')
    
    rejected_txt = txt_path.parent / f"rejected_{txt_path.name}"
    
    click.echo(f"Analizando URLs en {txt_path}...")
    success, valid_count, rejected_count = bootstrap_from_txt(txt_path, output_yaml, rejected_txt)
    
    if success:
        click.echo(f"¡Bootstrap completado!")
        click.echo(f" - URLs válidas: {valid_count} -> {output_yaml}")
        if rejected_count > 0:
            click.echo(f" - URLs filtradas (ruido): {rejected_count} -> {rejected_txt}")
        click.echo("\nPróximo paso: Revisa el archivo YAML y ejecuta 'doc-sync run'.")
    else:
        click.echo("Error: No se encontraron URLs válidas en el archivo.")

@main.command()
@click.argument('config_path', type=click.Path(exists=True))
@click.option('--output', '-o', default='output', help='Directorio de salida para los contenedores.')
@click.option('--db', default='state.db', help='Ruta a la base de datos de estado.')
def run(config_path, output, db):
    """Ejecuta el pipeline completo de sincronización."""
    config = load_config(Path(config_path))
    database = Database(Path(db))
    sync_engine = SyncEngine(database, config)
    bucketer = Bucketer(database, config)
    assembler = Assembler(database, config, Path(output))
    
    run_id = f"run_{datetime_id()}"
    click.echo(f"Iniciando ejecución {run_id} para el proyecto {config.project_id}...")
    
    # 1. Sync URLs
    for url in config.seed_urls:
        click.echo(f" Procesando: {url}")
        sync_engine.process_url(url, config.project_id)
        
        # Asignar tópico y contenedor si no lo tiene
        topic = bucketer.resolve_topic(url)
        with database.session() as conn:
            source = conn.execute("SELECT source_id, container_id FROM sources WHERE url_original = ?", (url,)).fetchone()
            if source and not source['container_id']:
                c_id = bucketer.assign_container(source['source_id'], topic)
                conn.execute("UPDATE sources SET container_id = ?, topic_slug = ? WHERE source_id = ?", (c_id, topic, source['source_id']))

    # 2. Assemble affected containers
    containers_affected = []
    with database.session() as conn:
        rows = conn.execute("SELECT container_id FROM containers WHERE project_id = ?", (config.project_id,)).fetchall()
        for row in rows:
            if assembler.assemble_container(row['container_id']):
                containers_affected.append(row['container_id'])
    
    # 3. Manifest
    if containers_affected:
        assembler.generate_manifest(run_id, containers_affected)
        click.echo(f"¡Éxito! Se han actualizado {len(containers_affected)} contenedores.")
    else:
        click.echo("No se detectaron cambios que requieran actualizar contenedores.")

@main.command()
@click.argument('domain_url')
@click.option('--sitemap/--no-sitemap', default=True, help='Intentar buscar sitemaps primero.')
def discover(domain_url, sitemap):
    """Busca y lista todas las URLs descubiertas en un dominio."""
    from trafilatura.sitemaps import sitemap_search
    from trafilatura.spider import focused_crawler
    
    click.echo(f"Buscando URLs en: {domain_url}...")
    
    urls = set()
    
    if sitemap:
        click.echo(" Intentando via Sitemap...")
        found = sitemap_search(domain_url)
        if found:
            urls.update(found)
            click.echo(f"  Encontradas {len(found)} URLs vía sitemap.")

    if not urls:
        click.echo(" No se encontró sitemap o se desactivó. Iniciando rastreo (crawler) limitado...")
        # El crawler de trafilatura es potente. Aquí lo limitamos un poco para el descubrimiento.
        to_visit, known_links = focused_crawler(domain_url, max_seen_urls=100)
        urls.update(known_links)
        click.echo(f"  Encontradas {len(known_links)} URLs vía rastreo.")

    if urls:
        click.echo("\nURLs descubiertas:")
        for url in sorted(urls):
            click.echo(f" - {url}")
        
        click.echo(f"\nTotal: {len(urls)} URLs.")
        click.echo("\nConsejo: Copia estas URLs en tu archivo de proyecto (.yaml) bajo 'seed_urls'.")
    else:
        click.echo(" No se encontraron URLs. Verifica que el dominio sea correcto y permita el rastreo.")

def datetime_id():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

if __name__ == '__main__':
    main()
