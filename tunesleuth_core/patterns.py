"""
TuneSleuth Pattern Detection Engine

Analyzes filenames and folder structures to detect naming conventions
and patterns in music libraries, with confidence scoring and explainability.
"""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from tunesleuth_core.models import Library, Track


class PatternType(Enum):
    """Types of patterns that can be detected in music libraries."""

    # Filename patterns
    ARTIST_TITLE = auto()  # Artist - Title.mp3
    ARTIST_ALBUM_TITLE = auto()  # Artist - Album - Title.mp3
    TRACK_TITLE = auto()  # 01 - Title.mp3 or 01. Title.mp3
    TRACK_ARTIST_TITLE = auto()  # 01 - Artist - Title.mp3
    TITLE_ONLY = auto()  # Title.mp3

    # Folder structure patterns
    FOLDER_ARTIST_ALBUM = auto()  # Artist/Album/tracks
    FOLDER_ARTIST_ALBUM_DISC = auto()  # Artist/Album/Disc N/tracks
    FOLDER_ALBUM_ONLY = auto()  # Album/tracks (flat artist)
    FOLDER_FLAT = auto()  # All tracks in one folder

    # Special patterns
    COMPILATION = auto()  # Various Artists compilation
    NUMBERED_PREFIX = auto()  # Files have track number prefix
    YEAR_IN_FOLDER = auto()  # Year in folder name: Artist/Album (Year)


@dataclass
class PatternMatch:
    """Represents a detected pattern with confidence scoring."""

    pattern_type: PatternType
    confidence: float  # 0.0 to 1.0
    matching_tracks: int
    total_tracks: int
    description: str
    explanation: str
    examples: list[str] = field(default_factory=list)

    @property
    def confidence_percent(self) -> float:
        """Return confidence as a percentage."""
        return self.confidence * 100

    @property
    def confidence_label(self) -> str:
        """Return a human-readable confidence label."""
        if self.confidence >= 0.9:
            return "Very High"
        elif self.confidence >= 0.75:
            return "High"
        elif self.confidence >= 0.5:
            return "Medium"
        elif self.confidence >= 0.25:
            return "Low"
        else:
            return "Very Low"

    def __str__(self) -> str:
        return f"{self.description} ({self.confidence_percent:.0f}% confidence)"


@dataclass
class PatternAnalysis:
    """Complete analysis results for a library."""

    library: Library
    filename_patterns: list[PatternMatch] = field(default_factory=list)
    folder_patterns: list[PatternMatch] = field(default_factory=list)
    special_patterns: list[PatternMatch] = field(default_factory=list)

    @property
    def all_patterns(self) -> list[PatternMatch]:
        """Return all detected patterns sorted by confidence."""
        all_p = self.filename_patterns + self.folder_patterns + self.special_patterns
        return sorted(all_p, key=lambda p: p.confidence, reverse=True)

    @property
    def primary_filename_pattern(self) -> PatternMatch | None:
        """Return the highest confidence filename pattern."""
        if self.filename_patterns:
            return max(self.filename_patterns, key=lambda p: p.confidence)
        return None

    @property
    def primary_folder_pattern(self) -> PatternMatch | None:
        """Return the highest confidence folder pattern."""
        if self.folder_patterns:
            return max(self.folder_patterns, key=lambda p: p.confidence)
        return None


class PatternDetector:
    """
    Detects naming patterns and conventions in music libraries.

    The detector analyzes filenames, folder structures, and metadata
    to infer how the library is organized. It provides confidence
    scores and human-readable explanations for each detected pattern.
    """

    # Common filename patterns (regex)
    FILENAME_PATTERNS = {
        PatternType.TRACK_ARTIST_TITLE: [
            r"^(\d{1,3})\s*[-._]\s*(.+?)\s*[-_]\s*(.+?)$",  # 01 - Artist - Title
            r"^(\d{1,3})\.\s*(.+?)\s*[-_]\s*(.+?)$",  # 01. Artist - Title
        ],
        PatternType.TRACK_TITLE: [
            r"^(\d{1,3})\s*[-._]\s*(.+?)$",  # 01 - Title
            r"^(\d{1,3})\.\s*(.+?)$",  # 01. Title
        ],
        PatternType.ARTIST_ALBUM_TITLE: [
            r"^(.+?)\s*[-_]\s*(.+?)\s*[-_]\s*(.+?)$",  # Artist - Album - Title
        ],
        PatternType.ARTIST_TITLE: [
            r"^(.+?)\s*[-_]\s*(.+?)$",  # Artist - Title
        ],
        PatternType.TITLE_ONLY: [
            r"^(.+?)$",  # Just the title
        ],
    }

    # Folder name patterns (regex)
    FOLDER_YEAR_PATTERN = re.compile(r"[\(\[]\s*(\d{4})\s*[\)\]]")
    DISC_PATTERN = re.compile(r"(?:disc|cd|disk)\s*(\d+)", re.IGNORECASE)

    def __init__(self):
        self._compiled_patterns: dict[PatternType, list[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        for pattern_type, regexes in self.FILENAME_PATTERNS.items():
            self._compiled_patterns[pattern_type] = [
                re.compile(r, re.IGNORECASE) for r in regexes
            ]

    def analyze(self, library: Library) -> PatternAnalysis:
        """
        Analyze a library and detect all patterns.

        Args:
            library: The Library to analyze.

        Returns:
            PatternAnalysis with all detected patterns and confidence scores.
        """
        analysis = PatternAnalysis(library=library)

        if not library.tracks:
            return analysis

        # Analyze filename patterns
        analysis.filename_patterns = self._detect_filename_patterns(library)

        # Analyze folder structure patterns
        analysis.folder_patterns = self._detect_folder_patterns(library)

        # Detect special patterns
        analysis.special_patterns = self._detect_special_patterns(library)

        # Populate inferred data on tracks based on detected patterns
        self._apply_inferences(library, analysis)

        return analysis

    def _detect_filename_patterns(self, library: Library) -> list[PatternMatch]:
        """Detect patterns in filenames."""
        matches: list[PatternMatch] = []
        total = len(library.tracks)

        # Test each pattern type
        pattern_counts: dict[PatternType, list[Track]] = {
            pt: [] for pt in self.FILENAME_PATTERNS
        }

        for track in library.tracks:
            # Remove extension for pattern matching
            stem = track.path.stem

            # Try patterns in order of specificity (most specific first)
            for pattern_type in [
                PatternType.TRACK_ARTIST_TITLE,
                PatternType.TRACK_TITLE,
                PatternType.ARTIST_ALBUM_TITLE,
                PatternType.ARTIST_TITLE,
                PatternType.TITLE_ONLY,
            ]:
                if self._matches_filename_pattern(stem, pattern_type):
                    pattern_counts[pattern_type].append(track)
                    break  # Only count first match

        # Create PatternMatch objects for significant patterns
        for pattern_type, matching_tracks in pattern_counts.items():
            if not matching_tracks:
                continue

            count = len(matching_tracks)
            confidence = count / total

            # Only report patterns with meaningful matches
            if confidence >= 0.1 or count >= 5:
                matches.append(
                    PatternMatch(
                        pattern_type=pattern_type,
                        confidence=confidence,
                        matching_tracks=count,
                        total_tracks=total,
                        description=self._get_pattern_description(pattern_type),
                        explanation=self._generate_filename_explanation(
                            pattern_type, count, total
                        ),
                        examples=[t.filename for t in matching_tracks[:3]],
                    )
                )

        return sorted(matches, key=lambda m: m.confidence, reverse=True)

    def _detect_folder_patterns(self, library: Library) -> list[PatternMatch]:
        """Detect patterns in folder structure."""
        matches: list[PatternMatch] = []
        folders = library.get_folders()
        total_folders = len(folders)
        total_tracks = len(library.tracks)

        if total_folders == 0:
            return matches

        # Check for flat structure (all in one folder)
        if total_folders == 1:
            matches.append(
                PatternMatch(
                    pattern_type=PatternType.FOLDER_FLAT,
                    confidence=1.0,
                    matching_tracks=total_tracks,
                    total_tracks=total_tracks,
                    description="Flat folder structure",
                    explanation=f"All {total_tracks} tracks are in a single folder.",
                    examples=[str(list(folders.keys())[0])],
                )
            )
            return matches

        # Analyze folder depths relative to root
        depths: dict[int, list[Path]] = {}
        for folder in folders:
            try:
                rel_path = folder.relative_to(library.root_path)
                depth = len(rel_path.parts)
                if depth not in depths:
                    depths[depth] = []
                depths[depth].append(folder)
            except ValueError:
                continue

        # Check for Artist/Album structure (depth 2)
        if 2 in depths:
            depth2_folders = depths[2]
            depth2_tracks = sum(len(folders[f]) for f in depth2_folders)
            confidence = depth2_tracks / total_tracks

            if confidence >= 0.5:
                # Check if parent folders are consistent (likely artists)
                artists = {f.parent.name for f in depth2_folders}

                matches.append(
                    PatternMatch(
                        pattern_type=PatternType.FOLDER_ARTIST_ALBUM,
                        confidence=confidence,
                        matching_tracks=depth2_tracks,
                        total_tracks=total_tracks,
                        description="Artist / Album folder structure",
                        explanation=(
                            f"Detected {len(artists)} artist folders containing "
                            f"{len(depth2_folders)} album folders with {depth2_tracks} tracks."
                        ),
                        examples=[
                            str(f.relative_to(library.root_path))
                            for f in list(depth2_folders)[:3]
                        ],
                    )
                )

        # Check for deeper structure with disc folders (depth 3)
        if 3 in depths:
            depth3_folders = depths[3]
            disc_folders = [
                f for f in depth3_folders if self.DISC_PATTERN.search(f.name)
            ]

            if disc_folders:
                disc_tracks = sum(len(folders[f]) for f in disc_folders)
                confidence = disc_tracks / total_tracks

                if confidence >= 0.1:
                    matches.append(
                        PatternMatch(
                            pattern_type=PatternType.FOLDER_ARTIST_ALBUM_DISC,
                            confidence=confidence,
                            matching_tracks=disc_tracks,
                            total_tracks=total_tracks,
                            description="Artist / Album / Disc folder structure",
                            explanation=(
                                f"Found {len(disc_folders)} disc folders containing "
                                f"{disc_tracks} tracks."
                            ),
                            examples=[
                                str(f.relative_to(library.root_path))
                                for f in list(disc_folders)[:3]
                            ],
                        )
                    )

        # Check for Album-only structure (depth 1, multiple folders)
        if 1 in depths and len(depths.get(1, [])) > 1:
            depth1_folders = depths[1]
            depth1_tracks = sum(len(folders[f]) for f in depth1_folders)
            confidence = depth1_tracks / total_tracks

            if confidence >= 0.5:
                matches.append(
                    PatternMatch(
                        pattern_type=PatternType.FOLDER_ALBUM_ONLY,
                        confidence=confidence,
                        matching_tracks=depth1_tracks,
                        total_tracks=total_tracks,
                        description="Album-only folder structure",
                        explanation=(
                            f"Found {len(depth1_folders)} album folders directly "
                            f"under root with {depth1_tracks} tracks."
                        ),
                        examples=[f.name for f in list(depth1_folders)[:3]],
                    )
                )

        return sorted(matches, key=lambda m: m.confidence, reverse=True)

    def _detect_special_patterns(self, library: Library) -> list[PatternMatch]:
        """Detect special patterns like compilations and year formatting."""
        matches: list[PatternMatch] = []
        folders = library.get_folders()
        total_tracks = len(library.tracks)

        # Check for track number prefixes
        numbered_tracks = [
            t for t in library.tracks if re.match(r"^\d{1,3}\s*[-._]", t.path.stem)
        ]
        if numbered_tracks:
            confidence = len(numbered_tracks) / total_tracks
            if confidence >= 0.25:
                matches.append(
                    PatternMatch(
                        pattern_type=PatternType.NUMBERED_PREFIX,
                        confidence=confidence,
                        matching_tracks=len(numbered_tracks),
                        total_tracks=total_tracks,
                        description="Track number prefix",
                        explanation=(
                            f"{len(numbered_tracks)} of {total_tracks} files "
                            f"({confidence * 100:.0f}%) have track number prefixes."
                        ),
                        examples=[t.filename for t in numbered_tracks[:3]],
                    )
                )

        # Check for year in folder names
        folders_with_year = [
            f for f in folders if self.FOLDER_YEAR_PATTERN.search(f.name)
        ]
        if folders_with_year:
            year_tracks = sum(len(folders[f]) for f in folders_with_year)
            confidence = year_tracks / total_tracks

            if confidence >= 0.1:
                matches.append(
                    PatternMatch(
                        pattern_type=PatternType.YEAR_IN_FOLDER,
                        confidence=confidence,
                        matching_tracks=year_tracks,
                        total_tracks=total_tracks,
                        description="Year in folder name",
                        explanation=(
                            f"{len(folders_with_year)} folders include release year, "
                            f"covering {year_tracks} tracks."
                        ),
                        examples=[f.name for f in folders_with_year[:3]],
                    )
                )

        # Check for compilation/various artists
        va_indicators = ["various artists", "va ", "compilation", "soundtrack", "ost"]
        compilation_folders = []
        for folder in folders:
            folder_lower = folder.name.lower()
            if any(ind in folder_lower for ind in va_indicators):
                compilation_folders.append(folder)

        # Also check by artist diversity within folders
        for folder, tracks in folders.items():
            if len(tracks) >= 5:
                artists = {
                    t.artist or t.inferred_artist
                    for t in tracks
                    if t.artist or t.inferred_artist
                }
                # If folder has many different artists, likely a compilation
                if len(artists) >= len(tracks) * 0.7:
                    if folder not in compilation_folders:
                        compilation_folders.append(folder)

        if compilation_folders:
            comp_tracks = sum(len(folders[f]) for f in compilation_folders)
            confidence = min(comp_tracks / total_tracks, 1.0)

            if confidence >= 0.05:
                matches.append(
                    PatternMatch(
                        pattern_type=PatternType.COMPILATION,
                        confidence=confidence,
                        matching_tracks=comp_tracks,
                        total_tracks=total_tracks,
                        description="Compilation / Various Artists",
                        explanation=(
                            f"Detected {len(compilation_folders)} potential compilation "
                            f"albums with {comp_tracks} tracks."
                        ),
                        examples=[f.name for f in compilation_folders[:3]],
                    )
                )

        return sorted(matches, key=lambda m: m.confidence, reverse=True)

    def _matches_filename_pattern(
        self, filename: str, pattern_type: PatternType
    ) -> bool:
        """Check if a filename matches a pattern type."""
        patterns = self._compiled_patterns.get(pattern_type, [])
        return any(p.match(filename) for p in patterns)

    def _get_pattern_description(self, pattern_type: PatternType) -> str:
        """Get human-readable description for a pattern type."""
        descriptions = {
            PatternType.ARTIST_TITLE: "Artist - Title",
            PatternType.ARTIST_ALBUM_TITLE: "Artist - Album - Title",
            PatternType.TRACK_TITLE: "## - Title (numbered)",
            PatternType.TRACK_ARTIST_TITLE: "## - Artist - Title",
            PatternType.TITLE_ONLY: "Title only",
            PatternType.FOLDER_ARTIST_ALBUM: "Artist / Album structure",
            PatternType.FOLDER_ARTIST_ALBUM_DISC: "Artist / Album / Disc structure",
            PatternType.FOLDER_ALBUM_ONLY: "Album folders only",
            PatternType.FOLDER_FLAT: "Flat (single folder)",
            PatternType.COMPILATION: "Compilation / Various Artists",
            PatternType.NUMBERED_PREFIX: "Track number prefix",
            PatternType.YEAR_IN_FOLDER: "Year in folder name",
        }
        return descriptions.get(pattern_type, str(pattern_type))

    def _generate_filename_explanation(
        self, pattern_type: PatternType, count: int, total: int
    ) -> str:
        """Generate explanation for a filename pattern detection."""
        percent = (count / total) * 100
        return (
            f"{count} of {total} files ({percent:.0f}%) match the "
            f"'{self._get_pattern_description(pattern_type)}' naming pattern."
        )

    def _apply_inferences(self, library: Library, analysis: PatternAnalysis) -> None:
        """Apply inferred data to tracks based on detected patterns."""
        primary_pattern = analysis.primary_filename_pattern

        if not primary_pattern:
            return

        pattern_type = primary_pattern.pattern_type
        patterns = self._compiled_patterns.get(pattern_type, [])

        for track in library.tracks:
            stem = track.path.stem

            for pattern in patterns:
                match = pattern.match(stem)
                if match:
                    groups = match.groups()

                    if (
                        pattern_type == PatternType.TRACK_ARTIST_TITLE
                        and len(groups) >= 3
                    ):
                        track.inferred_track_number = self._safe_int(groups[0])
                        track.inferred_artist = groups[1].strip()
                        track.inferred_title = groups[2].strip()

                    elif pattern_type == PatternType.TRACK_TITLE and len(groups) >= 2:
                        track.inferred_track_number = self._safe_int(groups[0])
                        track.inferred_title = groups[1].strip()
                        # Try to infer artist from folder
                        self._infer_from_folder(track, library)

                    elif (
                        pattern_type == PatternType.ARTIST_ALBUM_TITLE
                        and len(groups) >= 3
                    ):
                        track.inferred_artist = groups[0].strip()
                        track.inferred_album = groups[1].strip()
                        track.inferred_title = groups[2].strip()

                    elif pattern_type == PatternType.ARTIST_TITLE and len(groups) >= 2:
                        track.inferred_artist = groups[0].strip()
                        track.inferred_title = groups[1].strip()

                    elif pattern_type == PatternType.TITLE_ONLY and len(groups) >= 1:
                        track.inferred_title = groups[0].strip()
                        # Try to infer artist/album from folder
                        self._infer_from_folder(track, library)

                    break

    def _infer_from_folder(self, track: Track, library: Library) -> None:
        """Try to infer artist/album from folder structure."""
        try:
            rel_path = track.path.parent.relative_to(library.root_path)
            parts = rel_path.parts

            if len(parts) >= 2:
                # Assume Artist/Album structure
                track.inferred_artist = track.inferred_artist or parts[0]
                track.inferred_album = track.inferred_album or parts[1]
            elif len(parts) == 1:
                # Could be album name
                track.inferred_album = track.inferred_album or parts[0]

        except ValueError:
            pass

    def _safe_int(self, value: str) -> int | None:
        """Safely convert string to int."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
