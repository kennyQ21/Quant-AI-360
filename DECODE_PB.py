import json
import subprocess
import glob
from pathlib import Path
import re

CONVO_DIR = Path.home() / ".gemini/antigravity/conversations"
PROJECT_DIR = Path("/Users/pujeth/Quant-AI-Trading")

def decode_and_recover():
    recovered = set()
    pb_files = glob.glob(str(CONVO_DIR / "*.pb"))
    
    for pb_file in pb_files:
        print(f"Decoding {pb_file}...")
        try:
            # Run protoc --decode_raw
            result = subprocess.run(
                ["protoc", "--decode_raw"],
                input=open(pb_file, "rb").read(),
                capture_output=True
            )
            output = result.stdout  # This is BYTES
            
            # Simple regex to find strings that look like JSON containing "TargetFile"
            string_literals = re.findall(br'"((?:\\.|[^"\\])*)"', output)
            
            for s in string_literals:
                try:
                    # s is bytes. decode unicode escapes.
                    decoded_str = s.decode('unicode_escape')
                    if "TargetFile" in decoded_str and ("CodeContent" in decoded_str or "ReplacementContent" in decoded_str or "ReplacementChunks" in decoded_str):
                        if decoded_str.startswith("{") and decoded_str.endswith("}"):
                            data = json.loads(decoded_str)
                            target = data.get("TargetFile", "")
                            if target.startswith("/Users/pujeth/Quant-AI-Trading/"):
                                rel_path = target.replace("/Users/pujeth/Quant-AI-Trading/", "")
                                target_path = PROJECT_DIR / rel_path
                                
                                # Write file if it's new CodeContent
                                if "CodeContent" in data:
                                    target_path.parent.mkdir(parents=True, exist_ok=True)
                                    with open(target_path, "w", encoding="utf-8") as f:
                                        f.write(data["CodeContent"])
                                    recovered.add(rel_path)
                                
                except Exception:
                    pass
        except Exception as e:
            print(f"Error on {pb_file}: {e}")
            
    print(f"\nRecovered {len(recovered)} files from AI logs:")
    for r in sorted(recovered):
        print(f" - {r}")

if __name__ == "__main__":
    decode_and_recover()
