"""
Tests for TuneSleuth pattern detection.
"""

from pathlib import Path

import pytest

from tunesleuth_core.models import Library, Track
from tunesleuth_core.patterns import PatternDetector, PatternMatch, PatternType


class TestPatternMatch:
    """Tests for PatternMatch model."""

    def test_confidence_percent(self):
        """Test confidence percentage calculation."""
        match = PatternMatch(
            pattern_type=PatternType.ARTIST_TITLE,
            confidence=0.85,
            matching_tracks=85,
            total_tracks=100,
            description="Artist - Title",
            explanation="Test",
        )
        assert match.confidence_percent == 85.0

    def test_confidence_labels(self):
        """Test confidence label assignment."""
        very_high = PatternMatch(
            pattern_type=PatternType.ARTIST_TITLE,
            confidence=0.95,
            matching_tracks=95, total_tracks=100,
            description="", explanation=""
        )
        assert very_high.confidence_label == "Very High"

        high = PatternMatch(
            pattern_type=PatternType.ARTIST_TITLE,
            confidence=0.80,
            matching_tracks=80, total_tracks=100,
            description="", explanation=""
        )
        assert high.confidence_label == "High"

        medium = PatternMatch(
            pattern_type=PatternType.ARTIST_TITLE,
            confidence=0.60,
            matching_tracks=60, total_tracks=100,
            description="", explanation=""
        )
        assert medium.confidence_label == "Medium"

        low = PatternMatch(
            pattern_type=PatternType.ARTIST_TITLE,
            confidence=0.30,
            matching_tracks=30, total_tracks=100,
            description="", explanation=""
        )
        assert low.confidence_label == "Low"

        very_low = PatternMatch(
            pattern_type=PatternType.ARTIST_TITLE,
            confidence=0.10,
            matching_tracks=10, total_tracks=100,
            description="", explanation=""
        )
        assert very_low.confidence_label == "Very Low"


class TestPatternDetector:
    """Tests for PatternDetector."""

    @pytest.fixture
    def detector(self):
        """Create a pattern detector instance."""
        return PatternDetector()

    @pytest.fixture
    def artist_title_library(self):
        """Create a library with Artist - Title naming pattern."""
        library = Library(root_path=Path("/music"))
        tracks = [
            "Pink Floyd - Comfortably Numb.mp3",
            "Led Zeppelin - Stairway to Heaven.mp3",
            "Queen - Bohemian Rhapsody.mp3",
            "The Beatles - Hey Jude.mp3",
            "David Bowie - Space Oddity.mp3",
        ]
        for filename in tracks:
            library.add_track(Track(
                path=Path(f"/music/{filename}"),
                filename=filename,
            ))
        return library

    @pytest.fixture
    def numbered_library(self):
        """Create a library with numbered track pattern."""
        library = Library(root_path=Path("/music/Album"))
        tracks = [
            "01 - Opening.mp3",
            "02 - Main Theme.mp3",
            "03 - Battle.mp3",
            "04 - Victory.mp3",
            "05 - Credits.mp3",
        ]
        for filename in tracks:
            library.add_track(Track(
                path=Path(f"/music/Album/{filename}"),
                filename=filename,
            ))
        return library

    @pytest.fixture
    def artist_album_structure_library(self):
        """Create a library with Artist/Album folder structure."""
        library = Library(root_path=Path("/music"))
        structure = [
            ("Pink Floyd", "The Wall", ["01 - Track.mp3", "02 - Track.mp3"]),
            ("Pink Floyd", "Animals", ["01 - Track.mp3"]),
            ("Queen", "A Night at the Opera", ["01 - Track.mp3", "02 - Track.mp3"]),
        ]
        for artist, album, tracks in structure:
            for track in tracks:
                library.add_track(Track(
                    path=Path(f"/music/{artist}/{album}/{track}"),
                    filename=track,
                ))
        return library

    def test_detect_artist_title_pattern(self, detector, artist_title_library):
        """Test detection of Artist - Title filename pattern."""
        analysis = detector.analyze(artist_title_library)

        assert len(analysis.filename_patterns) > 0
        primary = analysis.primary_filename_pattern
        assert primary is not None
        assert primary.pattern_type == PatternType.ARTIST_TITLE
        assert primary.confidence > 0.9

    def test_detect_numbered_pattern(self, detector, numbered_library):
        """Test detection of numbered track pattern."""
        analysis = detector.analyze(numbered_library)

        assert len(analysis.filename_patterns) > 0
        primary = analysis.primary_filename_pattern
        assert primary is not None
        assert primary.pattern_type == PatternType.TRACK_TITLE
        assert primary.confidence > 0.9

    def test_detect_folder_structure(self, detector, artist_album_structure_library):
        """Test detection of Artist/Album folder structure."""
        analysis = detector.analyze(artist_album_structure_library)

        assert len(analysis.folder_patterns) > 0
        primary = analysis.primary_folder_pattern
        assert primary is not None
        assert primary.pattern_type == PatternType.FOLDER_ARTIST_ALBUM

    def test_special_pattern_numbered_prefix(self, detector, numbered_library):
        """Test detection of numbered prefix special pattern."""
        analysis = detector.analyze(numbered_library)

        numbered_patterns = [
            p for p in analysis.special_patterns
            if p.pattern_type == PatternType.NUMBERED_PREFIX
        ]
        assert len(numbered_patterns) > 0
        assert numbered_patterns[0].confidence > 0.9

    def test_empty_library(self, detector):
        """Test analysis of empty library."""
        library = Library(root_path=Path("/music"))
        analysis = detector.analyze(library)

        assert len(analysis.filename_patterns) == 0
        assert len(analysis.folder_patterns) == 0
        assert analysis.primary_filename_pattern is None
        assert analysis.primary_folder_pattern is None

    def test_inferred_data_applied(self, detector, artist_title_library):
        """Test that inferred data is applied to tracks."""
        detector.analyze(artist_title_library)

        # After analysis, tracks should have inferred data
        for track in artist_title_library.tracks:
            assert track.inferred_artist is not None
            assert track.inferred_title is not None

    def test_flat_folder_detection(self, detector):
        """Test detection of flat folder structure."""
        library = Library(root_path=Path("/music"))
        for i in range(10):
            library.add_track(Track(
                path=Path(f"/music/song{i}.mp3"),
                filename=f"song{i}.mp3",
            ))

        analysis = detector.analyze(library)

        flat_patterns = [
            p for p in analysis.folder_patterns
            if p.pattern_type == PatternType.FOLDER_FLAT
        ]
        assert len(flat_patterns) > 0
        assert flat_patterns[0].confidence == 1.0

    def test_year_in_folder_detection(self, detector):
        """Test detection of year in folder names."""
        library = Library(root_path=Path("/music"))
        folders = [
            "Artist/Album (2020)",
            "Artist/Album (2021)",
            "Artist/Another Album [2019]",
        ]
        for folder in folders:
            library.add_track(Track(
                path=Path(f"/music/{folder}/01 - Track.mp3"),
                filename="01 - Track.mp3",
            ))

        analysis = detector.analyze(library)

        year_patterns = [
            p for p in analysis.special_patterns
            if p.pattern_type == PatternType.YEAR_IN_FOLDER
        ]
        assert len(year_patterns) > 0


class TestPatternAnalysis:
    """Tests for PatternAnalysis results."""

    def test_all_patterns_sorted(self):
        """Test that all_patterns returns sorted by confidence."""
        detector = PatternDetector()
        library = Library(root_path=Path("/music"))

        # Add tracks with mixed patterns
        for i in range(5):
            library.add_track(Track(
                path=Path(f"/music/Artist - Song{i}.mp3"),
                filename=f"Artist - Song{i}.mp3",
            ))
        for i in range(3):
            library.add_track(Track(
                path=Path(f"/music/0{i} - Track.mp3"),
                filename=f"0{i} - Track.mp3",
            ))

        analysis = detector.analyze(library)
        all_patterns = analysis.all_patterns

        # Verify sorted by confidence (descending)
        for i in range(len(all_patterns) - 1):
            assert all_patterns[i].confidence >= all_patterns[i + 1].confidence
