import subprocess
from datetime import datetime
from pathlib import Path


SEEN: dict[Path, int] = {}


def note_read(path: str | Path) -> None:
    path = Path(path).resolve()
    SEEN[path] = path.stat().st_mtime_ns


def stale_files() -> list[str]:
    changed = []
    for path, mtime in SEEN.items():
        try:
            current_mtime = path.stat().st_mtime_ns
        except OSError:
            current_mtime = None
        if current_mtime != mtime:
            changed.append(path.as_posix())
    return changed


def stale_note() -> str:
    changed = stale_files()
    if not changed:
        return ""
    return (
        "\n<system-reminder>\n"
        "These files changed or became unavailable since you read them. "
        "Read them again before relying on their contents or editing them:\n"
        + "\n".join(changed)
        + "\n</system-reminder>"
    )


def git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    if result.returncode != 0:
        return "unavailable"
    return result.stdout.strip() or "detached HEAD"


def reminder() -> dict[str, str]:
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now().astimezone().isoformat(timespec='seconds')}\n"
            f"git branch: {git_branch()}\n"
            "</env>" + stale_note()
        ),
    }
