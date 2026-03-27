# FileOrganiser
File Organiser for Windows

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
