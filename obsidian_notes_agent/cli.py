#!/usr/bin/env python3
"""CLI entry point for the Obsidian Notes Agent package."""

import sys
import glob as glob_module
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from dotenv import load_dotenv

from obsidian_notes_agent.config import get_settings
from obsidian_notes_agent.agent import NotesAgent

# Load environment variables
load_dotenv()

app = typer.Typer(help="Obsidian Notes Agent - AI-powered note management")
console = Console()


@app.command()
def chat(
    reindex: bool = typer.Option(
        False,
        "--reindex",
        help="Rebuild the vector store before starting"
    )
):
    """Start an interactive chat session with the notes agent."""
    try:
        settings = get_settings()
        agent = NotesAgent(settings)

        # Check if vault exists
        if not settings.obsidian_vault_path.exists():
            console.print(
                f"[red]Error: Vault path does not exist: {settings.obsidian_vault_path}[/red]"
            )
            console.print("[yellow]Please set OBSIDIAN_VAULT_PATH in your .env file[/yellow]")
            sys.exit(1)

        # Initialize vector store if requested or if it doesn't exist
        if reindex or not settings.vector_store_path.exists():
            agent.initialize_vector_store()

        # Start chat
        agent.chat()

    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        console.print("[yellow]Please check your .env file[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask the agent"),
    reindex: bool = typer.Option(
        False,
        "--reindex",
        help="Rebuild the vector store before querying"
    )
):
    """Ask the agent a single question and exit."""
    try:
        settings = get_settings()
        agent = NotesAgent(settings)

        if reindex or not settings.vector_store_path.exists():
            agent.initialize_vector_store()

        response = agent.run(question)
        console.print(response)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def ingest(
    source: str = typer.Argument(..., help="URL or file path to ingest"),
    title: str = typer.Option(None, "--title", "-t", help="Custom title for the note"),
    reindex: bool = typer.Option(
        False,
        "--reindex",
        help="Rebuild the vector store after ingestion"
    )
):
    """Ingest content from a URL or file and create a note in Obsidian.

    Examples:
        notes ingest https://example.com/article
        notes ingest /path/to/document.pdf --title "My Paper"
        notes ingest ~/Downloads/presentation.pptx
    """
    try:
        settings = get_settings()

        # Check if vault exists
        if not settings.obsidian_vault_path.exists():
            console.print(
                f"[red]Error: Vault path does not exist: {settings.obsidian_vault_path}[/red]"
            )
            console.print("[yellow]Please set OBSIDIAN_VAULT_PATH in your .env file[/yellow]")
            sys.exit(1)

        agent = NotesAgent(settings)

        # Ensure vector store exists for related note suggestions
        if not settings.vector_store_path.exists():
            console.print("[yellow]Vector store not found. Initializing...[/yellow]")
            agent.initialize_vector_store()

        console.print(f"\n[cyan]Ingesting content from:[/cyan] {source}")
        if title:
            console.print(f"[cyan]Custom title:[/cyan] {title}")
        console.print()

        # Build the query for the agent
        if title:
            query_text = f'Ingest content from "{source}" and title it "{title}"'
        else:
            query_text = f'Ingest content from "{source}"'

        # Run the agent to ingest content
        response = agent.run(query_text)

        # Display the response
        from rich.markdown import Markdown
        console.print(Markdown(response))

        # Optionally reindex
        if reindex:
            console.print("\n[yellow]Reindexing vector store...[/yellow]")
            agent.initialize_vector_store()
            console.print("[green]✓ Vector store updated[/green]")

        console.print("\n[green]✓ Content ingestion complete![/green]")

    except ValueError as e:
        console.print(f"\n[red]Configuration error: {e}[/red]")
        console.print("[yellow]Please check your .env file[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@app.command()
def batch(
    sources: List[str] = typer.Argument(
        None,
        help="URLs or file paths to ingest (supports glob patterns like *.pdf). "
             "Required if --file is not provided."
    ),
    file: Optional[Path] = typer.Option(
        None,
        "--file", "-f",
        help="File containing URLs/paths to ingest (one per line). "
             "Required if no sources are provided as arguments."
    ),
    reindex: bool = typer.Option(
        False,
        "--reindex",
        help="Rebuild the vector store after all ingestions"
    ),
    continue_on_error: bool = typer.Option(
        True,
        "--continue-on-error/--stop-on-error",
        help="Continue processing if one source fails"
    )
):
    """Batch ingest multiple URLs or files at once.

    Examples:
        notes batch https://example.com/a https://example.com/b
        notes batch ~/Documents/*.pdf
        notes batch --file urls.txt
        notes batch "~/Papers/*.pdf" "~/Articles/*.md"
    """
    try:
        settings = get_settings()

        # Check if vault exists
        if not settings.obsidian_vault_path.exists():
            console.print(
                f"[red]Error: Vault path does not exist: {settings.obsidian_vault_path}[/red]"
            )
            console.print("[yellow]Please set OBSIDIAN_VAULT_PATH in your .env file[/yellow]")
            sys.exit(1)

        # Collect all sources to process
        all_sources: List[str] = []

        # Add sources from command line arguments
        if sources:
            for source in sources:
                # Check if it's a glob pattern for local files
                if not source.startswith(('http://', 'https://')) and ('*' in source or '?' in source):
                    # Expand glob pattern
                    expanded = Path(source).expanduser()
                    matches = glob_module.glob(str(expanded), recursive=True)
                    if matches:
                        all_sources.extend(sorted(matches))
                    else:
                        console.print(f"[yellow]Warning: No files matched pattern: {source}[/yellow]")
                else:
                    # Expand ~ for regular file paths
                    if not source.startswith(('http://', 'https://')):
                        source = str(Path(source).expanduser())
                    all_sources.append(source)

        # Add sources from file
        if file:
            if not file.exists():
                console.print(f"[red]Error: File not found: {file}[/red]")
                sys.exit(1)

            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Expand ~ for file paths
                        if not line.startswith(('http://', 'https://')):
                            line = str(Path(line).expanduser())
                        all_sources.append(line)

        if not all_sources:
            console.print("[red]Error: No sources provided. Use arguments or --file option.[/red]")
            console.print("\nExamples:")
            console.print("  notes batch https://example.com/article1 https://example.com/article2")
            console.print("  notes batch ~/Documents/*.pdf")
            console.print("  notes batch --file urls.txt")
            sys.exit(1)

        # Initialize agent
        agent = NotesAgent(settings)

        # Ensure vector store exists
        if not settings.vector_store_path.exists():
            console.print("[yellow]Vector store not found. Initializing...[/yellow]")
            agent.initialize_vector_store()

        console.print(f"\n[bold cyan]Batch Ingestion[/bold cyan]")
        console.print(f"Processing {len(all_sources)} source(s)...\n")

        # Track results
        results = {'success': [], 'failed': []}

        # Process each source with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Ingesting...", total=len(all_sources))

            for i, source in enumerate(all_sources, 1):
                progress.update(task, description=f"[{i}/{len(all_sources)}] {source[:50]}...")

                try:
                    query_text = f'Ingest content from "{source}"'
                    response = agent.run(query_text)
                    results['success'].append({'source': source, 'response': response})
                except Exception as e:
                    error_msg = str(e)
                    results['failed'].append({'source': source, 'error': error_msg})
                    if not continue_on_error:
                        progress.stop()
                        console.print(f"\n[red]Error processing {source}: {error_msg}[/red]")
                        console.print("[yellow]Stopping batch processing (use --continue-on-error to skip failures)[/yellow]")
                        break

                progress.advance(task)

        # Display results summary
        console.print("\n[bold]Results Summary[/bold]")

        # Success table
        if results['success']:
            success_table = Table(title=f"✓ Successfully Ingested ({len(results['success'])})")
            success_table.add_column("Source", style="green")
            for item in results['success']:
                # Truncate long sources
                source_display = item['source']
                if len(source_display) > 80:
                    source_display = "..." + source_display[-77:]
                success_table.add_row(source_display)
            console.print(success_table)

        # Failed table
        if results['failed']:
            failed_table = Table(title=f"✗ Failed ({len(results['failed'])})")
            failed_table.add_column("Source", style="red")
            failed_table.add_column("Error", style="dim")
            for item in results['failed']:
                source_display = item['source']
                if len(source_display) > 50:
                    source_display = "..." + source_display[-47:]
                error_display = item['error'][:50] + "..." if len(item['error']) > 50 else item['error']
                failed_table.add_row(source_display, error_display)
            console.print(failed_table)

        # Final stats
        console.print(f"\n[bold]Total:[/bold] {len(results['success'])} succeeded, {len(results['failed'])} failed")

        # Optionally reindex
        if reindex and results['success']:
            console.print("\n[yellow]Reindexing vector store...[/yellow]")
            agent.initialize_vector_store()
            console.print("[green]✓ Vector store updated[/green]")

        if results['success']:
            console.print("\n[green]✓ Batch ingestion complete![/green]")
        else:
            console.print("\n[red]✗ No sources were successfully ingested[/red]")
            sys.exit(1)

    except ValueError as e:
        console.print(f"\n[red]Configuration error: {e}[/red]")
        console.print("[yellow]Please check your .env file[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@app.command()
def reindex():
    """Rebuild the vector store index from all notes."""
    try:
        settings = get_settings()
        agent = NotesAgent(settings)
        agent.initialize_vector_store()
        console.print("[green]Vector store rebuilt successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def config():
    """Configure API key and Obsidian vault path interactively."""
    import os
    from pathlib import Path

    console.print("\n[bold cyan]Obsidian Notes Agent Configuration[/bold cyan]\n")
    console.print("This will create/update your configuration file.\n")

    # Determine config location
    config_dir = Path.home() / ".config" / "obsidian-notes-agent"
    config_file = config_dir / "config.env"

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Load existing config if it exists
    existing_api_key = None
    existing_vault_path = None

    if config_file.exists():
        with open(config_file, 'r') as f:
            for line in f:
                if line.startswith('ANTHROPIC_API_KEY='):
                    existing_api_key = line.split('=', 1)[1].strip()
                elif line.startswith('OBSIDIAN_VAULT_PATH='):
                    existing_vault_path = line.split('=', 1)[1].strip()

    # Prompt for API key
    console.print("[cyan]Anthropic API Key[/cyan]")
    if existing_api_key:
        console.print(f"Current: {existing_api_key[:20]}..." if len(existing_api_key) > 20 else f"Current: {existing_api_key}")
        console.print("[dim]Press Enter to keep current value, or enter a new key:[/dim]")
    else:
        console.print("Get your API key from: [link]https://console.anthropic.com/[/link]")

    api_key_input = input("API Key: ").strip()
    api_key = api_key_input if api_key_input else existing_api_key

    if not api_key:
        console.print("[red]Error: API key is required[/red]")
        sys.exit(1)

    # Prompt for vault path
    console.print("\n[cyan]Obsidian Vault Path[/cyan]")
    if existing_vault_path:
        console.print(f"Current: {existing_vault_path}")
        console.print("[dim]Press Enter to keep current value, or enter a new path:[/dim]")
    else:
        console.print("Enter the full path to your Obsidian vault directory:")

    vault_input = input("Vault Path: ").strip()
    vault_path = vault_input if vault_input else existing_vault_path

    if not vault_path:
        console.print("[red]Error: Vault path is required[/red]")
        sys.exit(1)

    # Expand ~ to home directory
    vault_path = str(Path(vault_path).expanduser())

    # Verify vault exists
    if not Path(vault_path).exists():
        console.print(f"[yellow]Warning: Path does not exist: {vault_path}[/yellow]")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            console.print("[yellow]Configuration cancelled[/yellow]")
            sys.exit(1)

    # Write config file
    with open(config_file, 'w') as f:
        f.write(f"ANTHROPIC_API_KEY={api_key}\n")
        f.write(f"OBSIDIAN_VAULT_PATH={vault_path}\n")
        f.write(f"CLAUDE_MODEL=claude-sonnet-4-5-20250929\n")
        f.write(f"VECTOR_STORE_PATH={config_dir}/chroma_db\n")

    # Set restrictive permissions (Unix only)
    try:
        os.chmod(config_file, 0o600)
    except:
        pass  # Windows doesn't support chmod

    console.print(f"\n[green]✓ Configuration saved to {config_file}[/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Run [cyan]notes chat[/cyan] to start an interactive session")
    console.print("2. Or run [cyan]notes info[/cyan] to verify your configuration\n")


@app.command()
def info():
    """Display configuration information."""
    try:
        settings = get_settings()

        console.print("\n[bold cyan]Obsidian Notes Agent Configuration[/bold cyan]\n")
        console.print(f"Vault Path: {settings.obsidian_vault_path}")
        console.print(f"Vector Store: {settings.vector_store_path}")
        console.print(f"Model: {settings.claude_model}")
        console.print(f"Temperature: {settings.temperature}")
        console.print(f"Max Iterations: {settings.max_iterations}")

        # Check vault
        if settings.obsidian_vault_path.exists():
            from obsidian_notes_agent.utils.obsidian import ObsidianVault
            vault = ObsidianVault(settings.obsidian_vault_path)
            notes = vault.get_all_notes()
            console.print(f"\n[green]✓[/green] Vault found with {len(notes)} notes")
        else:
            console.print(f"\n[red]✗[/red] Vault not found")

        # Check vector store
        if settings.vector_store_path.exists():
            console.print(f"[green]✓[/green] Vector store exists")
        else:
            console.print(f"[yellow]![/yellow] Vector store not initialized (run with --reindex)")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
