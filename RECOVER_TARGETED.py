import os
import json
import shutil
from pathlib import Path
import subprocess

PROJECT_DIR = Path("/Users/pujeth/Quant-AI-Trading")
TARGET_PREFIX = "file:///Users/pujeth/Quant-AI-Trading/"

def find_all_entries():
    """Find ALL entries.json files across the home directory."""
    result = subprocess.run(
        ["find", str(Path.home() / "Library"), "-name", "entries.json"],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout.strip().split("\n")

def recover():
    entries_files = find_all_entries()
    print(f"Found {len(entries_files)} entries.json files across Library.\n")
    
    recovered = 0
    for ef_path in entries_files:
        if not ef_path or not os.path.exists(ef_path):
            continue
        try:
            with open(ef_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            resource = data.get("resource", "")
            if not resource.startswith(TARGET_PREFIX):
                continue
            rel_path = resource[len(TARGET_PREFIX):]
            if any(x in rel_path for x in ["venv/", "__pycache__/", ".git/", "node_modules/", ".next/"]):
                continue
            
            entries = data.get("entries", [])
            if not entries:
                continue
            
            entry_dir = Path(ef_path).parent
            latest_entry = max(entries, key=lambda e: e.get("timestamp", 0))
            latest_id = latest_entry.get("id")
            source_file = entry_dir / latest_id
            if source_file.exists():
                target = PROJECT_DIR / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target)
                print(f"✅ {rel_path}  [from {ef_path}]")
                recovered += 1
        except Exception:
            pass
    
    print(f"\nTotal restored: {recovered} files from Library-wide sweep.")

if __name__ == "__main__":
    recover()
