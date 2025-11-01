import os
from pathlib import Path

# Auto-detect root
HERE = Path(__file__).resolve().parent
ROOT = HERE / "desktop_app"

if not ROOT.exists():
    # maybe user ran from inside desktop_app
    if HERE.name == "desktop_app":
        ROOT = HERE
    else:
        # brute scan
        for p in HERE.iterdir():
            if p.is_dir() and p.name == "desktop_app":
                ROOT = p
                break

def normalize_path(p: Path):
    parts = list(p.parts)
    if "desktop_app" in parts:
        idx = parts.index("desktop_app")
        return Path(*parts[idx:])
    return p

def read_text_safely(fp: Path):
    try:
        return fp.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return fp.read_text(encoding="latin1")

def write_text_safely(fp: Path, text: str):
    # Always write UTF-8
    fp.write_text(text, encoding="utf-8")

def process_file(fp: Path):
    rel = normalize_path(fp.relative_to(ROOT.parent))
    rel_str = str(rel).replace("\\", "/")
    new_header = f"# file: {rel_str}\n"

    text = read_text_safely(fp)
    lines = text.splitlines(True)

    # remove legacy headers
    if lines and lines[0].startswith("# file:"):
        lines = lines[1:]

    # insert updated header
    lines.insert(0, new_header)

    write_text_safely(fp, "".join(lines))


def run():
    for root, dirs, files in os.walk(ROOT):
        # --- skip junk folders ---
        if any(x in root for x in [
            "__pycache__",
            ".pyinstaller_cache",
            "dist",
            "build"
        ]):
            continue

        for name in files:
            if name.endswith(".py"):
                process_file(Path(root) / name)

if __name__ == "__main__":
    print(f"📌 Rewriting headers in: {ROOT}")
    run()
    print("✅ Done.")
