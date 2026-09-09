import os
import gzip
import shutil

import sys


"""
This script compresses specific files from the frontend directory into the data directory.
Files listed in FILES_TO_COMPRESS will be compressed using gzip and saved with a .gz extension.
Other files will be copied as-is to the data directory.
TODO: Handle the files which are templated.
"""

# Empty on purpose: bundle_frontend.py builds the JS and CSS and writes them to data/
# compressed itself, precompile_html.py does the same for the pages. Keeping the same
# output in two places is the coupling that already went wrong once with the HTML.
FILES_TO_COMPRESS = []

FILES_TO_SKIP = [
    # The page is produced by precompile_html.py, which compresses it itself.
    "html/index.html",
    # Bundle sources, not shipped individually.
    "js/app.js",
    "js/temp.js",
    "css/bundle.entry.css",
    "css/icons.css",
    # Library manifest and refresh helper, both build-host only.
    "package.json",
    "update-libs.sh",
]

FRONTEND_DIR = "frontend"
DATA_DIR = "data"

def ensure_dir_exists(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {path}: {e}")

def compress_file(src_path, dest_path):
    try:
        with open(src_path, "rb") as f_in, gzip.open(dest_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    except (IOError, OSError) as e:
        print(f"Error compressing {src_path}: {e}")

        # Clean up partial file
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        return False
    return True

def copy_file(src_path, dest_path):
    try:
        shutil.copy2(src_path, dest_path)
    except (IOError, OSError) as e:
        print(f"Error copying {src_path}: {e}")
        return False
    return True

def main():
    compress_set = set(FILES_TO_COMPRESS)
    skip_set = set(FILES_TO_SKIP)
    found_files = set()

    for root, dirs, files in os.walk(FRONTEND_DIR):
        # vendor/ holds the source libraries. They reach the device through the
        # bundles, never on their own.
        dirs[:] = [d for d in dirs if d != "vendor"]

        for file in files:
            rel_dir = os.path.relpath(root, FRONTEND_DIR)
            rel_file = os.path.join(rel_dir, file) if rel_dir != "." else file
            rel_file = rel_file.replace(os.sep, "/")
            found_files.add(rel_file)

            src_path = os.path.join(root, file)

            if rel_file in compress_set:
                dest_file = rel_file + ".gz"
                dest_path = os.path.join(DATA_DIR, dest_file)
                print(f"Compressing {rel_file} -> {dest_file}")
                ensure_dir_exists(os.path.dirname(dest_path))
                compress_file(src_path, dest_path)
            else:
                if rel_file not in skip_set:
                    dest_path = os.path.join(DATA_DIR, rel_file)
                    print(f"Copying {rel_file}")
                    ensure_dir_exists(os.path.dirname(dest_path))
                    copy_file(src_path, dest_path)

    # Check for missing files
    missing_files = compress_set - found_files

    if missing_files:
        print(f"Warning: The following files were not found: {missing_files}")

if "buildfs" in sys.argv:
    main()

if os.environ.get("PROJECT_TASK") == "buildfs":
    main()

