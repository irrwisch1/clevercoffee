import gzip
import os
import sys

SRC_DIR = "frontend/html"
BUILD_DIR = "data/html"

def build_html():
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    for filename in os.listdir(SRC_DIR):
        if not filename.endswith(".html"):
            continue
        src_path = os.path.join(SRC_DIR, filename)
        dest_path = os.path.join(BUILD_DIR, filename + ".gz")

        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Write compressed: the pages no longer need a template processor, so the
        # webserver can serve them straight from flash. serveStatic picks the .gz up
        # on its own and sends Content-Encoding: gzip.
        with gzip.open(dest_path, 'wt', encoding='utf-8') as f:
            f.write(content)

        # Drop a leftover uncompressed copy from an earlier build, it would only
        # take up flash.
        stale = os.path.join(BUILD_DIR, filename)
        if os.path.exists(stale):
            os.remove(stale)

        print(f"{filename} -> {filename}.gz ({os.path.getsize(dest_path)} bytes)")

if "buildfs" in sys.argv:
    build_html()