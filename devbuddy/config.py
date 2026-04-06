"""config.json load/save and project/music normalization."""

import json
import os

from devbuddy.playlists import playlist_source_from_url
from devbuddy.theme import CARD_PALETTE
from devbuddy.focus_gamify import normalize_focus_stats
from devbuddy.todos import normalize_item, normalize_todo_items

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(_ROOT, "config.json")


def normalize_repo(repo):
    """Ensure repo is always a {name, path} dict (handles legacy string format)."""
    if isinstance(repo, str):
        return {"name": "", "path": repo}
    return repo


def normalize_sln(sln):
    """Ensure sln is always a {name, path} dict (handles legacy string format)."""
    if isinstance(sln, str):
        return {"name": "", "path": sln}
    return sln


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "projects": [],
            "music_playlists": [],
            "todo_items": [],
            "focus_stats": normalize_focus_stats({}),
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    changed = False
    if "projects" not in data or not isinstance(data["projects"], list):
        data["projects"] = []
        changed = True
    if "music_playlists" not in data or not isinstance(data["music_playlists"], list):
        data["music_playlists"] = []
        changed = True

    legacy_todo_lists = data.pop("todo_lists", None)
    if legacy_todo_lists is not None:
        changed = True

    if "todo_items" not in data or not isinstance(data["todo_items"], list):
        data["todo_items"] = []
        changed = True

    if legacy_todo_lists and isinstance(legacy_todo_lists, list) and not data["todo_items"]:
        migrated = []
        for day in legacy_todo_lists:
            if isinstance(day, dict):
                for it in day.get("items", []):
                    migrated.append(normalize_item(it))
        data["todo_items"] = normalize_todo_items(migrated)
        changed = True
    else:
        normalized = normalize_todo_items(data["todo_items"])
        if normalized != data["todo_items"]:
            data["todo_items"] = normalized
            changed = True

    if "focus_stats" not in data or not isinstance(data["focus_stats"], dict):
        data["focus_stats"] = normalize_focus_stats({})
        changed = True
    else:
        fs = normalize_focus_stats(data["focus_stats"])
        if fs != data["focus_stats"]:
            data["focus_stats"] = fs
            changed = True

    for pl in data.get("music_playlists", []):
        if pl.get("source") not in ("spotify", "youtube"):
            s = playlist_source_from_url(pl.get("url", ""))
            if s:
                pl["source"] = s
                changed = True
    for i, project in enumerate(data.get("projects", [])):
        project["repos"] = [normalize_repo(r) for r in project.get("repos", [])]
        if "sln" in project:
            project["sln"] = normalize_sln(project["sln"])
        if project.get("accent") not in CARD_PALETTE:
            project["accent"] = CARD_PALETTE[i % len(CARD_PALETTE)]
            changed = True

    if changed:
        save_config(data)
    return data


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
