#!/usr/bin/env bash
#
# Refreshes the libraries in vendor/ from the versions pinned in package.json.
#
# The build does NOT need this, and it does not need npm: vendor/ is committed and
# bundle_frontend.py works from a plain checkout. Run this only to move a library to
# a new version -- edit package.json, run this, review the diff.
#
# Why vendored at all: the firmware build stays a git clone plus PlatformIO, with no
# network and no node_modules. The bundles are built from vendor/ by esbuild.
set -eu
cd "$(dirname "$0")"

command -v npm >/dev/null || { echo "npm required to refresh the libraries"; exit 1; }

echo "-- installing the pinned versions ..."
npm install --no-audit --no-fund --silent

copy() {
    local src="$1" dest="vendor/$2"
    [ -f "$src" ] || { echo "   MISSING: $src"; exit 1; }
    cp "$src" "$dest"
    printf "   %-28s %8s bytes\n" "$2" "$(stat -c%s "$dest")"
}

echo "-- copying into vendor/ ..."
# ESM builds, imported by name from app.js and temp.js. The global builds do not
# survive bundling. vue.esm-browser.prod on purpose: the pages carry their templates
# in the DOM, which the runtime-only build cannot compile.
copy node_modules/vue/dist/vue.esm-browser.prod.js     vue.esm.js
copy node_modules/bootstrap/dist/js/bootstrap.esm.min.js bootstrap.esm.js
copy node_modules/uplot/dist/uPlot.esm.js              uPlot.esm.js
copy node_modules/bootstrap/dist/css/bootstrap.min.css bootstrap.min.css
copy node_modules/uplot/dist/uPlot.min.css             uPlot.min.css

# bootstrap.esm imports @popperjs/core, which ships as a tree of small modules --
# flatten it into one vendored file so the firmware build needs no node_modules.
echo "-- flattening @popperjs/core ..."
if command -v esbuild >/dev/null; then ESB=esbuild; else ESB="npx --yes esbuild@0.25.5"; fi
$ESB node_modules/@popperjs/core/dist/esm/index.js --bundle --format=esm --minify \
     --outfile=vendor/popper.esm.js >/dev/null
printf "   %-28s %8s bytes\n" "popper.esm.js" "$(stat -c%s vendor/popper.esm.js)"

echo
echo "Done. Review with 'git diff --stat frontend/' before committing."
echo "node_modules/ is gitignored and can be deleted."
