"""XP, streaks, and reward copy for completed focus sessions."""

from __future__ import annotations

from datetime import date, timedelta


def clamp_minutes(raw) -> int:
    try:
        m = int(float(str(raw).strip()))
    except (TypeError, ValueError):
        return 0
    return max(0, min(240, m))


def clamp_seconds(raw) -> int:
    try:
        s = int(float(str(raw).strip()))
    except (TypeError, ValueError):
        return 0
    return max(0, min(59, s))


def level_from_total_xp(total_xp: int) -> int:
    total_xp = max(0, int(total_xp))
    return 1 + total_xp // 100


def xp_bar_values(total_xp: int) -> tuple[int, int, float]:
    """
    Gaming-style bar toward next level (100 XP per level).
    Returns (xp_into_level 0..99, xp_for_level always 100, fill 0..1).
    """
    total_xp = max(0, int(total_xp))
    into = total_xp % 100
    return into, 100, into / 100.0


def rank_title(level: int) -> str:
    if level >= 25:
        return "Zen Panda"
    if level >= 15:
        return "Focus Ninja"
    if level >= 8:
        return "Deep-Work Demon"
    if level >= 3:
        return "Flow-State Hacker"
    return "Coding Cub"


def normalize_focus_stats(raw) -> dict:
    if not isinstance(raw, dict):
        raw = {}
    return {
        "total_focus_minutes": max(0, int(raw.get("total_focus_minutes", 0) or 0)),
        "total_xp": max(0, int(raw.get("total_xp", 0) or 0)),
        "sessions_completed": max(0, int(raw.get("sessions_completed", 0) or 0)),
        "streak_days": max(0, int(raw.get("streak_days", 0) or 0)),
        "last_focus_date": raw.get("last_focus_date"),
    }


def streak_after_session(prev: dict, today: date | None = None) -> tuple[int, str]:
    """
    Streak when a session completes successfully (same day = keep streak; yesterday = +1; gap = 1).
    Returns (new_streak, last_focus_date_iso).
    """
    today = today or date.today()
    today_s = today.isoformat()
    prev_streak = int(prev.get("streak_days", 0) or 0)
    raw_last = prev.get("last_focus_date")

    if not raw_last or not isinstance(raw_last, str):
        return 1, today_s

    try:
        last = date.fromisoformat(raw_last[:10])
    except ValueError:
        return 1, today_s

    if last == today:
        return max(1, prev_streak), today_s
    if last == today - timedelta(days=1):
        return prev_streak + 1, today_s
    return 1, today_s


def xp_for_session(minutes: int, streak_days: int) -> int:
    base = minutes * 10
    bonus = min(7, max(0, streak_days)) * 5
    return base + bonus


def reward_summary_rows(
    minutes: int,
    xp_earned: int,
    total_xp_after: int,
    streak: int,
    old_level: int,
    new_level: int,
) -> list[tuple[str, str]]:
    """
    Rows for the focus completion UI. Each item is (kind, text).
    kind: title | xp | meta | levelup | level | total
    """
    rows: list[tuple[str, str]] = [
        ("title", f"You crushed a {minutes}-minute focus session!"),
        ("xp", f"+{xp_earned} XP"),
        ("meta", f"Streak: {streak} day{'s' if streak != 1 else ''}"),
    ]
    if new_level > old_level:
        rows.append(("levelup", f"Level up! Now level {new_level} — {rank_title(new_level)}"))
    else:
        rows.append(("level", f"Level {new_level} — {rank_title(new_level)}"))
    rows.append(("total", f"Total XP: {total_xp_after}"))
    return rows


def reward_summary(
    minutes: int,
    xp_earned: int,
    total_xp_after: int,
    streak: int,
    old_level: int,
    new_level: int,
) -> str:
    return "\n".join(t for _, t in reward_summary_rows(
        minutes, xp_earned, total_xp_after, streak, old_level, new_level
    ))
