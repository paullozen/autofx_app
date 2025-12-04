# manifesto.py
import json
import time

from pathlib import Path
from .paths import MANIFEST_PATH


# ==========================
# CORE LOAD/SAVE
# ==========================
def _deserialize_paths(data):
    """Recursively convert known path keys to absolute Path objects."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k in ("txt_file", "audio_file", "srt_file", "video_file", "image_file") and isinstance(v, str):
                from .paths import to_absolute
                data[k] = str(to_absolute(v))  # Keep as string for JSON compatibility in other parts, but absolute
            elif isinstance(v, (dict, list)):
                _deserialize_paths(v)
    elif isinstance(data, list):
        for item in data:
            _deserialize_paths(item)
    return data


def _serialize_paths(data):
    """Recursively convert known path keys to relative strings."""
    if isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            if k in ("txt_file", "audio_file", "srt_file", "video_file", "image_file") and isinstance(v, (str, Path)):
                from .paths import to_relative
                new_data[k] = to_relative(v)
            elif isinstance(v, dict):
                new_data[k] = _serialize_paths(v)
            elif isinstance(v, list):
                new_data[k] = _serialize_paths(v)
            else:
                new_data[k] = v
        return new_data
    elif isinstance(data, list):
        return [_serialize_paths(item) for item in data]
    return data


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return _deserialize_paths(data)
    return {}


def save_manifest(mf: dict):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_mf = _serialize_paths(mf)
    MANIFEST_PATH.write_text(json.dumps(clean_mf, indent=2, ensure_ascii=False), encoding="utf-8")


# ==========================
# HELPERS
# ==========================
def ensure_entry(base: str):
    mf = load_manifest()
    if base not in mf:
        mf[base] = {
            "txt": "ready",          # TXT already in inbox
            "audio": "pending",
            "audio_downloaded": "pending", # audio downloaded
            "srt": "pending",        # subtitle not yet generated
            "suggestions": "pending",# prompts not yet generated
            "images": "pending",     # images not yet made
            "timeline": "pending",   # timeline JSON not yet created
            "video": "pending",      # final render not yet done
            "last_update": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "sentences": 0,
            "scenes": 0,
            "images_saved": 0,
            "group_size": 1
        }
        save_manifest(mf)
    return mf
def update_stage(base: str, stage: str, status: str, extra: dict | None = None):
    """
    Updates the status of a specific stage of the base.
    """
    mf = load_manifest()
    entry = mf.setdefault(base, {})
    entry[stage] = status
    if extra:
        entry.update(extra)
    entry["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_manifest(mf)


def set_stage(mf: dict, base: str, stage: str, status: str):
    """
    Updates status inline (when mf is already loaded).
    """
    entry = mf.setdefault(base, {})
    entry[stage] = status
    entry["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_manifest(mf)


