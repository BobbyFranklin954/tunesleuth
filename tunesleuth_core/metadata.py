"""
TuneSleuth Metadata Provider

Connects to online metadata sources (MusicBrainz, etc.) to enrich track information.
Implements rate limiting and fuzzy matching for reliable lookups.
"""

import time
from dataclasses import dataclass
from difflib import SequenceMatcher

import musicbrainzngs

from tunesleuth_core.models import Track


@dataclass
class MetadataMatch:
    """Represents a potential metadata match from an online source."""

    # Matched metadata
    title: str
    artist: str
    album: str
    track_number: int | None = None
    year: int | None = None
    genre: str | None = None

    # Match quality
    confidence: float = 0.0  # 0.0 to 1.0
    source: str = "musicbrainz"

    # MusicBrainz IDs for future use
    recording_id: str | None = None
    release_id: str | None = None
    artist_id: str | None = None

    def __str__(self) -> str:
        return f"{self.artist} - {self.title} ({self.confidence:.0%} match)"


class RateLimiter:
    """Simple rate limiter to respect API limits."""

    def __init__(self, calls_per_second: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            calls_per_second: Maximum number of calls per second (default: 1.0)
        """
        self.min_interval = 1.0 / calls_per_second
        self.last_call: float | None = None

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        if self.last_call is not None:
            elapsed = time.time() - self.last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


class MusicBrainzClient:
    """
    Client for MusicBrainz metadata lookups with rate limiting and fuzzy matching.

    MusicBrainz API limits:
    - 1 request per second for anonymous users
    - Must provide User-Agent identifying your application
    """

    def __init__(
        self,
        app_name: str = "TuneSleuth",
        app_version: str = "0.1.0",
        contact: str = "",
        rate_limit: float = 1.0,
    ):
        """
        Initialize MusicBrainz client.

        Args:
            app_name: Application name for User-Agent
            app_version: Application version
            contact: Contact email (optional but recommended)
            rate_limit: Requests per second (default: 1.0)
        """
        # Set User-Agent (required by MusicBrainz)
        musicbrainzngs.set_useragent(app_name, app_version, contact)

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(calls_per_second=rate_limit)

    def search_track(
        self,
        title: str,
        artist: str | None = None,
        album: str | None = None,
        limit: int = 5,
    ) -> list[MetadataMatch]:
        """
        Search for track metadata using fuzzy matching.

        Args:
            title: Track title
            artist: Artist name (optional but improves accuracy)
            album: Album name (optional but improves accuracy)
            limit: Maximum number of results to return

        Returns:
            List of MetadataMatch objects sorted by confidence (highest first)
        """
        # Respect rate limit
        self.rate_limiter.wait()

        # Build search query WITHOUT quotes for fuzzy matching
        # This allows MusicBrainz to match "Blue Rondo ALa Turk" to "Blue Rondo a la Turk"
        # and "Fly Me To The Moon" to "Fly Me to the Moon"
        query_parts = [f'recording:{title}']
        if artist:
            query_parts.append(f'artist:{artist}')
        if album:
            query_parts.append(f'release:{album}')

        query = " AND ".join(query_parts)

        try:
            # Search MusicBrainz
            result = musicbrainzngs.search_recordings(
                query=query,
                limit=limit,
            )

            # Parse results
            matches = []
            for recording in result.get("recording-list", []):
                match = self._parse_recording(recording, title, artist, album)
                if match:
                    matches.append(match)

            # Sort by confidence
            matches.sort(key=lambda m: m.confidence, reverse=True)
            return matches

        except musicbrainzngs.WebServiceError as e:
            # Handle API errors gracefully
            print(f"MusicBrainz API error: {e}")
            return []

    def lookup_track(self, track: Track, limit: int = 5) -> list[MetadataMatch]:
        """
        Look up metadata for a Track object.

        Prefers inferred data (from filename patterns) over existing ID3 tags when:
        1. ID3 tags look suspicious (contain filename patterns, camel case, etc.)
        2. Inferred data is available and differs from ID3 tags

        This handles cases where files have incorrect or auto-generated ID3 tags.

        Args:
            track: Track to look up
            limit: Maximum number of results

        Returns:
            List of MetadataMatch objects sorted by confidence
        """
        # Strategy: Prefer inferred data when available, as it's derived from
        # filename patterns that are often more reliable than stale/incorrect ID3 tags

        # For title: prefer inferred if it exists, otherwise use ID3
        if track.inferred_title:
            title = track.inferred_title
        elif track.title and ("(" in track.title or ")-" in track.title):
            # ID3 title looks like a filename, use it but suspicious
            title = track.title
        else:
            title = track.title or track.path.stem

        # For artist: prefer inferred if it exists and differs from ID3
        # This handles cases where ID3 has wrong artist (e.g., "Sergio Mendez" vs "Quincy Jones")
        if track.inferred_artist:
            artist = track.inferred_artist
        elif track.artist and " " not in track.artist and any(c.isupper() for c in track.artist[1:]):
            # ID3 artist is camel case - suspicious
            artist = track.inferred_artist or track.artist
        else:
            artist = track.artist

        album = track.album or track.inferred_album

        return self.search_track(title=title, artist=artist, album=album, limit=limit)

    def _parse_recording(
        self,
        recording: dict,
        search_title: str,
        search_artist: str | None,
        search_album: str | None,
    ) -> MetadataMatch | None:
        """Parse a MusicBrainz recording result into a MetadataMatch."""
        try:
            # Extract basic info
            title = recording.get("title", "")
            recording_id = recording.get("id", "")

            # Extract artist (first artist if multiple)
            artist = ""
            artist_id = None
            if "artist-credit" in recording:
                artist_credit = recording["artist-credit"]
                if isinstance(artist_credit, list) and artist_credit:
                    first_artist = artist_credit[0]
                    if isinstance(first_artist, dict) and "artist" in first_artist:
                        artist = first_artist["artist"].get("name", "")
                        artist_id = first_artist["artist"].get("id")

            # Extract release info (use first release)
            album = ""
            release_id = None
            track_number = None
            year = None

            if "release-list" in recording:
                releases = recording["release-list"]
                if releases:
                    first_release = releases[0]
                    album = first_release.get("title", "")
                    release_id = first_release.get("id")

                    # Extract year from date
                    if "date" in first_release:
                        date_str = first_release["date"]
                        if date_str and len(date_str) >= 4:
                            try:
                                year = int(date_str[:4])
                            except ValueError:
                                pass

                    # Extract track number if available
                    if "medium-list" in first_release:
                        mediums = first_release["medium-list"]
                        if mediums and "track-list" in mediums[0]:
                            tracks = mediums[0]["track-list"]
                            if tracks:
                                track_num_str = tracks[0].get("number", "")
                                if track_num_str:
                                    try:
                                        track_number = int(track_num_str)
                                    except ValueError:
                                        pass

            # Calculate confidence score based on fuzzy matching
            confidence = self._calculate_confidence(
                title, artist, album,
                search_title, search_artist, search_album
            )

            return MetadataMatch(
                title=title,
                artist=artist,
                album=album,
                track_number=track_number,
                year=year,
                confidence=confidence,
                source="musicbrainz",
                recording_id=recording_id,
                release_id=release_id,
                artist_id=artist_id,
            )

        except (KeyError, TypeError, IndexError) as e:
            # Skip malformed results
            print(f"Error parsing recording: {e}")
            return None

    def _calculate_confidence(
        self,
        result_title: str,
        result_artist: str,
        result_album: str,
        search_title: str,
        search_artist: str | None,
        search_album: str | None,
    ) -> float:
        """
        Calculate confidence score for a match using fuzzy string matching.

        Returns:
            Confidence score from 0.0 to 1.0
        """
        scores = []

        # Title match (most important)
        title_score = self._fuzzy_match(result_title, search_title)
        scores.append(title_score * 2.0)  # Weight title heavily

        # Artist match
        if search_artist:
            artist_score = self._fuzzy_match(result_artist, search_artist)
            scores.append(artist_score * 1.5)  # Weight artist moderately

        # Album match
        if search_album:
            album_score = self._fuzzy_match(result_album, search_album)
            scores.append(album_score)  # Standard weight

        # Calculate weighted average
        if not scores:
            return 0.0

        confidence = sum(scores) / sum([2.0, 1.5, 1.0][:len(scores)])
        return min(confidence, 1.0)

    def _fuzzy_match(self, str1: str, str2: str) -> float:
        """
        Calculate fuzzy match score between two strings.

        Returns:
            Score from 0.0 to 1.0
        """
        if not str1 or not str2:
            return 0.0

        # Normalize strings (lowercase, strip whitespace)
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, s1, s2).ratio()
