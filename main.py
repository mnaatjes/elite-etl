import sys
import os
import json
import argparse
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt

# Ensure the current directory is in the path so we can import from src
sys.path.append(os.getcwd())

from src.adapters.local_manifest_repository import LocalManifestRepository
from src.adapters.http_downloader import HttpDownloaderAdapter
from src.adapters.json_analyzer import JsonAnalyzerAdapter
from src.application.downloader_service import DownloaderService
from src.application.analyzer_service import AnalyzerService
from src.application.normalization_service import NormalizationService
from src.application.loader_service import LoaderService
from src.adapters.postgres_adapter import PostgresAdapter
from src.utils.db_utils import ping_database

console = Console()

def load_config():
    if not os.path.exists("config.json"):
        return {"base_download_dir": "data", "datasets": []}
    with open("config.json", "r") as f:
        return json.load(f)

def verify_permissions(data_dir: str):
    """Verifies that the data directory has safe and functional permissions."""
    path = Path(data_dir)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    
    if not os.access(path, os.W_OK):
        console.print(f"[bold red]CRITICAL ERROR:[/bold red] Data directory '{data_dir}' is not writable by current user.")
        sys.exit(1)
        
    # Check for overly broad permissions (World Writable)
    mode = os.stat(path).st_mode
    if mode & 0o002:
        console.print(f"[bold yellow]SECURITY WARNING:[/bold yellow] Data directory '{data_dir}' is world-writable (777).")
        console.print("Recommended: [cyan]chmod 750 " + data_dir + "[/cyan]")

def display_global_status(config, manifest_repo):
    """Displays a dashboard of all datasets and their current pipeline state."""
    # Infrastructure Check (Quiet)
    db_online, _ = ping_database()
    if not db_online:
        console.print("\n[bold red]⚠ Database is Offline.[/bold red] Run [cyan].scripts/setup_db.sh[/cyan] before loading data.")

    table = Table(title="[bold blue]Data Pipeline: Global Orchestrator Dashboard", title_justify="left", show_header=True, header_style="bold magenta")
    table.add_column("Dataset ID", style="cyan", no_wrap=True)
    table.add_column("Current Status", justify="left")
    table.add_column("Ready for Load", justify="center")
    table.add_column("Next Suggested Command", style="yellow")

    status_colors = {
        "READY_FOR_LOAD": "bold green",
        "NORMALIZATION_PROPOSED": "bold yellow",
        "SAMPLED": "yellow",
        "DOWNLOADED": "cyan",
        "PENDING": "dim white",
        "FAILED": "bold red"
    }

    for dataset in config.get("datasets", []):
        ds_id = dataset["id"]
        manifest = manifest_repo.get(ds_id)
        
        raw_status = "PENDING"
        ready = "[red]No[/red]"
        next_cmd = f"python3 main.py {ds_id}"
        
        if manifest:
            raw_status = manifest.status
            if "FAILED" in raw_status:
                status_display = f"[bold red]{raw_status}[/bold red]"
                next_cmd = f"python3 main.py {ds_id} (Retry)"
            else:
                color = status_colors.get(raw_status, "white")
                status_display = f"[{color}]{raw_status}[/{color}]"
                ready = "[green]Yes[/green]" if manifest.validation.is_human_approved else "[red]No[/red]"
                
                # Logic for next suggested command
                if raw_status == "DOWNLOADED":
                    next_cmd = f"python3 main.py {ds_id} -s"
                elif raw_status == "SAMPLED":
                    next_cmd = f"python3 main.py {ds_id} -n"
                elif raw_status == "NORMALIZATION_PROPOSED":
                    next_path = f"data/schemas/{ds_id}_target_schema.json"
                    next_cmd = f"Review {next_path} then -a"
                elif raw_status == "READY_FOR_LOAD":
                    next_cmd = "[bold green]COMPLETE[/bold green]"
        else:
            status_display = f"[{status_colors['PENDING']}]PENDING[/{status_colors['PENDING']}]"
        
        table.add_row(ds_id, status_display, ready, next_cmd)

    console.print("\n")
    console.print(table)
    console.print("\n[dim]Run 'python3 main.py --help' for all options.[/dim]")

def run_pipeline():
    parser = argparse.ArgumentParser(description="Elite Dangerous Data Pipeline")
    # Positional dataset argument
    parser.add_argument("dataset_pos", nargs='?', help="Dataset ID to process (positional)")
    
    # Flags with aliases
    parser.add_argument("-d", "--dataset", help="Dataset ID from config to process (flag override)")
    parser.add_argument("-u", "--url", help="Override Source URI (Download only)")
    parser.add_argument("-t", "--dest", help="Override Local Destination Path (Download only)")
    
    # Analyzer Phases
    parser.add_argument("-s", "--sample", action="store_true", help="Phase 1: Extract sample and raw schema")
    parser.add_argument("-n", "--normalize", action="store_true", help="Phase 2: Propose normalization strategy")
    parser.add_argument("-a", "--approve", action="store_true", help="Phase 4: Approve schema and cleanup")
    parser.add_argument("-l", "--load", action="store_true", help="Phase 3: Load data into database")
    
    # Automated flow
    parser.add_argument("-x", "--next", action="store_true", help="Auto-execute the next logical phase")
    
    # Status
    parser.add_argument("--status", action="store_true", help="Display global project status dashboard")
    parser.add_argument("--check", action="store_true", help="Verify infrastructure and database connectivity")
    
    # Lifecycle
    parser.add_argument("--delete", metavar="DATASET_ID", help="Delete all artifacts for a specific dataset")
    parser.add_argument("--clear", action="store_true", help="Global reset: Purge all data and the manifest")
    
    args = parser.parse_args()

    config = load_config()
    manifest_repo = LocalManifestRepository("data/manifest.json")
    
    # 0. Permission Check
    verify_permissions(config.get("base_download_dir", "data"))

    # Handle Infrastructure Check
    if args.check:
        console.print(Panel.fit("[bold blue]Infrastructure Verification[/bold blue]"))
        
        # 1. FS Check
        console.print("Checking Filesystem: [bold green]OK[/bold green]")
        
        # 2. DB Check
        console.print("Checking Database Connectivity...")
        success, msg = ping_database()
        if success:
            console.print(f"Database Status: [bold green]ONLINE[/bold green] ({msg})")
        else:
            console.print(f"Database Status: [bold red]OFFLINE[/bold red]")
            console.print(f"[dim]Reason: {msg}[/dim]")
            console.print("\n[bold yellow]Action Required:[/bold yellow] Run [cyan].scripts/setup_db.sh[/cyan] to start the database container.")
        return

    # Handle Global Clear
    if args.clear:
        console.print(Panel.fit("[bold red]GLOBAL RESET REQUESTED[/bold red]"))
        confirm = Prompt.ask("[bold red]WARNING:[/bold red] This will destroy ALL downloaded data, schemas, and the manifest. Type '[bold white]YES[/bold white]' to continue")
        if confirm == "YES":
            def remove_readonly(func, path, _):
                """Error handler to remove read-only files."""
                os.chmod(path, 0o660)
                func(path)

            for sub in ["downloads", "schemas", "samples"]:
                path = Path(f"data/{sub}")
                if path.exists():
                    console.print(f"Clearing {path}...")
                    shutil.rmtree(path, onerror=remove_readonly)
                    path.mkdir()
            # Reset manifest
            with open("data/manifest.json", "w") as f:
                f.write("{}")
            console.print("[bold green]✓ System cleared successfully.[/bold green]")
        else:
            console.print("[dim]Operation cancelled.[/dim]")
        return

    # Handle Targeted Delete
    if args.delete:
        ds_id = args.delete
        manifest = manifest_repo.get(ds_id)
        if not manifest:
            console.print(f"[bold red]Error:[/bold red] Dataset '{ds_id}' not found in manifest.")
            return
            
        if Confirm.ask(f"Are you sure you want to delete all artifacts for dataset '[cyan]{ds_id}[/cyan]'?"):
            if os.path.exists(manifest.local_filepath):
                console.print(f"Removing download: {manifest.local_filepath}")
                os.chmod(manifest.local_filepath, 0o660)
                os.remove(manifest.local_filepath)
            
            if manifest.metadata.schema_filepath and os.path.exists(manifest.metadata.schema_filepath):
                console.print(f"Removing schema: {manifest.metadata.schema_filepath}")
                os.remove(manifest.metadata.schema_filepath)
                
            if manifest.metadata.sample_filepath and os.path.exists(manifest.metadata.sample_filepath):
                console.print(f"Removing sample: {manifest.metadata.sample_filepath}")
                os.remove(manifest.metadata.sample_filepath)
            
            target_path = f"data/schemas/{ds_id}_target_schema.json"
            if os.path.exists(target_path):
                console.print(f"Removing target schema: {target_path}")
                os.remove(target_path)

            manifest_repo.delete(ds_id)
            console.print(f"[bold green]✓ Dataset '{ds_id}' artifacts removed.[/bold green]")
        return

    # Resolve Dataset ID
    # Priority: Positional > -d Flag > None
    dataset_id = args.dataset_pos if args.dataset_pos else args.dataset
    
    # If no arguments or just --status, show dashboard and exit
    if (len(sys.argv) <= 1 and not dataset_id) or args.status:
        console.print(Panel.fit("[bold blue]Elite Dangerous Data Pipeline[/bold blue]", subtitle="Hexagonal Orchestrator"))
        display_global_status(config, manifest_repo)
        return

    # If an action was requested but no dataset specified, check if we should default or error
    if not dataset_id:
        if args.next:
            # For --next without a dataset, pick the first one from config that isn't complete
            for ds in config.get("datasets", []):
                m = manifest_repo.get(ds["id"])
                if not m or not m.validation.is_human_approved:
                    dataset_id = ds["id"]
                    break
            if not dataset_id:
                console.print("[bold green]All datasets are complete![/bold green]")
                return
        else:
            console.print("[bold red]Error:[/bold red] You must specify a dataset ID to perform this action.")
            console.print("[dim]Example: python3 main.py spansh_systems_1day -s[/dim]")
            return

    target_dataset = next((d for d in config.get("datasets", []) if d["id"] == dataset_id), None)
    if not target_dataset:
        console.print(f"[bold red]Error:[/bold red] Dataset '{dataset_id}' not found in config.json")
        return

    # Initialize Services
    downloader_adapter = HttpDownloaderAdapter()
    analyzer_adapter = JsonAnalyzerAdapter()
    
    downloader_service = DownloaderService(manifest_repo, downloader_adapter)
    analyzer_service = AnalyzerService(manifest_repo, analyzer_adapter)
    loader_service = LoaderService(manifest_repo, PostgresAdapter())
    norm_service = NormalizationService(console)

    console.print(Panel.fit("[bold blue]Elite Dangerous Data Pipeline[/bold blue]", subtitle=dataset_id))

    try:
        manifest = manifest_repo.get(dataset_id)
        current_status = manifest.status if manifest else "PENDING"

        # Determine what to do
        do_download = False
        do_sample = args.sample
        do_normalize = args.normalize
        do_approve = args.approve
        do_load = args.load

        if args.next:
            if current_status == "PENDING": do_download = True
            elif current_status == "DOWNLOADED": do_sample = True
            elif current_status == "SAMPLED": do_normalize = True
            elif current_status == "NORMALIZATION_PROPOSED":
                console.print(f"\n[bold yellow]Action Required:[/bold yellow] Please review [cyan]data/schemas/{dataset_id}_target_schema.json[/cyan] then run with -a")
                return
            elif current_status == "READY_FOR_LOAD":
                console.print(f"\n[bold green]Success:[/bold green] {dataset_id} is already ready for loading.")
                return

        # Smart Chaining
        if do_normalize and current_status not in ["SAMPLED", "NORMALIZATION_PROPOSED", "READY_FOR_LOAD"]:
            do_sample = True
        
        if (do_sample or do_normalize) and current_status == "PENDING":
            do_download = True

        # --- EXECUTION ---

        # 1. Download
        is_explicit_download = not any([args.sample, args.normalize, args.approve, args.next])
        if do_download or (is_explicit_download and current_status == "PENDING"):
            source_uri = args.url if args.url else target_dataset["source_uri"]
            local_filepath = args.dest
            console.print(f"\n[bold yellow]Step: Download[/bold yellow] [cyan]{dataset_id}[/cyan]")
            manifest = downloader_service.download_dataset(dataset_id, source_uri, local_filepath)
            if manifest.status == "DOWNLOADED":
                console.print("[bold green]✓ Download Success![/bold green]")
            else:
                console.print(f"[bold blue]ℹ Info:[/bold blue] Dataset already downloaded and verified. Skipping.")
            current_status = manifest.status
        elif is_explicit_download and current_status != "PENDING":
             console.print(f"\n[bold blue]ℹ Info:[/bold blue] Dataset [cyan]{dataset_id}[/cyan] is already {current_status}. Skipping download.")

        # 2. Sample
        if do_sample:
            if current_status in ["SAMPLED", "NORMALIZATION_PROPOSED", "READY_FOR_LOAD"]:
                console.print(f"\n[bold blue]ℹ Info:[/bold blue] Dataset is already sampled. Skipping.")
            else:
                console.print(f"\n[bold yellow]Step: Sample[/bold yellow] [cyan]{dataset_id}[/cyan]...")
                manifest = analyzer_service.extract_sample(dataset_id)
                console.print(f"[bold green]✓ Sample & Raw Schema Created[/bold green]")
                current_status = manifest.status

        # 3. Normalize
        if do_normalize:
            if current_status in ["NORMALIZATION_PROPOSED", "READY_FOR_LOAD"]:
                console.print(f"\n[bold blue]ℹ Info:[/bold blue] Normalization already proposed. Skipping.")
            else:
                console.print(f"\n[bold yellow]Step: Normalize[/bold yellow] [cyan]{dataset_id}[/cyan]...")
                with open(manifest.metadata.schema_filepath, "r") as f:
                    raw_schema = json.load(f)
                
                target_schema = norm_service.propose_normalization(raw_schema)
                target_path = f"data/schemas/{dataset_id}_target_schema.json"
                with open(target_path, "w") as f:
                    json.dump(target_schema, f, indent=4)
                
                norm_service.visualize_proposal(dataset_id, target_schema)
                console.print(f"\n[bold yellow]Action Required:[/bold yellow] Review [cyan]{target_path}[/cyan].")
                current_status = "NORMALIZATION_PROPOSED"

        # 4. Approve
        if do_approve:
            if current_status == "READY_FOR_LOAD":
                console.print(f"\n[bold blue]ℹ Info:[/bold blue] Dataset is already approved and ready for load.")
            else:
                console.print(f"\n[bold yellow]Step: Approve[/bold yellow] [cyan]{dataset_id}[/cyan]...")
                manifest = analyzer_service.approve_schema(dataset_id)
                console.print(f"[bold green]✓ Schema Approved![/bold green]")
                current_status = manifest.status

        # 5. Load
        if do_load:
            if current_status == "LOADED":
                console.print(f"\n[bold blue]ℹ Info:[/bold blue] Dataset is already loaded.")
            else:
                # DB Check first
                db_ok, db_msg = ping_database()
                if not db_ok:
                    raise RuntimeError(f"Database offline: {db_msg}")

                console.print(f"\n[bold yellow]Step: Load to Database[/bold yellow] [cyan]{dataset_id}[/cyan]...")
                manifest = loader_service.load_dataset(dataset_id)
                console.print(f"[bold green]✓ Load Success![/bold green] Total rows: {manifest.metadata.estimated_rows}")
                current_status = manifest.status

        # Suggested Next Step
        if current_status == "DOWNLOADED":
            console.print(f"\n[bold yellow]Next Step:[/bold yellow] python3 main.py {dataset_id} -s")
        elif current_status == "SAMPLED":
            console.print(f"\n[bold yellow]Next Step:[/bold yellow] python3 main.py {dataset_id} -n")
        elif current_status == "NORMALIZATION_PROPOSED":
            console.print(f"\n[bold yellow]Next Step:[/bold yellow] python3 main.py {dataset_id} -a")
        elif current_status == "READY_FOR_LOAD":
            console.print(f"\n[bold yellow]Next Step:[/bold yellow] python3 main.py {dataset_id} -l")

    except Exception as e:
        console.print(f"\n[bold red]Pipeline Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    run_pipeline()
