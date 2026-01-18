"""
Tests for TuneSleuth data models.
"""

from datetime import datetime
from pathlib import Path

import pytest

from tunesleuth_core.models import Track, Album, Artist, Library, LibraryStats


class TestTrack:
    """Tests for Track model."""

    def test_track_creation(self):
        """Test basic track creation."""
        track = Track(
            path=Path("/music/artist/album/01 - Song.mp3"),
            filename="01 - Song.mp3",
        )
        assert track.filename == "01 - Song.mp3"
        assert track.path == Path("/music/artist/album/01 - Song.mp3")

    def test_display_title_with_tag(self):
        """Test display_title returns tag when available."""
        track = Track(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
            title="Actual Song Title",
        )
        assert track.display_title == "Actual Song Title"

    def test_display_title_with_inferred(self):
        """Test display_title returns inferred when tag missing."""
        track = Track(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
            inferred_title="Inferred Title",
        )
        assert track.display_title == "Inferred Title"

    def test_display_title_fallback(self):
        """Test display_title falls back to filename."""
        track = Track(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
        )
        assert track.display_title == "song.mp3"

    def test_has_complete_tags(self):
        """Test has_complete_tags property."""
        complete_track = Track(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
            title="Song",
            artist="Artist",
            album="Album",
        )
        assert complete_track.has_complete_tags is True

        incomplete_track = Track(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
            title="Song",
        )
        assert incomplete_track.has_complete_tags is False

    def test_tag_completeness_score(self):
        """Test tag completeness scoring."""
        # All tags filled (6 fields: title, artist, album, track_number, year, genre)
        full_track = Track(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
            title="Song",
            artist="Artist",
            album="Album",
            track_number=1,
            year=2020,
            genre="Rock",
        )
        assert full_track.tag_completeness_score == 1.0

        # No tags
        empty_track = Track(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
        )
        assert empty_track.tag_completeness_score == 0.0

        # Half filled
        half_track = Track(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
            title="Song",
            artist="Artist",
            album="Album",
        )
        assert half_track.tag_completeness_score == 0.5


class TestAlbum:
    """Tests for Album model."""

    def test_album_creation(self):
        """Test basic album creation."""
        album = Album(name="Test Album", artist="Test Artist")
        assert album.name == "Test Album"
        assert album.artist == "Test Artist"
        assert album.track_count == 0

    def test_album_with_tracks(self):
        """Test album with tracks."""
        album = Album(name="Test Album")
        album.tracks = [
            Track(path=Path("/music/01.mp3"), filename="01.mp3", track_number=1),
            Track(path=Path("/music/02.mp3"), filename="02.mp3", track_number=2),
        ]
        assert album.track_count == 2

    def test_is_complete(self):
        """Test album completeness detection."""
        # Complete album (tracks 1, 2, 3)
        complete_album = Album(name="Complete")
        complete_album.tracks = [
            Track(path=Path(f"/music/0{i}.mp3"), filename=f"0{i}.mp3", track_number=i)
            for i in [1, 2, 3]
        ]
        assert complete_album.is_complete is True

        # Incomplete album (missing track 2)
        incomplete_album = Album(name="Incomplete")
        incomplete_album.tracks = [
            Track(path=Path("/music/01.mp3"), filename="01.mp3", track_number=1),
            Track(path=Path("/music/03.mp3"), filename="03.mp3", track_number=3),
        ]
        assert incomplete_album.is_complete is False


class TestLibrary:
    """Tests for Library model."""

    def test_library_creation(self):
        """Test basic library creation."""
        library = Library(root_path=Path("/music"))
        assert library.root_path == Path("/music")
        assert len(library) == 0

    def test_add_track(self):
        """Test adding tracks to library."""
        library = Library(root_path=Path("/music"))
        track = Track(path=Path("/music/song.mp3"), filename="song.mp3")
        library.add_track(track)
        assert len(library) == 1

    def test_get_artists(self):
        """Test artist grouping."""
        library = Library(root_path=Path("/music"))
        library.add_track(Track(
            path=Path("/music/song1.mp3"),
            filename="song1.mp3",
            artist="Artist A",
        ))
        library.add_track(Track(
            path=Path("/music/song2.mp3"),
            filename="song2.mp3",
            artist="Artist A",
        ))
        library.add_track(Track(
            path=Path("/music/song3.mp3"),
            filename="song3.mp3",
            artist="Artist B",
        ))

        artists = library.get_artists()
        assert len(artists) == 2
        assert "Artist A" in artists
        assert "Artist B" in artists
        assert artists["Artist A"].track_count == 2

    def test_get_folders(self):
        """Test folder grouping."""
        library = Library(root_path=Path("/music"))
        library.add_track(Track(
            path=Path("/music/album1/song1.mp3"),
            filename="song1.mp3",
        ))
        library.add_track(Track(
            path=Path("/music/album1/song2.mp3"),
            filename="song2.mp3",
        ))
        library.add_track(Track(
            path=Path("/music/album2/song3.mp3"),
            filename="song3.mp3",
        ))

        folders = library.get_folders()
        assert len(folders) == 2
        assert len(folders[Path("/music/album1")]) == 2
        assert len(folders[Path("/music/album2")]) == 1

    def test_calculate_stats(self):
        """Test statistics calculation."""
        library = Library(root_path=Path("/music"))
        library.add_track(Track(
            path=Path("/music/song1.mp3"),
            filename="song1.mp3",
            file_size=1024 * 1024,  # 1 MB
            duration_seconds=180,
            title="Song 1",
            artist="Artist",
            album="Album",
        ))
        library.add_track(Track(
            path=Path("/music/song2.mp3"),
            filename="song2.mp3",
            file_size=2 * 1024 * 1024,  # 2 MB
            duration_seconds=240,
        ))

        stats = library.calculate_stats()
        assert stats.total_tracks == 2
        assert stats.total_size_mb == 3.0
        assert stats.total_duration_seconds == 420
        assert stats.tracks_with_tags == 1
        assert stats.tracks_without_tags == 1


class TestLibraryStats:
    """Tests for LibraryStats model."""

    def test_size_conversions(self):
        """Test size unit conversions."""
        stats = LibraryStats(total_size_bytes=1024 * 1024 * 1024)  # 1 GB
        assert stats.total_size_mb == 1024.0
        assert stats.total_size_gb == 1.0

    def test_duration_conversion(self):
        """Test duration conversion to hours."""
        stats = LibraryStats(total_duration_seconds=7200)  # 2 hours
        assert stats.total_duration_hours == 2.0

    def test_tag_coverage_percent(self):
        """Test tag coverage percentage calculation."""
        stats = LibraryStats(total_tracks=100, tracks_with_tags=75)
        assert stats.tag_coverage_percent == 75.0

        empty_stats = LibraryStats(total_tracks=0)
        assert empty_stats.tag_coverage_percent == 0.0
