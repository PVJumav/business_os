import os
from pathlib import Path


def get_upload_root() -> Path:
    configured = os.getenv("BUSINESS_OS_UPLOAD_DIR")
    candidates = [Path(configured)] if configured else []
    candidates.extend([
        Path("uploads"),
        Path.home() / "Documents" / "Codex" / "business-os-runtime-uploads",
    ])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except OSError:
            continue
    raise RuntimeError("No writable upload directory is available")


def resolve_upload_url(file_url: str) -> Path:
    parts = file_url.lstrip("/").split("/")
    if parts and parts[0] == "uploads":
        parts = parts[1:]
    return get_upload_root().joinpath(*parts)
