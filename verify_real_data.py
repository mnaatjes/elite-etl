import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.append(str(Path.cwd()))

from src.engine.factory import EngineFactory
from src.workflows.onboard import OnboardingWorkflow

console = Console()

def test_onboard(name, url):
    console.print(f"\n[bold blue]>>> Testing Onboarding for: {name}[/bold blue]")
    console.print(f"[dim]URL: {url}[/dim]")
    
    factory = EngineFactory()
    db = factory.get_db()
    manifest = factory.get_manifest_manager()
    workflow = OnboardingWorkflow(db, manifest, factory.get_data_dir())
    
    try:
        # 1. Download & Sample
        console.print("[cyan]Step 1: Downloading & Decompressing...[/cyan]")
        entry = workflow.create_sample(name, url)
        console.print(f"   [green]Success![/green] File saved to: {entry.local_filepath}")
        console.print(f"   [dim]Size: {entry.metadata.file_size_bytes / 1024:.1f} KB, Hash: {entry.validation.actual_checksum[:10]}...[/dim]")
        
        # 2. Analyze
        console.print("[cyan]Step 2: Inferring Schema...[/cyan]")
        raw_schema = workflow.analyze_source(entry)
        
        props = raw_schema.get("properties", {})
        if not props and raw_schema.get("type") == "array":
            props = raw_schema.get("items", {}).get("properties", {})
            
        console.print(f"   [green]Success![/green] Inferred {len(props)} fields.")
        
        # 3. Register (Automated - no YAML edit for this test)
        console.print("[cyan]Step 3: Registering in Metadata Store...[/cyan]")
        source = workflow.register_source(
            name=name,
            url=url,
            target_table=f"src_{name.lower().replace(' ', '_')}",
            raw_schema=raw_schema,
            approved_schema=props # Just use raw props for test
        )
        console.print(f"   [bold green]Final Success![/bold green] Source ID: {source.id}")
        
    except Exception as e:
        console.print(f"[bold red]FAILED:[/bold red] {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_sources = [
        ("Spansh Systems 1Day", "https://downloads.spansh.co.uk/systems_1day.json.gz"),
        ("Spansh Factions", "https://downloads.spansh.co.uk/factions.json.gz"),
        ("Spansh Neutron Systems", "https://downloads.spansh.co.uk/systems_neutron.json.gz")
    ]
    
    for name, url in test_sources:
        test_onboard(name, url)
