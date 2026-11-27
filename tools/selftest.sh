#!/usr/bin/env bash
# Runs the skill's five Blender scripts on a deliberately awkward model and
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

# Reference pictures of the finished model, prepared, then compared with it.
run "$here/selftest.py" -- views "$work/out.glb" "$work/pictures" >/dev/null
run "$tools/prepare_views.py" -- "$work/pictures" "$work/views" --size 256 >/dev/null
run "$here/selftest.py" -- agreement "$work/views/views.json" above 0.95 | grep '^SELFTEST'
run "$tools/compare_views.py" -- "$work/out.glb" "$work/views" "$work/compare" --size 256 >/dev/null
run "$here/selftest.py" -- agreement "$work/compare/compare.json" above 0.94 | grep '^SELFTEST'
for view in front left back right top; do
  test -s "$work/compare/$view.png" || { echo "FAIL: no comparison picture for $view"; exit 1; }
done

# Swapped side views must score low: the check has to catch a mirrored view.
mv "$work/views/left.png" "$work/views/swap.png"
mv "$work/views/right.png" "$work/views/left.png"
mv "$work/views/swap.png" "$work/views/right.png"
run "$tools/compare_views.py" -- "$work/out.glb" "$work/views" "$work/swapped" --size 256 >/dev/null
run "$here/selftest.py" -- agreement "$work/swapped/compare.json" below 0.8 left right | grep '^SELFTEST'

# The finished model baked onto a mesh of a tenth of its triangles keeps its
# shape, so it still matches the reference views.
run "$tools/bake_maps.py" -- "$work/out.glb" "$work/game.glb" --triangles 400 --size 256 \
  | grep '^BAKED'
run "$here/selftest.py" -- baked "$work/game.glb" 450 256 | grep '^SELFTEST'
mv "$work/views/left.png" "$work/views/swap.png"
mv "$work/views/right.png" "$work/views/left.png"
mv "$work/views/swap.png" "$work/views/right.png"
run "$tools/compare_views.py" -- "$work/game.glb" "$work/views" "$work/baked" --size 256 >/dev/null
run "$here/selftest.py" -- agreement "$work/baked/compare.json" above 0.9 | grep '^SELFTEST'
echo "OK: the finishing, preview, view, comparison and bake scripts pass"
