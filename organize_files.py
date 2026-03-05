#!/usr/bin/env python3
"""
File Organizer - Recursively scans a folder and organizes files by type
into subfolders within a destination directory.

Usage:
    python organize_files.py <source_folder> <destination_folder> [options]

Options:
    --dry-run       Preview what would happen without copying files
    --report        Save a CSV report of all files found
    --no-confirm    Skip confirmation prompt

Examples:
    python organize_files.py C:/Downloads C:/Organized
    python organize_files.py /home/user/docs /home/user/sorted --dry-run
    python organize_files.py . ./organized --report
"""

import os
import sys
import shutil
import csv
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ── Extension → folder name mapping ──────────────────────────────────────────
EXT_GROUPS = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    ".bmp": "Images", ".tiff": "Images", ".tif": "Images", ".webp": "Images",
    ".svg": "Images", ".ico": "Images", ".heic": "Images", ".raw": "Images",
    # Videos
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos", ".mov": "Videos",
    ".wmv": "Videos", ".flv": "Videos", ".webm": "Videos", ".m4v": "Videos",
    ".mpg": "Videos", ".mpeg": "Videos", ".3gp": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio", ".aac": "Audio",
    ".ogg": "Audio", ".wma": "Audio", ".m4a": "Audio", ".opus": "Audio",
    # Documents
    ".pdf": "Documents_PDF", ".doc": "Documents_Word", ".docx": "Documents_Word",
    ".xls": "Documents_Excel", ".xlsx": "Documents_Excel", ".csv": "Documents_Excel",
    ".ppt": "Documents_PowerPoint", ".pptx": "Documents_PowerPoint",
    ".odt": "Documents_OpenOffice", ".ods": "Documents_OpenOffice",
    ".odp": "Documents_OpenOffice", ".rtf": "Documents_Text",
    ".txt": "Documents_Text", ".md": "Documents_Text", ".rst": "Documents_Text",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives", ".tar": "Archives",
    ".gz": "Archives", ".bz2": "Archives", ".xz": "Archives", ".iso": "Archives",
    # Code
    ".py": "Code_Python", ".js": "Code_JavaScript", ".ts": "Code_JavaScript",
    ".html": "Code_Web", ".htm": "Code_Web", ".css": "Code_Web",
    ".java": "Code_Java", ".c": "Code_C", ".cpp": "Code_C", ".h": "Code_C",
    ".cs": "Code_CSharp", ".php": "Code_PHP", ".rb": "Code_Ruby",
    ".go": "Code_Go", ".rs": "Code_Rust", ".swift": "Code_Swift",
    ".sh": "Code_Scripts", ".bat": "Code_Scripts", ".ps1": "Code_Scripts",
    ".sql": "Code_SQL", ".json": "Code_Data", ".xml": "Code_Data",
    ".yaml": "Code_Data", ".yml": "Code_Data", ".toml": "Code_Data",
    # Executables
    ".exe": "Executables", ".msi": "Executables", ".dmg": "Executables",
    ".deb": "Executables", ".rpm": "Executables", ".app": "Executables",
    # Fonts
    ".ttf": "Fonts", ".otf": "Fonts", ".woff": "Fonts", ".woff2": "Fonts",
}

def get_folder_name(ext: str) -> str:
    """Return the destination subfolder name for a given extension."""
    ext_lower = ext.lower()
    return EXT_GROUPS.get(ext_lower, f"Other_{ext_lower.lstrip('.').upper() or 'NoExtension'}")


def scan_files(source: Path) -> list[dict]:
    """Recursively scan source and return list of file info dicts."""
    files = []
    for root, _dirs, filenames in os.walk(source):
        for name in filenames:
            filepath = Path(root) / name
            ext = filepath.suffix
            folder = get_folder_name(ext)
            files.append({
                "source_path": filepath,
                "name": name,
                "extension": ext.lower() if ext else "(none)",
                "folder": folder,
                "size_bytes": filepath.stat().st_size,
            })
    return files


def print_summary(files: list[dict]) -> None:
    """Print a grouped summary table."""
    by_folder = defaultdict(list)
    for f in files:
        by_folder[f["folder"]].append(f)

    total_size = sum(f["size_bytes"] for f in files)
    print(f"\n{'─'*60}")
    print(f"  {'FOLDER':<35} {'FILES':>6}  {'SIZE':>10}")
    print(f"{'─'*60}")
    for folder in sorted(by_folder):
        count = len(by_folder[folder])
        size  = sum(f["size_bytes"] for f in by_folder[folder])
        print(f"  {folder:<35} {count:>6}  {fmt_size(size):>10}")
    print(f"{'─'*60}")
    print(f"  {'TOTAL':<35} {len(files):>6}  {fmt_size(total_size):>10}")
    print(f"{'─'*60}\n")


def fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def copy_files(files: list[dict], dest: Path, dry_run: bool) -> tuple[int, int]:
    """Copy files to destination subfolders. Returns (copied, skipped)."""
    copied = skipped = 0
    for f in files:
        target_dir  = dest / f["folder"]
        target_path = target_dir / f["name"]

        # Handle name collisions by appending a counter
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        counter = 1
        stem, suffix = Path(f["name"]).stem, Path(f["name"]).suffix
        while target_path.exists():
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        if dry_run:
            print(f"  [DRY-RUN] {f['source_path']}  →  {target_path}")
            copied += 1
        else:
            try:
                shutil.copy2(f["source_path"], target_path)
                copied += 1
            except Exception as e:
                print(f"  [ERROR] {f['source_path']}: {e}")
                skipped += 1

    return copied, skipped


def save_report(files: list[dict], dest: Path) -> Path:
    """Write a CSV report listing every file."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = dest / f"_file_report_{ts}.csv"
    dest.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "extension", "folder",
                                                 "size_bytes", "source_path"])
        writer.writeheader()
        writer.writerows(
            {k: v for k, v in f.items() if k != "size_bytes" or True}
            for f in sorted(files, key=lambda x: (x["folder"], x["name"]))
        )
    return report_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Recursively organize files by type into subfolders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("source",      help="Source folder to scan")
    parser.add_argument("destination", help="Destination folder for organized files")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Preview actions without copying anything")
    parser.add_argument("--report",    action="store_true",
                        help="Save a CSV report of all discovered files")
    parser.add_argument("--no-confirm", action="store_true",
                        help="Skip the confirmation prompt")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    dest   = Path(args.destination).resolve()

    if not source.exists():
        print(f"[ERROR] Source folder not found: {source}")
        sys.exit(1)

    if source == dest or dest.is_relative_to(source):
        print("[ERROR] Destination must be outside the source folder.")
        sys.exit(1)

    print(f"\nScanning: {source}")
    files = scan_files(source)

    if not files:
        print("No files found. Nothing to do.")
        sys.exit(0)

    print_summary(files)

    if args.dry_run:
        print("── DRY RUN – no files will be copied ──\n")
        copy_files(files, dest, dry_run=True)
        print(f"\nDry run complete. {len(files)} file(s) would be processed.")
        return

    if not args.no_confirm:
        ans = input(f"Copy {len(files)} file(s) to '{dest}'? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    print(f"\nCopying to: {dest}\n")
    copied, skipped = copy_files(files, dest, dry_run=False)

    if args.report:
        rp = save_report(files, dest)
        print(f"\nReport saved: {rp}")

    print(f"\n✓ Done — {copied} copied, {skipped} skipped/errored.")


if __name__ == "__main__":
    main()