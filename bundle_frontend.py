import gzip
import os
import shutil
import subprocess
import sys

"""
Builds the frontend bundles with esbuild and writes them to data/ gzipped.

Why bundle at all: load-libs.js used to load eight files strictly sequentially -- a
CDN probe, then three stylesheets, then four scripts, each in the previous one's
.then(). That was not a style problem but a necessity: eight parallel asset requests
took the board off the network reproducibly (5 of 8 hung with a truncated body). The
price was eight round trips plus parse steps per page load.

One bundle for every page. That works only because temp.js does nothing at module
level: it exposes window.initCharts and index.html calls it. A self-starting temp.js
would fetch /timeseries on every page load -- the endpoint that caused the crashes --
and fail on the pages without #chart-temperature.

The vendored libraries are the ESM distributions, imported by name from app.js and
temp.js, so esbuild resolves them like any other module. The global builds
(vue.global.prod.js, uPlot.iife.min.js) would not survive bundling: they publish their
global with a top-level `var`, which --format=iife turns into a closure-local, and the
page then fails with "Vue is not defined".

Writes to data/ and compresses here rather than relying on auto_compression.py:
maintaining its allow-list and this output separately is the kind of coupling that
already went wrong with the HTML.
"""

BUNDLES = [
    ("frontend/js/bundle.entry.js", "data/js/bundle.js"),
    ("frontend/css/bundle.entry.css", "data/css/bundle.css"),
]

# Do not inline the font files: the references in fontawesome.min.css are relative
# (../webfonts/...) and the bundle lands under /css/ again, so they still resolve.
EXTERNAL = ["*.woff2", "*.woff", "*.ttf", "*.eot", "*.svg"]

POPPER = "./frontend/vendor/popper.esm.js"


def esbuild_binary():
    found = shutil.which("esbuild")
    if found:
        return [found]
    if shutil.which("npx"):
        return ["npx", "--yes", "esbuild@0.25.5"]
    sys.exit(
        "ERROR: esbuild not found.\n"
        "  Debian/Ubuntu: sudo apt install esbuild\n"
        "  otherwise:     npm i -g esbuild@0.25.5"
    )


def build():
    cmd_base = esbuild_binary()

    for src, dest in BUNDLES:
        if not os.path.exists(src):
            sys.exit(f"ERROR: {src} is missing")

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        cmd = cmd_base + [src, "--bundle", "--minify", "--target=es2020", f"--outfile={dest}"]
        if src.endswith(".js"):
            cmd.append("--format=iife")
            # bootstrap.esm.min.js imports @popperjs/core as a bare specifier -- that is
            # why a .bundle. build exists at all. Popper ships as a tree of dozens of
            # small ESM modules, so update-libs.sh flattens it into one vendored file
            # and this maps the specifier onto it. Keeps the build free of node_modules.
            cmd.append(f"--alias:@popperjs/core={POPPER}")
        cmd += [f"--external:{pattern}" for pattern in EXTERNAL]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr.strip())
            sys.exit(f"ERROR: esbuild failed on {src}")

        with open(dest, "rb") as raw, gzip.open(dest + ".gz", "wb", compresslevel=9) as gz:
            shutil.copyfileobj(raw, gz)

        raw_size = os.path.getsize(dest)
        gz_size = os.path.getsize(dest + ".gz")
        os.remove(dest)  # only the .gz is served; serveStatic finds it on its own
        print(f"{src} -> {dest}.gz ({raw_size} -> {gz_size} bytes)")


if "buildfs" in sys.argv:
    build()
