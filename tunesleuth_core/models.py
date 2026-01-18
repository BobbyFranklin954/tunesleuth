"""
TuneSleuth Data Models

Core data structures representing tracks, albums, artists, and the music library.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Track:
    """Represents a single music track (MP3 file)."""

    path: Path
    filename: str

    # File metadata
    file_size: int = 0
    modified_date: Optional[datetime] = None

    # ID3 tag data (may be None if tags are missing)
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    track_number: Optional[int] = None
    track_total: Optional[int] = None
    disc_number: Optional[int] = None
    disc_total: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration_seconds: Optional[float] = None
    bitrate: Optional[int] = None

    # Parsed from filename/path (inferred data)
    inferred_artist: Optional[str] = None
    inferred_album: Optional[str] = None
    inferred_title: Optional[str] = None
    inferred_track_number: Optional[int] = None

    @property
    def display_title(self) -> str:
        """Return the best available title for display."""
        return self.title or self.inferred_title or self.filename

    @property
    def display_artist(self) -> str:
        """Return the best available artist for display."""
        return self.artist or self.inferred_artist or "Unknown Artist"

    @property
    def display_album(self) -> str:
        """Return the best available album for display."""
        return self.album or self.inferred_album or "Unknown Album"

    @property
    def has_complete_tags(self) -> bool:
        """Check if track has minimum required ID3 tags."""
        return all([self.title, self.artist, self.album])

    @property
    def tag_completeness_score(self) -> float:
        """Calculate a completeness score for ID3 tags (0.0 to 1.0)."""
        fields = [
            self.title,
            self.artist,
            self.album,
            self.track_number,
            self.year,
            self.genre,
        ]
        filled = sum(1 for f in fields if f is not None)
        return filled / len(fields)

    def __str__(self) -> str:
        return f"{self.display_artist} - {self.display_title}"


@dataclass
class Artist:
    """Represents an artist in the library."""

    name: str
    tracks: list[Track] = field(default_factory=list)
    albums: list["Album"] = field(default_factory=list)

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def album_count(self) -> int:
        return len(self.albums)

    def __str__(self) -> str:
        return self.name


@dataclass
class Album:
    """Represents an album in the library."""

    name: str
    artist: Optional[str] = None
    tracks: list[Track] = field(default_factory=list)
    year: Optional[int] = None
    folder_path: Optional[Path] = None

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def total_duration_seconds(self) -> float:
        """Calculate total album duration."""
        return sum(t.duration_seconds or 0 for t in self.tracks)

    @property
    def is_complete(self) -> bool:
        """Check if album appears to be complete (has track numbers in sequence)."""
        if not self.tracks:
            return False
        track_nums = [t.track_number for t in self.tracks if t.track_number]
        if not track_nums:
            return False
        # Check if we have tracks 1 through max
        max_track = max(track_nums)
        expected = set(range(1, max_track + 1))
        return set(track_nums) == expected

    def __str__(self) -> str:
        if self.artist:
            return f"{self.artist} - {self.name}"
        return self.name


@dataclass
class LibraryStats:
    """Statistics about the music library."""

    total_tracks: int = 0
    total_size_bytes: int = 0
    total_duration_seconds: float = 0.0

    tracks_with_tags: int = 0
    tracks_without_tags: int = 0
    average_tag_completeness: float = 0.0

    unique_artists: int = 0
    unique_albums: int = 0
    unique_genres: int = 0

    # File organization stats
    folder_count: int = 0
    max_folder_depth: int = 0

    @property
    def total_size_mb(self) -> float:
        return self.total_size_bytes / (1024 * 1024)

    @property
    def total_size_gb(self) -> float:
        return self.total_size_bytes / (1024 * 1024 * 1024)

    @property
    def total_duration_hours(self) -> float:
        return self.total_duration_seconds / 3600

    @property
    def tag_coverage_percent(self) -> float:
        if self.total_tracks == 0:
            return 0.0
        return (self.tracks_with_tags / self.total_tracks) * 100


@dataclass
class Library:
    """
    Represents the entire music library.

    This is the central data structure that holds all scanned tracks
    and provides methods for querying and analyzing the collection.
    """

    root_path: Path
    tracks: list[Track] = field(default_factory=list)
    scan_date: Optional[datetime] = None

    # Cached groupings (populated on demand)
    _artists: Optional[dict[str, Artist]] = field(default=None, repr=False)
    _albums: Optional[dict[str, Album]] = field(default=None, repr=False)

    def add_track(self, track: Track) -> None:
        """Add a track to the library."""
        self.tracks.append(track)
        # Invalidate caches
        self._artists = None
        self._albums = None

    def get_artists(self) -> dict[str, Artist]:
        """Get all artists in the library, grouped by name."""
        if self._artists is None:
            self._artists = {}
            for track in self.tracks:
                artist_name = track.display_artist
                if artist_name not in self._artists:
                    self._artists[artist_name] = Artist(name=artist_name)
                self._artists[artist_name].tracks.append(track)
        return self._artists

    def get_albums(self) -> dict[str, Album]:
        """Get all albums in the library, grouped by name."""
        if self._albums is None:
            self._albums = {}
            for track in self.tracks:
                # Use combination of artist + album as key to handle same album names
                album_name = track.display_album
                artist_name = track.display_artist
                key = f"{artist_name}|{album_name}"

                if key not in self._albums:
                    self._albums[key] = Album(
                        name=album_name,
                        artist=artist_name,
                        folder_path=track.path.parent,
                    )
                self._albums[key].tracks.append(track)

                # Update year if available
                if track.year and not self._albums[key].year:
                    self._albums[key].year = track.year
        return self._albums

    def get_folders(self) -> dict[Path, list[Track]]:
        """Get tracks grouped by their containing folder."""
        folders: dict[Path, list[Track]] = {}
        for track in self.tracks:
            folder = track.path.parent
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(track)
        return folders

    def calculate_stats(self) -> LibraryStats:
        """Calculate comprehensive library statistics."""
        stats = LibraryStats()

        if not self.tracks:
            return stats

        stats.total_tracks = len(self.tracks)
        stats.total_size_bytes = sum(t.file_size for t in self.tracks)
        stats.total_duration_seconds = sum(t.duration_seconds or 0 for t in self.tracks)

        # Tag statistics
        completeness_scores = [t.tag_completeness_score for t in self.tracks]
        stats.average_tag_completeness = sum(completeness_scores) / len(
            completeness_scores
        )
        stats.tracks_with_tags = sum(1 for t in self.tracks if t.has_complete_tags)
        stats.tracks_without_tags = stats.total_tracks - stats.tracks_with_tags

        # Unique counts
        artists = set(t.display_artist for t in self.tracks)
        albums = set(f"{t.display_artist}|{t.display_album}" for t in self.tracks)
        genres = set(t.genre for t in self.tracks if t.genre)

        stats.unique_artists = len(artists)
        stats.unique_albums = len(albums)
        stats.unique_genres = len(genres)

        # Folder statistics
        folders = self.get_folders()
        stats.folder_count = len(folders)

        if folders:
            depths = []
            for folder in folders:
                try:
                    rel_path = folder.relative_to(self.root_path)
                    depths.append(len(rel_path.parts))
                except ValueError:
                    depths.append(0)
            stats.max_folder_depth = max(depths) if depths else 0

        return stats

    def __len__(self) -> int:
        return len(self.tracks)

    def __str__(self) -> str:
        return f"Library({self.root_path}, {len(self.tracks)} tracks)"
