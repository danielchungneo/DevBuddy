"""Spotify / YouTube playlist URL detection and normalization."""

MUSIC_SPOTIFY_ACCENT = "#1ed760"
MUSIC_YOUTUBE_ACCENT = "#ff0000"


def playlist_source_from_url(url):
    """Return 'spotify' | 'youtube' | None based on URL."""
    if not url or not isinstance(url, str):
        return None
    u = url.strip().lower()
    if u.startswith("spotify:") or "open.spotify.com" in u or "spotify.com" in u:
        return "spotify"
    if "youtube.com" in u or "youtu.be" in u or "music.youtube.com" in u:
        return "youtube"
    return None


def normalize_playlist_url(url):
    u = (url or "").strip()
    if not u:
        return ""
    if not u.startswith(("http://", "https://", "spotify:")):
        u = "https://" + u
    return u
