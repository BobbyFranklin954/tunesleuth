"""
TuneSleuth Scanner Module

Recursively scans directories for MP3 files and extracts metadata.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, Optional

from mutagen import File as MutagenFile
from mutagen.id3 import ID3
from mutagen.mp3 import MP3

from tunesleuth_core.models import Library, Track


@dataclass
class ScanProgress:
    """Tracks the progress of a library scan."""

    total_files_found: int = 0
    files_scanned: int = 0
    files_with_errors: int = 0
    current_file: Optional[str] = None
    errors: list[tuple[str, str]] = field(default_factory=list)

    @property
    def progress_percent(self) -> float:
        if self.total_files_found == 0:
            return 0.0
        return (self.files_scanned / self.total_files_found) * 100

    @property
    def is_complete(self) -> bool:
        return self.files_scanned >= self.total_files_found


class Scanner:
    """
    Scans directories for MP3 files and builds a Library.

    The scanner recursively traverses directories, identifies MP3 files,
    extracts ID3 metadata, and creates Track objects for each file.
    """

    # Supported audio file extensions
    SUPPORTED_EXTENSIONS = {".mp3"}

    def __init__(
        self,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None,
    ):
        """
        Initialize the scanner.

        Args:
            progress_callback: Optional callback function that receives
                              ScanProgress updates during scanning.
        """
        self.progress_callback = progress_callback

    def scan(self, root_path: Path | str) -> Library:
        """
        Scan a directory and return a Library containing all found tracks.

        Args:
            root_path: The root directory to scan.

        Returns:
            A Library object containing all discovered tracks.
        """
        root_path = Path(root_path).resolve()

        if not root_path.exists():
            raise FileNotFoundError(f"Directory not found: {root_path}")

        if not root_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {root_path}")

        library = Library(root_path=root_path, scan_date=datetime.now())
        progress = ScanProgress()

        # First pass: count total files
        mp3_files = list(self._find_mp3_files(root_path))
        progress.total_files_found = len(mp3_files)
        self._notify_progress(progress)

        # Second pass: scan each file
        for file_path in mp3_files:
            progress.current_file = str(file_path)

            try:
                track = self._scan_file(file_path)
                library.add_track(track)
            except Exception as e:
                progress.files_with_errors += 1
                progress.errors.append((str(file_path), str(e)))

            progress.files_scanned += 1
            self._notify_progress(progress)

        return library

    def scan_iter(self, root_path: Path | str) -> Iterator[tuple[Track, ScanProgress]]:
        """
        Scan a directory and yield tracks one at a time.

        This is useful for streaming results to a UI without waiting
        for the entire scan to complete.

        Args:
            root_path: The root directory to scan.

        Yields:
            Tuples of (Track, ScanProgress) for each discovered track.
        """
        root_path = Path(root_path).resolve()

        if not root_path.exists():
            raise FileNotFoundError(f"Directory not found: {root_path}")

        if not root_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {root_path}")

        progress = ScanProgress()

        # First pass: count total files
        mp3_files = list(self._find_mp3_files(root_path))
        progress.total_files_found = len(mp3_files)

        # Second pass: scan each file
        for file_path in mp3_files:
            progress.current_file = str(file_path)

            try:
                track = self._scan_file(file_path)
                progress.files_scanned += 1
                yield track, progress
            except Exception as e:
                progress.files_with_errors += 1
                progress.errors.append((str(file_path), str(e)))
                progress.files_scanned += 1

    def _find_mp3_files(self, root_path: Path) -> Iterator[Path]:
        """
        Recursively find all MP3 files in a directory.

        Args:
            root_path: The root directory to search.

        Yields:
            Path objects for each found MP3 file.
        """
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                file_path = Path(dirpath) / filename
                if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    yield file_path

    def _scan_file(self, file_path: Path) -> Track:
        """
        Scan a single MP3 file and extract metadata.

        Args:
            file_path: Path to the MP3 file.

        Returns:
            A Track object with file and ID3 metadata.
        """
        stat = file_path.stat()

        track = Track(
            path=file_path,
            filename=file_path.name,
            file_size=stat.st_size,
            modified_date=datetime.fromtimestamp(stat.st_mtime),
        )

        # Try to extract ID3 metadata
        try:
            audio = MutagenFile(file_path)

            if audio is None:
                return track

            # Extract duration and bitrate from MP3
            if isinstance(audio, MP3):
                track.duration_seconds = audio.info.length
                track.bitrate = audio.info.bitrate

            # Extract ID3 tags
            if hasattr(audio, "tags") and audio.tags:
                self._extract_id3_tags(track, audio)

        except Exception:
            # If metadata extraction fails, we still return the track
            # with basic file info
            pass

        return track

    def _extract_id3_tags(self, track: Track, audio: MutagenFile) -> None:
        """
        Extract ID3 tags from an audio file and populate the track.

        Args:
            track: The Track object to populate.
            audio: The Mutagen audio file object.
        """
        tags = audio.tags

        if tags is None:
            return

        # Handle both ID3 and other tag formats
        if isinstance(tags, ID3):
            # ID3v2 tags
            track.title = self._get_id3_text(tags, "TIT2")
            track.artist = self._get_id3_text(tags, "TPE1")
            track.album = self._get_id3_text(tags, "TALB")
            track.album_artist = self._get_id3_text(tags, "TPE2")
            track.genre = self._get_id3_text(tags, "TCON")

            # Track number (may be "X/Y" format)
            track_str = self._get_id3_text(tags, "TRCK")
            if track_str:
                track.track_number, track.track_total = self._parse_number_pair(track_str)

            # Disc number (may be "X/Y" format)
            disc_str = self._get_id3_text(tags, "TPOS")
            if disc_str:
                track.disc_number, track.disc_total = self._parse_number_pair(disc_str)

            # Year
            year_str = self._get_id3_text(tags, "TDRC") or self._get_id3_text(tags, "TYER")
            if year_str:
                try:
                    # TDRC can be a timestamp, extract just the year
                    track.year = int(str(year_str)[:4])
                except (ValueError, IndexError):
                    pass
        else:
            # Other tag formats (e.g., ID3v1, Vorbis comments)
            track.title = self._get_tag_value(tags, ["title", "TITLE"])
            track.artist = self._get_tag_value(tags, ["artist", "ARTIST"])
            track.album = self._get_tag_value(tags, ["album", "ALBUM"])
            track.genre = self._get_tag_value(tags, ["genre", "GENRE"])

            # Track number
            track_str = self._get_tag_value(tags, ["tracknumber", "TRACKNUMBER", "track"])
            if track_str:
                track.track_number, track.track_total = self._parse_number_pair(track_str)

            # Year
            year_str = self._get_tag_value(tags, ["date", "DATE", "year", "YEAR"])
            if year_str:
                try:
                    track.year = int(str(year_str)[:4])
                except (ValueError, IndexError):
                    pass

    def _get_id3_text(self, tags: ID3, frame_id: str) -> Optional[str]:
        """Extract text from an ID3 frame."""
        frame = tags.get(frame_id)
        if frame and hasattr(frame, "text") and frame.text:
            return str(frame.text[0])
        return None

    def _get_tag_value(self, tags, keys: list[str]) -> Optional[str]:
        """Get a tag value trying multiple possible keys."""
        for key in keys:
            if key in tags:
                value = tags[key]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None

    def _parse_number_pair(self, value: str) -> tuple[Optional[int], Optional[int]]:
        """
        Parse a number that may be in "X/Y" format.

        Args:
            value: String like "5" or "5/12"

        Returns:
            Tuple of (number, total) where total may be None.
        """
        if "/" in value:
            parts = value.split("/")
            try:
                num = int(parts[0])
                total = int(parts[1]) if len(parts) > 1 else None
                return num, total
            except ValueError:
                return None, None
        else:
            try:
                return int(value), None
            except ValueError:
                return None, None

    def _notify_progress(self, progress: ScanProgress) -> None:
        """Send progress update to callback if registered."""
        if self.progress_callback:
            self.progress_callback(progress)
