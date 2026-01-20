"""
TuneSleuth CLI

Command-line interface for scanning and analyzing music libraries.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from tunesleuth_core import Library, PatternDetector, Scanner, ScanProgress

console = Console()


def print_banner() -> None:
    """Print the TuneSleuth banner."""
    banner = """
╔╦╗┬ ┬┌┐┌┌─┐╔═╗┬  ┌─┐┬ ┬┌┬┐┬ ┬
 ║ │ ││││├┤ ╚═╗│  ├┤ │ │ │ ├─┤
 ╩ └─┘┘└┘└─┘╚═╝┴─┘└─┘└─┘ ┴ ┴ ┴
    """
    console.print(banner, style="bold cyan")
    console.print("Your music library's private investigator", style="dim italic")
    console.print()


@click.group()
@click.version_option(version="0.1.0", prog_name="TuneSleuth")
def main():
    """
    TuneSleuth - Your music library's private investigator.

    Analyzes folder structures and filenames, infers conventions,
    and helps organize your music into a clean, logical library.
    """
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def scan(path: Path, verbose: bool) -> None:
    """
    Scan a music directory and report library statistics.

    PATH is the root directory of your music library to scan.
    """
    print_banner()

    console.print(f"🔍 Scanning: [bold]{path}[/bold]")
    console.print()

    library: Library | None = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)

        def on_progress(scan_progress: ScanProgress) -> None:
            if scan_progress.total_files_found > 0:
                progress.update(
                    task,
                    total=scan_progress.total_files_found,
                    completed=scan_progress.files_scanned,
                    description=f"Scanning: {scan_progress.current_file or '...'}",
                )

        scanner = Scanner(progress_callback=on_progress)
        library = scanner.scan(path)

    console.print()

    # Calculate and display stats
    stats = library.calculate_stats()

    # Summary panel
    summary_text = (
        f"[bold cyan]{stats.total_tracks}[/bold cyan] tracks found\n"
        f"[bold]{stats.total_size_mb:.1f} MB[/bold] total size\n"
        f"[bold]{stats.total_duration_hours:.1f} hours[/bold] of music"
    )
    console.print(Panel(summary_text, title="📊 Library Summary", border_style="cyan"))
    console.print()

    # Metadata coverage
    table = Table(title="🏷️ Metadata Coverage", show_header=True, header_style="bold")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Tracks with complete tags", f"{stats.tracks_with_tags}")
    table.add_row("Tracks missing tags", f"{stats.tracks_without_tags}")
    table.add_row(
        "Average tag completeness",
        f"{stats.average_tag_completeness * 100:.0f}%",
    )
    table.add_row("Unique artists", f"{stats.unique_artists}")
    table.add_row("Unique albums", f"{stats.unique_albums}")
    table.add_row("Unique genres", f"{stats.unique_genres}")

    console.print(table)
    console.print()

    # Folder structure
    console.print(f"📁 [bold]Folder Structure:[/bold] {stats.folder_count} folders, "
                  f"max depth: {stats.max_folder_depth}")

    if verbose and library.tracks:
        console.print()
        console.print("[bold]Sample Tracks:[/bold]")
        for track in library.tracks[:5]:
            tag_status = "✅" if track.has_complete_tags else "⚠️"
            console.print(f"  {tag_status} {track.display_artist} - {track.display_title}")

    console.print()
    console.print("[dim]Run 'tunesleuth analyze' for pattern detection.[/dim]")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--explain", "-e", is_flag=True, help="Show detailed pattern explanations")
@click.option("--verbose", "-v", is_flag=True, help="Show all detected patterns")
def analyze(path: Path, explain: bool, verbose: bool) -> None:
    """
    Analyze a music library to detect naming patterns and conventions.

    PATH is the root directory of your music library to analyze.
    """
    print_banner()

    console.print(f"🔍 Analyzing: [bold]{path}[/bold]")
    console.print()

    # First scan the library
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning library...", total=None)
        scanner = Scanner()
        library = scanner.scan(path)
        progress.update(task, description=f"Scanned {len(library)} tracks")

    console.print(f"📚 Found [bold]{len(library)}[/bold] tracks")
    console.print()

    # Analyze patterns
    with console.status("Detecting patterns..."):
        detector = PatternDetector()
        analysis = detector.analyze(library)

    # Display filename patterns
    if analysis.filename_patterns:
        console.print("[bold cyan]📄 Filename Patterns[/bold cyan]")
        console.print()

        for pattern in analysis.filename_patterns:
            if not verbose and pattern.confidence < 0.1:
                continue

            confidence_color = _get_confidence_color(pattern.confidence)
            badge = f"[{confidence_color}]{pattern.confidence_label}[/{confidence_color}]"

            console.print(
                f"  {badge} [bold]{pattern.description}[/bold] "
                f"({pattern.matching_tracks}/{pattern.total_tracks} files)"
            )

            if explain:
                console.print(f"    [dim]{pattern.explanation}[/dim]")
                if pattern.examples:
                    console.print("    [dim]Examples:[/dim]")
                    for example in pattern.examples[:3]:
                        console.print(f"      • {example}")

            console.print()

    # Display folder patterns
    if analysis.folder_patterns:
        console.print("[bold cyan]📁 Folder Structure Patterns[/bold cyan]")
        console.print()

        for pattern in analysis.folder_patterns:
            if not verbose and pattern.confidence < 0.1:
                continue

            confidence_color = _get_confidence_color(pattern.confidence)
            badge = f"[{confidence_color}]{pattern.confidence_label}[/{confidence_color}]"

            console.print(
                f"  {badge} [bold]{pattern.description}[/bold] "
                f"({pattern.matching_tracks} tracks)"
            )

            if explain:
                console.print(f"    [dim]{pattern.explanation}[/dim]")
                if pattern.examples:
                    console.print("    [dim]Examples:[/dim]")
                    for example in pattern.examples[:3]:
                        console.print(f"      • {example}")

            console.print()

    # Display special patterns
    if analysis.special_patterns:
        console.print("[bold cyan]✨ Special Patterns[/bold cyan]")
        console.print()

        for pattern in analysis.special_patterns:
            if not verbose and pattern.confidence < 0.1:
                continue

            confidence_color = _get_confidence_color(pattern.confidence)
            badge = f"[{confidence_color}]{pattern.confidence_label}[/{confidence_color}]"

            console.print(f"  {badge} [bold]{pattern.description}[/bold]")

            if explain:
                console.print(f"    [dim]{pattern.explanation}[/dim]")

            console.print()

    # Summary
    primary_filename = analysis.primary_filename_pattern
    primary_folder = analysis.primary_folder_pattern

    console.print(Panel(
        _build_summary(primary_filename, primary_folder),
        title="🎯 Analysis Summary",
        border_style="green",
    ))


def _get_confidence_color(confidence: float) -> str:
    """Get color for confidence level."""
    if confidence >= 0.9:
        return "bold green"
    elif confidence >= 0.75:
        return "green"
    elif confidence >= 0.5:
        return "yellow"
    elif confidence >= 0.25:
        return "orange1"
    else:
        return "red"


def _build_summary(primary_filename, primary_folder) -> str:
    """Build summary text for analysis results."""
    lines = []

    if primary_filename:
        lines.append(
            f"[bold]Primary filename pattern:[/bold] "
            f"{primary_filename.description} ({primary_filename.confidence_percent:.0f}%)"
        )
    else:
        lines.append("[bold]Primary filename pattern:[/bold] [dim]None detected[/dim]")

    if primary_folder:
        lines.append(
            f"[bold]Primary folder structure:[/bold] "
            f"{primary_folder.description} ({primary_folder.confidence_percent:.0f}%)"
        )
    else:
        lines.append("[bold]Primary folder structure:[/bold] [dim]None detected[/dim]")

    lines.append("")
    lines.append("[dim]TuneSleuth can use these patterns to organize your library.[/dim]")
    lines.append("[dim]Coming soon: tunesleuth organize --dry-run[/dim]")

    return "\n".join(lines)


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, default=True, help="Preview changes without applying")
def organize(path: Path, dry_run: bool) -> None:
    """
    Organize music library based on detected patterns.

    [Coming Soon] This command will reorganize files based on
    detected or specified patterns.

    PATH is the root directory of your music library.
    """
    print_banner()

    console.print("[yellow]⚠️ This command is coming soon![/yellow]")
    console.print()
    console.print("The organize command will:")
    console.print("  • Detect your library's naming patterns")
    console.print("  • Suggest a clean folder structure")
    console.print("  • Preview all changes with --dry-run")
    console.print("  • Safely reorganize files when you're ready")
    console.print()
    console.print("For now, use 'tunesleuth analyze' to see detected patterns.")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--source", type=click.Choice(["musicbrainz"]), default="musicbrainz", help="Metadata source")
@click.option("--limit", type=int, default=3, help="Number of matches to show per track")
@click.option("--dry-run", is_flag=True, help="Preview matches without writing tags")
@click.option("--auto", is_flag=True, help="Automatically apply best match (requires confidence >= 90%)")
def tag(path: Path, source: str, limit: int, dry_run: bool, auto: bool) -> None:
    """
    Fetch and update ID3 tags from online metadata sources.

    PATH is the root directory of your music library.

    This command looks up tracks in MusicBrainz and shows potential matches
    with confidence scores. Use --auto to automatically apply high-confidence matches.
    """
    print_banner()

    console.print(f"🔍 Looking up metadata from [bold]{source}[/bold]: {path}")
    console.print()

    # Scan library
    with console.status("Scanning library..."):
        scanner = Scanner()
        library = scanner.scan(path)

    if not library.tracks:
        console.print("[yellow]No tracks found in library.[/yellow]")
        return

    console.print(f"📚 Found [bold]{len(library)}[/bold] tracks")
    console.print()

    # Run pattern detection to infer artist/title from filenames
    with console.status("Analyzing patterns..."):
        detector = PatternDetector()
        detector.analyze(library)

    # Initialize metadata client
    from tunesleuth_core import MusicBrainzClient

    client = MusicBrainzClient(contact="tunesleuth@example.com")

    updated_count = 0
    skipped_count = 0

    # Process each track
    for idx, track in enumerate(library.tracks, 1):
        # Skip tracks with complete tags unless they need improvement
        if track.has_complete_tags and not auto:
            skipped_count += 1
            continue

        console.print(f"[dim]{idx}/{len(library)}[/dim] [bold]{track.filename}[/bold]")

        # Look up metadata
        with console.status(f"Searching {source}..."):
            matches = client.lookup_track(track, limit=limit)

        if not matches:
            console.print("  [yellow]No matches found[/yellow]")
            console.print()
            continue

        # Display matches
        console.print(f"  Found [bold]{len(matches)}[/bold] potential matches:")
        for i, match in enumerate(matches, 1):
            confidence_color = _get_confidence_color(match.confidence)
            console.print(
                f"    [{confidence_color}]{i}. {match.artist} - {match.title}[/{confidence_color}] "
                f"({match.confidence * 100:.0f}%)"
            )
            if match.album:
                console.print(f"       Album: {match.album}")
            if match.year:
                console.print(f"       Year: {match.year}")

        # Auto-apply if requested and confidence is high
        if auto and matches[0].confidence >= 0.9:
            console.print(f"  [green]✓ Auto-applying best match ({matches[0].confidence * 100:.0f}% confidence)[/green]")
            if not dry_run:
                # TODO: Write tags to file (implement in next phase)
                console.print("  [dim](Tag writing not yet implemented)[/dim]")
            updated_count += 1
        elif not auto:
            console.print("  [dim]Use --auto to apply matches automatically[/dim]")

        console.print()

    # Summary
    console.print(Panel(
        f"[bold]Lookup Complete[/bold]\n\n"
        f"Tracks processed: {len(library) - skipped_count}\n"
        f"Tracks skipped (already tagged): {skipped_count}\n"
        f"Potential updates: {updated_count}",
        title="📊 Summary",
        border_style="green",
    ))

    if dry_run:
        console.print("\n[dim]This was a dry run. No tags were modified.[/dim]")
    else:
        console.print("\n[yellow]Note: Tag writing is not yet implemented.[/yellow]")
        console.print("[dim]Matches are shown for preview only.[/dim]")


if __name__ == "__main__":
    main()
