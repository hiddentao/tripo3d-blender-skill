#!/usr/bin/env bash
# Runs the skill's two Blender scripts on a deliberately awkward model and
# checks what they produce. Needs Blender 5.x; set BLENDER to its binary if the
# `blender` command is not on the path. Spends no Tripo3D credits.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
tools="$here/../tripo3d-blender/tools"
blender="${BLENDER:-blender}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

run() { "$blender" --background --factory-startup --python-exit-code 1 --python "$@"; }

run "$here/selftest.py" -- make "$work/raw.glb" | grep '^SELFTEST'
run "$tools/finish_model.py" -- "$work/raw.glb" "$work/out.glb" \
  --height 2 --name test --turn -90 --levels 0.4,0.12 --texture 512 | grep '^FINISHED'
run "$here/selftest.py" -- check "$work/out.glb" "$work/out-1.glb" "$work/out-2.glb" \
  | grep '^SELFTEST'
run "$tools/preview_model.py" -- "$work/out.glb" "$work/preview" --size 160 >/dev/null
for view in front side top; do
  test -s "$work/preview/$view.png" || { echo "FAIL: no $view.png"; exit 1; }
done
echo "OK: the finishing and preview scripts pass"
