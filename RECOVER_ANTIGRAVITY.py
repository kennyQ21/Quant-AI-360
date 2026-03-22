import json
import shutil
from pathlib import Path

HISTORY_DIR = Path("/Users/pujeth/Library/Application Support/Antigravity/User/History")
PROJECT_DIR = Path("/Users/pujeth/Quant-AI-Trading")
TARGET_PREFIX = "file:///Users/pujeth/Quant-AI-Trading/"

def recover_all_versions():
    """Recover ALL versions of each file, restore the latest one."""
    if not HISTORY_DIR.exists():
        print(f"Not found: {HISTORY_DIR}")
        return

    all_resources = {}  # resource_path -> list of (timestamp, source_file)
    
    for entry_dir in HISTORY_DIR.iterdir():
        if not entry_dir.is_dir():
            continue
        entries_file = entry_dir / "entries.json"
        if not entries_file.exists():
            continue
        try:
            with open(entries_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            resource = data.get("resource", "")
            if not resource.startswith(TARGET_PREFIX):
                continue
            rel_path = resource[len(TARGET_PREFIX):]
            if any(x in rel_path for x in ["venv/", "__pycache__/", ".git/", "node_modules/", ".next/"]):
                continue
            entries = data.get("entries", [])
            for entry in entries:
                ts = entry.get("timestamp", 0)
                eid = entry.get("id")
                src = entry_dir / eid
                if src.exists():
                    if rel_path not in all_resources:
                        all_resources[rel_path] = []
                    all_resources[rel_path].append((ts, src))
        except Exception:
            pass

    print(f"Found history for {len(all_resources)} project files.\n")
    restored = 0
    for rel_path, versions in all_resources.items():
        # Sort by timestamp descending, pick latest
        versions.sort(key=lambda x: x[0], reverse=True)
        latest_ts, latest_src = versions[0]
        target = PROJECT_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(latest_src, target)
        print(f"✅ {rel_path}")
        restored += 1

    print(f"\nTotal restored: {restored} files.")

if __name__ == "__main__":
    recover_all_versions()
