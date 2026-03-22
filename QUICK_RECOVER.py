import json
import shutil
from pathlib import Path

HISTORY_DIR = Path.home() / "Library" / "Application Support" / "Code" / "User" / "History"
TARGET_PREFIX = "file:///Users/pujeth/Quant-AI-Trading/"
PROJECT_DIR = Path("/Users/pujeth/Quant-AI-Trading")

def recover():
    if not HISTORY_DIR.exists():
        print("History directory not found.")
        return

    recovered_files = 0
    
    # Iterate through all random subfolders in History
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
            if resource.startswith(TARGET_PREFIX):
                # We found a file that belongs to the project!
                rel_path = resource[len(TARGET_PREFIX):]
                
                # Ignore temp/venv files
                if any(x in rel_path for x in [".venv/", "venv/", "__pycache__/", ".git/", "node_modules/", ".next/"]):
                    continue
                    
                entries = data.get("entries", [])
                if not entries:
                    continue
                    
                # Find the latest entry by timestamp
                latest_entry = max(entries, key=lambda e: e.get("timestamp", 0))
                latest_id = latest_entry.get("id")
                
                source_file = entry_dir / latest_id
                target_file = PROJECT_DIR / rel_path
                
                if source_file.exists():
                    # Create parent dirs
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    print(f"Recovered: {rel_path}")
                    recovered_files += 1
                    
        except Exception as e:
            print(f"Error parsing {entries_file}: {e}")
            
    print(f"\nSuccessfully recovered {recovered_files} files.")

if __name__ == "__main__":
    recover()
