"""
Tests for TuneSleuth metadata lookup functionality.
"""

from pathlib import Path
from unittest.mock import patch

from tunesleuth_core.metadata import MetadataMatch, MusicBrainzClient, RateLimiter
from tunesleuth_core.models import Track


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(calls_per_second=2.0)
        assert limiter.min_interval == 0.5

    def test_rate_limiter_wait_first_call(self):
        """Test that first call doesn't wait."""
        limiter = RateLimiter(calls_per_second=1.0)
        limiter.wait()  # Should not raise or block significantly
        assert limiter.last_call is not None


class TestMetadataMatch:
    """Tests for MetadataMatch model."""

    def test_metadata_match_creation(self):
        """Test creating a metadata match."""
        match = MetadataMatch(
            title="Bohemian Rhapsody",
            artist="Queen",
            album="A Night at the Opera",
            year=1975,
            confidence=0.95,
        )
        assert match.title == "Bohemian Rhapsody"
        assert match.artist == "Queen"
        assert match.confidence == 0.95

    def test_metadata_match_str(self):
        """Test string representation."""
        match = MetadataMatch(
            title="Test",
            artist="Artist",
            album="Album",
            confidence=0.85,
        )
        assert "Artist - Test" in str(match)
        assert "85%" in str(match)


class TestMusicBrainzClient:
    """Tests for MusicBrainzClient."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = MusicBrainzClient(
            app_name="TestApp",
            app_version="1.0",
            contact="test@example.com",
        )
        assert client.rate_limiter is not None

    def test_fuzzy_match_exact(self):
        """Test fuzzy matching with exact strings."""
        client = MusicBrainzClient()
        score = client._fuzzy_match("Bohemian Rhapsody", "Bohemian Rhapsody")
        assert score == 1.0

    def test_fuzzy_match_case_insensitive(self):
        """Test fuzzy matching is case insensitive."""
        client = MusicBrainzClient()
        score = client._fuzzy_match("Bohemian Rhapsody", "bohemian rhapsody")
        assert score == 1.0

    def test_fuzzy_match_similar(self):
        """Test fuzzy matching with similar strings."""
        client = MusicBrainzClient()
        score = client._fuzzy_match("Bohemian Rhapsody", "Bohemian Rapsody")
        assert score > 0.9  # Should be high but not perfect

    def test_fuzzy_match_different(self):
        """Test fuzzy matching with different strings."""
        client = MusicBrainzClient()
        score = client._fuzzy_match("Bohemian Rhapsody", "Stairway to Heaven")
        assert score < 0.5  # Should be low

    def test_fuzzy_match_empty(self):
        """Test fuzzy matching with empty strings."""
        client = MusicBrainzClient()
        assert client._fuzzy_match("", "test") == 0.0
        assert client._fuzzy_match("test", "") == 0.0

    def test_calculate_confidence_perfect_match(self):
        """Test confidence calculation for perfect match."""
        client = MusicBrainzClient()
        confidence = client._calculate_confidence(
            result_title="Bohemian Rhapsody",
            result_artist="Queen",
            result_album="A Night at the Opera",
            search_title="Bohemian Rhapsody",
            search_artist="Queen",
            search_album="A Night at the Opera",
        )
        assert confidence >= 0.99  # Should be very close to 1.0

    def test_calculate_confidence_title_only(self):
        """Test confidence calculation with title only."""
        client = MusicBrainzClient()
        confidence = client._calculate_confidence(
            result_title="Bohemian Rhapsody",
            result_artist="Queen",
            result_album="A Night at the Opera",
            search_title="Bohemian Rhapsody",
            search_artist=None,
            search_album=None,
        )
        # With perfect title match but no artist/album, confidence should be high
        assert confidence >= 0.9

    @patch("musicbrainzngs.search_recordings")
    def test_search_track_with_results(self, mock_search):
        """Test searching for a track with mocked results."""
        # Mock MusicBrainz response
        mock_search.return_value = {
            "recording-list": [
                {
                    "id": "test-recording-id",
                    "title": "Bohemian Rhapsody",
                    "artist-credit": [
                        {
                            "artist": {
                                "name": "Queen",
                                "id": "test-artist-id",
                            }
                        }
                    ],
                    "release-list": [
                        {
                            "id": "test-release-id",
                            "title": "A Night at the Opera",
                            "date": "1975-11-21",
                            "medium-list": [
                                {
                                    "track-list": [
                                        {"number": "11"}
                                    ]
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        client = MusicBrainzClient()
        matches = client.search_track(
            title="Bohemian Rhapsody",
            artist="Queen",
            album="A Night at the Opera",
        )

        assert len(matches) == 1
        match = matches[0]
        assert match.title == "Bohemian Rhapsody"
        assert match.artist == "Queen"
        assert match.album == "A Night at the Opera"
        assert match.year == 1975
        assert match.track_number == 11
        assert match.confidence > 0.0

    @patch("musicbrainzngs.search_recordings")
    def test_search_track_no_results(self, mock_search):
        """Test searching for a track with no results."""
        mock_search.return_value = {"recording-list": []}

        client = MusicBrainzClient()
        matches = client.search_track(
            title="Nonexistent Song",
            artist="Nonexistent Artist",
        )

        assert len(matches) == 0

    @patch("musicbrainzngs.search_recordings")
    def test_search_track_api_error(self, mock_search):
        """Test handling of API errors."""
        import musicbrainzngs

        mock_search.side_effect = musicbrainzngs.WebServiceError("API Error")

        client = MusicBrainzClient()
        matches = client.search_track(title="Test")

        # Should return empty list on error
        assert matches == []

    def test_lookup_track(self):
        """Test looking up metadata for a Track object."""
        client = MusicBrainzClient()

        track = Track(
            path=Path("/music/test.mp3"),
            filename="test.mp3",
            title="Bohemian Rhapsody",
            artist="Queen",
            album="A Night at the Opera",
        )

        # Mock the search to avoid actual API call
        with patch.object(client, "search_track") as mock_search:
            mock_search.return_value = []
            client.lookup_track(track)
            mock_search.assert_called_once_with(
                title="Bohemian Rhapsody",
                artist="Queen",
                album="A Night at the Opera",
                limit=5,
            )

    def test_lookup_track_with_inferred_data(self):
        """Test lookup uses inferred data when tags are missing."""
        client = MusicBrainzClient()

        track = Track(
            path=Path("/music/test.mp3"),
            filename="test.mp3",
            inferred_title="Bohemian Rhapsody",
            inferred_artist="Queen",
        )

        with patch.object(client, "search_track") as mock_search:
            mock_search.return_value = []
            client.lookup_track(track)
            mock_search.assert_called_once_with(
                title="Bohemian Rhapsody",
                artist="Queen",
                album=None,
                limit=5,
            )
