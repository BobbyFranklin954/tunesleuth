# 🔍 TuneSleuth

**Your music library's private investigator**

[![CI](https://github.com/bobbyfranklin954/tunesleuth/actions/workflows/ci.yml/badge.svg)](https://github.com/bobbyfranklin954/tunesleuth/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

TuneSleuth analyzes folder structures and filenames, infers conventions, enriches tracks with accurate metadata, and organizes your music into a clean, logical library—without guesswork or heavy-handed renaming.

<p align="center">
  <img src="docs/screenshot.png" alt="TuneSleuth Screenshot" width="800">
</p>

## ✨ Features

- **Smart Pattern Detection** — Automatically detects naming conventions in your library (e.g., `Artist - Album - Track`, numbered prefixes, folder hierarchies)
- **Confidence Scoring** — Every detected pattern comes with a confidence score and human-readable explanation
- **Non-Destructive** — Analyzes and suggests changes without modifying your files until you approve
- **Dual Interface** — Full-featured GUI for visual exploration, plus CLI for scripting and automation
- **ID3 Tag Analysis** — Scans existing metadata and identifies gaps in your tag coverage

### Coming Soon

- 🏷️ **Online Metadata Lookup** — Connect to MusicBrainz, Discogs, and other sources
- 📁 **Smart Organization** — Reorganize files based on detected or specified patterns
- 🎨 **Album Artwork** — Fetch and embed missing cover art

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/bobbyfranklin954/tunesleuth.git
cd tunesleuth

# Install with pip (recommended: use a virtual environment)
pip install -e ".[dev]"
```

### Requirements

- Python 3.10+
- PyQt6 (for GUI)
- macOS, Windows, or Linux

### Launch the GUI

```bash
tunesleuth-gui
```

Or run directly:

```bash
python -m tunesleuth_gui
```

### Use the CLI

```bash
# Scan a music folder and view statistics
tunesleuth scan ~/Music

# Analyze patterns with detailed explanations
tunesleuth analyze ~/Music --explain

# Quick analysis
tunesleuth analyze ~/Music
```

## 📖 Usage

### GUI Workflow

1. **Launch** — Open TuneSleuth and you'll see the welcome screen
2. **Select Folder** — Click "Select Music Folder" to choose your library
3. **Scan** — Watch as TuneSleuth scans your files and extracts metadata
4. **Analyze** — View detected patterns with confidence scores
5. **Explore** — Browse your library organized by folders and tracks

### CLI Commands

#### `tunesleuth scan <path>`

Scan a directory and display library statistics.

```bash
$ tunesleuth scan ~/Music

📊 Library Summary
─────────────────────
1,247 tracks found
4.2 GB total size
86.3 hours of music

🏷️ Metadata Coverage
─────────────────────
Tracks with complete tags: 892
Tracks missing tags: 355
Average tag completeness: 72%
```

**Options:**
- `-v, --verbose` — Show sample tracks and additional details

#### `tunesleuth analyze <path>`

Detect naming patterns and folder structures.

```bash
$ tunesleuth analyze ~/Music --explain

📄 Filename Patterns
  [High] Artist - Title (847/1247 files)
    847 of 1247 files (68%) match the 'Artist - Title' naming pattern.
    Examples:
      • Pink Floyd - Comfortably Numb.mp3
      • Led Zeppelin - Stairway to Heaven.mp3
      • Queen - Bohemian Rhapsody.mp3

📁 Folder Structure Patterns
  [Very High] Artist / Album structure (1189 tracks)
    Detected 45 artist folders containing 127 album folders.

🎯 Analysis Summary
───────────────────
Primary filename pattern: Artist - Title (68%)
Primary folder structure: Artist / Album structure (95%)
```

**Options:**
- `-e, --explain` — Show detailed pattern explanations with examples
- `-v, --verbose` — Include low-confidence patterns in output

#### `tunesleuth organize <path>` *(Coming Soon)*

Reorganize files based on detected patterns.

```bash
tunesleuth organize ~/Music --dry-run  # Preview changes
tunesleuth organize ~/Music            # Apply changes
```

#### `tunesleuth tag` *(Coming Soon)*

Fetch and update ID3 tags from online sources.

```bash
tunesleuth tag --source musicbrainz
```

## 🏗️ Architecture

TuneSleuth is structured as a monorepo with three packages:

```
tunesleuth/
├── tunesleuth_core/    # Shared library (pattern detection, file analysis)
│   ├── models.py       # Data models (Track, Album, Library)
│   ├── scanner.py      # File scanning and ID3 extraction
│   └── patterns.py     # Pattern detection engine
├── tunesleuth_cli/     # CLI interface (Click-based)
│   └── __main__.py     # Command implementations
├── tunesleuth_gui/     # PyQt6 GUI application
│   ├── main_window.py  # Main application window
│   ├── results_view.py # Pattern results visualization
│   └── styles.py       # Visual theming
└── tests/              # Test suite
```

### Core Concepts

- **Library** — Represents your entire music collection with tracks, stats, and groupings
- **Track** — A single audio file with both ID3 metadata and inferred information
- **PatternDetector** — Analyzes filenames and folders to detect naming conventions
- **PatternMatch** — A detected pattern with confidence score and explanation

## 🎨 Design Philosophy

TuneSleuth embraces a **detective/investigator** metaphor:

- **Sleuthing over brute force** — We analyze and infer rather than blindly rename
- **Explainability** — Every suggestion comes with reasoning you can understand
- **Confidence scoring** — Know how certain we are about each detection
- **Non-destructive first** — Preview everything before making changes

### UI Aesthetic

- **Color palette**: Deep navy (#1a1f36) with warm amber accents (#f59e0b)
- **Typography**: JetBrains Mono for file paths, Inter for UI text
- **Visual motif**: Magnifying glass + audio waveform

## 🧪 Development

### Setup Development Environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/bobbyfranklin954/tunesleuth.git
cd tunesleuth
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Format code
ruff format .
```

### Running from Source

```bash
# Run CLI
python -m tunesleuth_cli scan ~/Music

# Run GUI
python -m tunesleuth_gui
```

### Project Structure

| Package | Purpose |
|---------|---------|
| `tunesleuth_core` | Core library with models, scanner, and pattern detection |
| `tunesleuth_cli` | Command-line interface using Click and Rich |
| `tunesleuth_gui` | PyQt6 graphical interface |

## 📋 Roadmap

### v0.1.0 (Current)
- [x] File scanning with ID3 extraction
- [x] Pattern detection with confidence scoring
- [x] CLI with scan and analyze commands
- [x] GUI with folder selection and results view

### v0.2.0
- [ ] MusicBrainz integration for metadata lookup
- [ ] ID3 tag writing capabilities
- [ ] Batch tag suggestions

### v0.3.0
- [ ] File organization/renaming with preview
- [ ] Custom pattern rules
- [ ] Album artwork fetching

### v1.0.0
- [ ] Full metadata enrichment pipeline
- [ ] Undo/history for changes
- [ ] Homebrew installation for macOS
- [ ] Windows installer

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Mutagen](https://mutagen.readthedocs.io/) for audio metadata handling
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

---

<p align="center">
  <i>Built with 🔍 by the TuneSleuth Team</i>
</p>
