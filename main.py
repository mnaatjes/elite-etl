import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint
from pathlib import Path
from typing import Optional
import shutil
import os
from loguru import logger

from src.engine.factory import EngineFactory
from src.workflows.onboard import OnboardingWorkflow
from src.workflows.ingest import IngestionWorkflow
from src.engine.resource import MemoryGuard

app = typer.Typer(help="Elite Dangerous Metadata-Driven Pipeline CLI")
console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Elite Dangerous Metadata-Driven Pipeline: The Flight Controller.
    """
    if ctx.invoked_subcommand is None:
        console.clear()
        console.print(Panel.fit(
            "[bold blue]Elite Dangerous Metadata-Driven Pipeline[/bold blue]\n"
            "[dim]The Workflow-Centric Orchestration Engine[/dim]",
            border_style="magenta"
        ))
        try:
            factory = EngineFactory()
            db = factory.get_db()
            from src.engine.models import Source, SyncJob
            
            source_count = db.query(Source).count()
            last_job = db.query(SyncJob).order_by(SyncJob.started_at.desc()).first()
            
            status_table = Table.grid(padding=1)
            status_table.add_column(style="cyan", justify="right")
            status_table.add_column(style="white")
            
            status_table.add_row("Registered Sources:", str(source_count))
            if last_job:
                status_style = "green" if last_job.status == "success" else "red" if last_job.status == "failed" else "yellow"
                status_table.add_row("Latest Sync Status:", f"[{status_style}]{last_job.status}[/{status_style}]")
            else:
                status_table.add_row("Latest Sync Status:", "[yellow]N/A[/yellow]")

            # Resource Monitoring
            guard = MemoryGuard()
            usage = guard.get_current_usage()
            status_table.add_row("System Memory:", f"{usage.percent}% used ({usage.used_mb:.1f} MB by CLI)")

            console.print(Panel(status_table, title="[bold]System Status[/bold]", border_style="blue", expand=False))
            db.close()
        except Exception:
            console.print("[dim yellow]Note: Metadata database not yet initialized.[/dim yellow]")

        # Quick Help
        help_table = Table.grid(padding=1)
        help_table.add_column(style="green")
        help_table.add_column(style="dim")
        
        help_table.add_row("onboard [URL]", "Register a new data source")
        help_table.add_row("migrate", "Synchronize schemas to PostgreSQL")
        help_table.add_row("ingest [NAME]", "Perform high-speed data ingestion")
        help_table.add_row("status", "View detailed sync history")
        help_table.add_row("list", "Show all registered sources")
        help_table.add_row("clear", "Reset the entire catalog and manifest")
        help_table.add_row("--help", "Show full command menu")

        console.print(Panel(help_table, title="[bold]Quick Start[/bold]", border_style="green", expand=False))

def get_factory():
    return EngineFactory()

@app.command()
def clear():
    """
    CLEARS the entire data-source registry, manifest, local files, AND PostgreSQL tables.
    """
    console.print(Panel(
        "[bold red]⚠ CRITICAL WARNING ⚠[/bold red]\n\n"
        "This command will [underline]PERMANENTLY DELETE[/underline]:\n"
        "1. All Metadata in the SQLite catalog\n"
        "2. All Sync History and Logs\n"
        "3. All local Sample and YAML files\n"
        "4. [blink]ALL ACTIVE DATA TABLES[/blink] in your PostgreSQL Warehouse\n\n"
        "This action CANNOT be undone.",
        title="DANGER ZONE",
        border_style="bold red"
    ))

    if not typer.confirm("Are you absolutely sure you want to wipe the entire system?"):
        console.print("[yellow]System reset aborted.[/yellow]")
        return

    console.print("\n[bold red]FINAL VERIFICATION REQUIRED[/bold red]")
    if not typer.confirm("This is your last chance. Delete everything?"):
        console.print("[yellow]System reset aborted. Your data is safe.[/yellow]")
        return

    with console.status("[bold red]Wiping all pipeline data and tables...", spinner="bouncingBar"):
        factory = get_factory()
        data_dir = factory.get_data_dir()
        db = factory.get_db()
        pg = factory.get_postgres_adapter()
        
        try:
            # 1. Identify tables to drop (Surgical + Namespace Sweep)
            tables_to_drop = set()
            
            # A. From Metadata
            from src.engine.models import SchemaContract
            try:
                contracts = db.query(SchemaContract).all()
                for c in contracts:
                    tables_to_drop.add(c.target_table_name)
            except:
                pass
                
            # B. From Namespace Sweep (PostgreSQL tables starting with 'src_')
            try:
                sweep_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'src_%'"
                conn = pg._get_connection()
                with conn.cursor() as cur:
                    cur.execute(sweep_query)
                    for row in cur.fetchall():
                        tables_to_drop.add(row[0])
            except Exception as e:
                logger.warning(f"DB: Namespace sweep failed: {e}")

            # 2. Execute Drops
            from psycopg2 import sql
            for table_name in tables_to_drop:
                logger.info(f"DB: Dropping table {table_name}")
                pg.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table_name)))
            
            # 3. Reset Metadata Database (SQLite)
            db_url = os.getenv("METADATA_DB_URL", "sqlite:///data/metadata.db")
            if db_url.startswith("sqlite:///"):
                db_path = Path(db_url.replace("sqlite:///", ""))
                db.close()
                factory.engine.dispose()
                if db_path.exists():
                    db_path.unlink()
                from src.engine.models import Base
                Base.metadata.create_all(factory.engine)
            else:
                from src.engine.models import Base
                Base.metadata.drop_all(factory.engine)
                Base.metadata.create_all(factory.engine)
            
            # 4. Reset Manifest
            manifest_mgr = factory.get_manifest_manager()
            manifest_mgr.save({"datasets": []})
            
            # 5. Purge Directories
            dirs_to_clear = ["samples", "downloads", "schemas"]
            for d in dirs_to_clear:
                dir_path = data_dir / d
                if dir_path.exists():
                    for item in dir_path.iterdir():
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
            
            logger.warning("Full system reset (Metadata + Data Plane) completed.")
            console.print(f"[bold green]Success![/bold green] System wiped. {len(tables_to_drop)} tables dropped.")
            
        except Exception as e:
            console.print(f"[bold red]Error during reset:[/bold red] {str(e)}")
            logger.exception("CLI: Clear command failed")
        finally:
            pg.close()

@app.command()
@logger.catch
def onboard(
    name: str = typer.Argument(..., help="Human-readable name for the source"),
    url: str = typer.Argument(..., help="The URL to download the data from"),
    memory_limit: float = typer.Option(75.0, "--memory-limit", help="Memory usage percentage limit")
):
    """
    Launches the interactive onboarding wizard for a new data source.
    """
    factory = get_factory()
    db = factory.get_db()
    manifest = factory.get_manifest_manager()
    workflow = OnboardingWorkflow(db, manifest, factory.get_data_dir(), memory_limit=memory_limit)

    logger.info(f"CLI: Starting onboarding for {name}")
    console.print(Panel(f"[bold blue]Initializing Onboarding (Streaming Mode)[/bold blue]\n[cyan]Source:[/cyan] {name}\n[cyan]URL:[/cyan] {url}", title="Phase A: Init"))

    try:
        # Step 1: Direct-to-Pandas Analysis
        with console.status("[bold green]Streaming and Analyzing structure...", spinner="dots") as status:
            def memory_heartbeat():
                usage = workflow.guard.get_current_usage()
                status.update(f"[bold green]Streaming & Analyzing... [dim]RAM: {usage.percent}% ({usage.used_mb:.1f}MB)[/dim]")
                workflow.guard.check_memory()
            
            workflow.analyzer.memory_callback = memory_heartbeat
            
            # Create the IO Adapter bridge
            stream_adapter = workflow.get_streaming_sample(url)
            raw_schema = workflow.analyze_source(stream_adapter)

        # Step 2: Discovery Table
        console.print("\n[bold]Inferred Schema Discovery[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Field Path")
        table.add_column("Type")
        table.add_column("Required")

        props = raw_schema.get("properties", {})
        if not props and raw_schema.get("type") == "array":
            props = raw_schema.get("items", {}).get("properties", {})

        for field_name, details in props.items():
            field_type = details.get("type", "unknown")
            is_required = field_name in raw_schema.get("required", [])
            table.add_row(str(field_name), str(field_type), "Yes" if is_required else "No")

        console.print(table)
        
        # Step 3: HITL
        if typer.confirm("\n[bold cyan]Would you like to rename columns or refine the schema before saving?[/bold cyan]"):
            yaml_path = workflow.prepare_hitl_yaml(name, raw_schema)
            edited_content = typer.edit(filename=str(yaml_path))
            
            if edited_content:
                with open(yaml_path, "w") as f:
                    f.write(edited_content)
                
                with console.status("[bold green]Finalizing registration...", spinner="check"):
                    source = workflow.finalize_onboarding(name, url, yaml_path, raw_schema)
                
                console.print(f"\n[bold green]Success![/bold green] Source [cyan]{name}[/cyan] registered.")
            else:
                logger.warning(f"CLI: HITL Edit cancelled for {name}")
                console.print("[yellow]No changes detected. Onboarding suspended.[/yellow]")
        else:
            if typer.confirm("Save with raw (un-edited) schema?"):
                yaml_path = workflow.prepare_hitl_yaml(name, raw_schema)
                source = workflow.finalize_onboarding(name, url, yaml_path, raw_schema)
                console.print(f"\n[bold green]Success![/bold green] Source [cyan]{name}[/cyan] registered.")

    except MemoryError as me:
        console.print(f"\n[bold red]CRITICAL MEMORY HALT:[/bold red] {str(me)}")
        logger.critical(f"CLI: Execution halted due to memory limits: {str(me)}")
    except Exception as e:
        console.print(f"[bold red]Error during onboarding:[/bold red] {str(e)}")
        logger.exception("CLI: Unexpected error during onboarding")
    finally:
        db.close()

@app.command()
def migrate():
    """
    Synchronizes the Metadata Catalog to physical tables in PostgreSQL.
    Checks for missing tables and performs Tier 2 DDL validation.
    """
    factory = get_factory()
    db = factory.get_db()
    pg = factory.get_postgres_adapter()
    from src.engine.models import Source

    sources = db.query(Source).filter_by(is_active=True).all()
    
    if not sources:
        console.print("[yellow]No active sources found to migrate.[/yellow]")
        db.close()
        return

    console.print(Panel("[bold blue]Starting Schema Migration[/bold blue]", subtitle="PostgreSQL Warehouse"))

    try:
        for s in sources:
            if not s.contract:
                console.print(f"[dim]Skipping {s.name}: No approved schema contract found.[/dim]")
                continue

            table_name = s.contract.target_table_name
            if not pg.table_exists(table_name):
                # Tier 2 Validation
                console.print(f"Validating DDL for [cyan]{table_name}[/cyan]...")
                if pg.validate_ddl(table_name, s.contract.approved_schema):
                    console.print(f"Creating table: [cyan]{table_name}[/cyan]...")
                    pg.create_table(table_name, s.contract.approved_schema)
                    console.print(f"[green]✓ Table initialized.[/green]")
                else:
                    console.print(f"[bold red]FAILED:[/bold red] DDL validation failed for {table_name}. Check logs.")
            else:
                console.print(f"[dim]Table {table_name} already exists. Skipping.[/dim]")
        
        console.print("\n[bold green]Migration Complete![/bold green] Warehouse is in-sync with catalog.")
    except Exception as e:
        console.print(f"[bold red]Migration Error:[/bold red] {str(e)}")
        logger.exception("CLI: Migration failed")
    finally:
        db.close()
        pg.close()

@app.command()
@logger.catch
def ingest(
    name: str = typer.Argument(..., help="Name of the source to ingest"),
    memory_limit: float = typer.Option(75.0, "--memory-limit", help="Memory usage percentage limit")
):
    """
    Performs a high-speed ingestion with Tier 3 Bookend validation.
    """
    factory = get_factory()
    db = factory.get_db()
    pg = factory.get_postgres_adapter()
    workflow = IngestionWorkflow(db, pg, memory_limit=memory_limit)
    from src.engine.models import Source, SyncJob

    console.print(Panel(f"[bold blue]Starting Ingestion[/bold blue]\n[cyan]Source:[/cyan] {name}", title="Phase C: Ingest"))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[mem]}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Streaming data from source...", total=None, mem="")
            
            def update_progress(rows):
                usage = workflow.guard.get_current_usage()
                mem_str = f"RAM: {usage.percent}% ({usage.used_mb:.1f}MB)"
                progress.update(task, description=f"Ingested {rows:,} rows...", mem=mem_str)

            rows_loaded = workflow.ingest_source(name, progress_callback=update_progress)
            
            # Check for SUSPECT status in SyncJob
            last_job = db.query(SyncJob).filter_by(source_id=db.query(Source).filter_by(name=name).first().id).order_by(SyncJob.started_at.desc()).first()
            
            if last_job.status == "suspect":
                progress.update(task, description=f"[bold yellow]Ingested {rows_loaded:,} rows (Suspect)", completed=100)
                console.print(f"\n[bold yellow]WARNING:[/bold yellow] Row count mismatch detected! {last_job.error_message}")
            else:
                progress.update(task, description=f"Success! {rows_loaded:,} rows loaded.", completed=100)
                console.print(f"\n[bold green]Ingestion Complete![/bold green] Source [cyan]{name}[/cyan] data is verified and queryable.")

    except MemoryError as me:
        console.print(f"\n[bold red]CRITICAL MEMORY HALT:[/bold red] {str(me)}")
    except Exception as e:
        console.print(f"[bold red]Error during ingestion:[/bold red] {str(e)}")
        logger.exception(f"CLI: Ingestion failed for {name}")
    finally:
        db.close()
        pg.close()

@app.command()
def list():
    """
    Lists all registered data sources in the metadata catalog.
    """
    factory = get_factory()
    db = factory.get_db()
    from src.engine.models import Source

    sources = db.query(Source).all()

    if not sources:
        console.print("[yellow]No sources registered in the catalog.[/yellow]")
        db.close()
        return

    table = Table(title="Metadata Catalog: Registered Sources")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Active", style="green")
    table.add_column("Target Table")

    for s in sources:
        target = s.contract.target_table_name if s.contract else "N/A"
        table.add_row(
            str(s.id),
            s.name,
            "Yes" if s.is_active else "No",
            target
        )

    console.print(table)
    db.close()

@app.command()
def status():
    """
    Displays a dashboard of the latest synchronization jobs and system health.
    """
    factory = get_factory()
    db = factory.get_db()
    from src.engine.models import SyncJob

    # Get last 10 jobs
    jobs = db.query(SyncJob).order_by(SyncJob.started_at.desc()).limit(10).all()

    if not jobs:
        console.print("[yellow]No job history found.[/yellow]")
        db.close()
        return

    table = Table(title="System Health: Recent Sync Jobs")
    table.add_column("Started", style="dim")
    table.add_column("Source", style="cyan")
    table.add_column("Status")
    table.add_column("Rows", justify="right")
    table.add_column("Payload Size")

    for j in jobs:
        status_style = "green" if j.status == "success" else "red" if j.status == "failed" else "yellow"
        if j.status == "suspect": status_style = "bold yellow"
        
        source_name = j.source.name if j.source else "Unknown"
        size_kb = f"{j.byte_count / 1024:.1f} KB" if j.byte_count else "0"
        
        table.add_row(
            j.started_at.strftime("%Y-%m-%d %H:%M"),
            source_name,
            f"[{status_style}]{j.status}[/{status_style}]",
            str(j.rows_processed),
            size_kb
        )

    console.print(table)
    db.close()

@app.command()
def delete(name: str):
    """
    Removes a data source and its associated metadata from the catalog.
    """
    factory = get_factory()
    db = factory.get_db()
    from src.engine.models import Source

    source = db.query(Source).filter_by(name=name).first()
    if not source:
        console.print(f"[red]Source '{name}' not found.[/red]")
        db.close()
        return

    if typer.confirm(f"Are you sure you want to delete source '{name}' and all its history?"):
        # Surgical drop of target table if it exists
        if source.contract:
            pg = factory.get_postgres_adapter()
            try:
                table_name = source.contract.target_table_name
                from psycopg2 import sql
                query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table_name))
                pg.execute(query)
                pg.close()
            except:
                pass
        
        db.delete(source)
        db.commit()
        console.print(f"[green]Source '{name}' and its PostgreSQL table deleted successfully.[/green]")
    
    db.close()

if __name__ == "__main__":
    app()
