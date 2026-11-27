# Blender

Tripo3D gives the base model. Everything after that happens here: measuring,
turning, cleaning, repairing, repainting, cutting levels of detail and
exporting. Blender work is free and repeatable, so it comes before any new
paid run.

## Installing Blender

Use Blender 5.x. On macOS, Homebrew's cask puts the `blender` command on the
path:

```bash
brew install --cask blender
blender --version
```

Without Homebrew, call the binary inside the app,
`/Applications/Blender.app/Contents/MacOS/Blender`. Run every script with
Blender's own Python through `--python`. Plain `python3` has no `bpy` module.

## The finishing script

`tools/finish_model.py` turns a raw GLB into a measured, clean GLB and its
coarser copies.

| Argument | Status | What it does |
| --- | --- | --- |
| `src` | required | The raw GLB |
| `dst` | required | The finished GLB; copies are written beside it as `-1`, `-2` |
| `--height` | required | Final height in metres |
| `--name` | optional | Object and mesh name; `model` by default |
| `--turn` | optional | Degrees about the vertical axis; 0 by default |
| `--levels` | optional | Triangle shares for coarser copies, such as `0.4,0.12`; none by default |
| `--texture` | optional | Largest texture side in texels; 0 keeps the textures |

In order, it:

1. imports the GLB into an empty scene;
2. bakes every object's world transform into its vertices, removes parents
   and empties, and joins the meshes into one object;
3. merges vertices that sit on top of each other, which joins the seams that
   a GLB stores as separate vertices;
4. turns the model by `--turn` degrees, scales it to `--height`, centres it
   and puts its lowest point at height 0;
5. shrinks every texture longer than `--texture` texels;
6. makes one decimated copy for each share in `--levels`;
7. writes each file and prints `FINISHED` with a JSON summary: the name, the
   size in metres, the shrunk textures, and each file's triangles and bytes.

A positive `--turn` turns the model anticlockwise seen from above, so +90
takes +x to +y and -90 takes +x to -y. Tripo's docs give +x as the forward
axis of a generated model, and Blender's front view shows the side facing -y,
so `--turn -90` usually brings the front round. Check it on a preview.

The coarser copies are separate files that share one origin. An engine that
wants all levels in one file, such as glTF with `MSFT_lod`, needs the
project's own exporter; give it the finished meshes.

## The preview script

`tools/preview_model.py` renders `front.png`, `side.png` and `top.png` from a
GLB with orthographic cameras that frame the whole model. A grey sky and one
sun light it, and Cycles renders on the CPU, which works with no window.
`--size` sets the square image size, 640 by default. The front camera looks
along +y, so `front.png` shows the side that faces -y. Read the pictures
after every change; a number in the summary cannot show a backwards face or a
lost texture.

## Which fix goes where

| What is wrong | Fix it in Blender | Pay for Tripo3D only if |
| --- | --- | --- |
| Size, facing, pivot, stray parent transforms | `finish_model.py` with `--height` and `--turn` | Never |
| Too many triangles, or levels of detail needed | `--levels`, or Tripo's `tripo mesh decimate` (30 to 40 credits) when Blender's decimation spoils the shape | Never |
| Lumps, soft detail, odd hands, small holes | Fill holes and smooth (below), or sculpt in a live Blender | The outline or the proportions are wrong |
| Faces that render dark or vanish | Recalculate the normals (below) | Never |
| Blocky, faceted shading on curved parts | Shade smoothly by angle (below) | Never |
| Colour or tone off | Tint the texture (below), or paint it in a live Blender | The texture is unusable: `tripo model texture` re-textures the same mesh |
| Light baked into the texture | Paint it out | Generate again with `delight=true` |
| Parts fused that must move or show apart | Split the loose parts (below), or cut with a bisect | Real named parts are needed: `tripo mesh segment` |
| One dimension off the spec, such as a side 8% too deep | Scale that axis alone (below) | Never |
| A thin part painted out of the pictures: an antenna, a rail, a rope | Build it (below) | Never |
| Too many triangles for a real-time scene, at AAA detail | Bake onto a game mesh with `bake_maps.py` | Never |
| Textures too large | `--texture` | Never |

## A repair script

Repair between two finishing runs, so the levels of detail carry the fix:

1. finish the raw file with `--height` and `--turn`, without `--levels`;
2. repair that finished file with a script like the one below;
3. finish the repaired file again with `--levels` and `--texture`.

The second finishing run keeps the height and needs no turn. This script ran
on Blender 5.3 against a finished GLB. It starts from an empty scene, takes
the one mesh object as `obj`, applies two fixes and writes the result:

```python
# Repairs a finished model and writes it out again:
#   blender --background --factory-startup --python repair.py -- in.glb out.glb
import sys

import bmesh
import bpy

src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src, merge_vertices=True)
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

# Fill small holes and point every face outward.
bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=8)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(obj.data)
bm.free()

# Shade smoothly, keeping edges sharper than 30 degrees crisp.
bpy.ops.object.shade_smooth_by_angle(angle=0.5236)

bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=True)
print(f'REPAIRED {dst}')
```

A dark patch has two common causes. Faces that point inward render dark or
vanish, and the normals fix above turns them round. A faceted, blocky look on
a curved surface is flat shading, and smoothing by angle fixes it. Render a
preview to see which one you have.

A file's size in bytes can change a lot between exports. In the test above,
the repair took a finished file from 313 KB to 109 KB with the same 3,980
triangles and the same 512-texel texture. Compare triangles and texture
sizes, not bytes.

## Fixes as code

Each snippet below ran on Blender 5.3 against a finished GLB. Put the ones you
need into a script like the one above, between the import and the export.

> A GLB stores every texture seam as separate vertices, so after an import
> each seam looks like a hole and each face can look like its own part.
> Merge the doubled vertices first, as the first snippet does. Without it,
> filling holes patches the seams, splitting by loose parts gave 2,266
> pieces where the model had 2, and decimating tore a test model apart. The
> importer's `merge_vertices=True` option is not enough: on Blender 5.3 it
> left all 8,535 vertices of a test model split, and `remove_doubles` took
> them to 2,010.

Merge the seams, fill small holes and point every face outward:

```python
import bmesh

bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=8)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(obj.data)
bm.free()
```

`sides=8` fills holes with up to eight edges; raise it for larger gaps.

Smooth the whole mesh a little, then keep the result:

```python
mod = obj.modifiers.new('smooth', 'SMOOTH')
mod.factor, mod.iterations = 0.5, 4
depsgraph = bpy.context.evaluated_depsgraph_get()
smoothed = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
obj.modifiers.clear()
obj.data = smoothed
```

This softens every edge. For one lump, sculpt it in a live Blender and then
script the result, or limit the modifier to a vertex group with
`mod.vertex_group`.

Tint the base colour texture by multiplying its pixels. The export writes the
changed pixels:

```python
import numpy as np

def base_colour_image(material):
    for node in material.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED' and node.inputs['Base Color'].links:
            return node.inputs['Base Color'].links[0].from_node.image
    return None

image = base_colour_image(obj.active_material)
pixels = np.empty(len(image.pixels), dtype=np.float32)
image.pixels.foreach_get(pixels)
pixels = pixels.reshape(-1, 4)
pixels[:, :3] *= (0.55, 0.8, 0.6)          # greener and darker
image.pixels.foreach_set(pixels.ravel())
image.update()
```

Split fused parts into separate objects, after merging the seams:

```python
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')
```

Rebuild the surface as an even mesh, which closes holes and removes inner
pieces:

```python
obj.data.remesh_voxel_size = 0.02          # metres between new vertices
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.voxel_remesh()
```

The new faces no longer match the old texture layout. Unwrap the new mesh and
bake the original's maps onto it (Cycles, *Selected to Active*), or let
Tripo's `tripo mesh decimate` rebuild the mesh with the textures baked on.

Carry the reviewer's points: scale one axis to the spec, and build a thin
part that the pictures left out. On the test crate this took the depth from
0.778 m to the spec's 0.7 m and put a 0.4 m antenna at the crate's own left
rear corner:

```python
from mathutils import Matrix

# Scale one axis to the spec: here the depth (y) to 0.7 m.
obj.data.transform(Matrix.Diagonal((1, 0.7 / obj.dimensions.y, 1, 1)))
obj.data.update()

# Build a thin part that was painted out of the pictures: a 0.4 m antenna on
# the top at the model's own left rear corner (+x is own left, +y is the rear).
xs, ys, zs = zip(*(v.co for v in obj.data.vertices))
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.006,
                      radius2=0.004, depth=0.4)
bmesh.ops.translate(bm, verts=bm.verts,
                    vec=(max(xs) - 0.06, max(ys) - 0.06, max(zs) + 0.2))
mesh = bpy.data.meshes.new('antenna')
bm.to_mesh(mesh)
bm.free()
steel = bpy.data.materials.new('steel')
if steel.node_tree is None:
    steel.use_nodes = True
shader = steel.node_tree.nodes['Principled BSDF']
shader.inputs['Base Color'].default_value = (0.55, 0.56, 0.58, 1)
shader.inputs['Metallic'].default_value = 1.0
shader.inputs['Roughness'].default_value = 0.4
mesh.materials.append(steel)
antenna = bpy.data.objects.new('antenna', mesh)
bpy.context.collection.objects.link(antenna)

bpy.ops.object.select_all(action='DESELECT')
antenna.select_set(True)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.join()
```

Do this before the bake, so the game mesh gets the part too.

Export only what you selected:

```python
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=True)
```

## Checking the model against the views

`tools/compare_views.py` renders a finished model from the views that
`prepare_views.py` wrote, framed the same way, and measures how far the
outlines agree:

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/compare_views.py -- \
  build/crate.glb views/crate build/crate-compare --size 512
```

For each view it writes a picture of three panels: the reference, the
render, and an overlay in which grey is shared, red is only in the reference
(missing from the model) and blue is only in the model. `compare.json` and
the `COMPARED` line give, for each view, the outline agreement from 0 to 1,
the shares missing and extra, the width and height of the model against the
reference, and the colour of each.

The model must face -y, as `finish_model.py` leaves it. The left camera
looks at the model's own left side, which is +x. The figures on 2026-11-27:

| Model | Outline agreement |
| --- | --- |
| The self-test model against renders of itself | 0.95 to 0.98 |
| A Tripo3D H3.1 crate against its four input views | 0.93 to 0.95; the lightness of each view within 0.03 |
| The same views with left and right swapped | 0.47 |

A good model scored 0.93 or more in these tests. For a view well under that,
look at its overlay before you change anything, and send the pictures to the
reviewer with the figures.

## Baking onto a game mesh

An AAA model from Tripo3D has hundreds of thousands of faces. A real-time
scene wants a game mesh of tens of thousands, with the fine detail in its
texture maps. `tools/bake_maps.py` does that:

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/bake_maps.py -- \
  build/crate.glb build/crate-game.glb --triangles 30000 --size 2048
```

| Argument | Status | What it does |
| --- | --- | --- |
| `src` | required | The detailed, finished GLB |
| `dst` | required | The game GLB to write |
| `--triangles` | optional | Triangles of the game mesh it cuts down from the detailed one; 30,000 by default |
| `--low` | optional | A game mesh of your own instead, in the same place as the detailed model |
| `--size` | optional | Side of each map in texels; 2048 by default |
| `--cage` | optional | How far the bake looks out from the game mesh, as a share of the model's largest side; 0.01 by default |
| `--margin` | optional | Texels of bleed around each UV island; 16 by default |
| `--unwrap` | optional | Unwrap a supplied game mesh even when it has UVs |

It merges the seam vertices, cuts the mesh down or reads `--low`, and lays
the game mesh flat for texturing when it was cut down here or has no UV map.
Then it bakes, with Cycles, a base colour map, a tangent normal map, and a
roughness and metalness map in glTF's layout (green roughness, blue metal).
It gives the game mesh one material with the maps and writes the GLB.

On 2026-11-27 it baked the 440,650-triangle crate onto 30,000 triangles with
2048-texel maps in 37 seconds on a CPU. The game crate scored the same
outline agreement as the detailed one, 0.93 to 0.95, and looked the same in
the previews.

A cut-down mesh has uneven triangles and many UV islands. It suits props. A
character that bends, or a hero piece seen very close, wants a clean game
mesh made by hand in Blender over the detailed model, given with `--low`.
Tripo's own `tripo mesh decimate` also gives a mesh that sits on the same
model. If the normal map has holes or smears, raise `--cage`; if detail from
another part shows up, lower it.

Finish and repair first, bake last, then cut levels of detail from the game
GLB with `finish_model.py --levels`, or let the engine make them.

## For the web: null3d

When the target is the web, use null3d
(<https://github.com/null3d-engine/null3d>) in place of three.js or another
web engine. It is a browser 3D engine in Rust and WebAssembly, built for
agents, and it loads glTF models. Its asset tool prepares the files that this
skill writes. The steps below come from null3d's documentation, read on
2026-11-27; they were not run for this skill.

1. Finish one GLB for each model, without `--levels`. null3d's tool makes
   its own levels of detail inside the file, each with about half the
   triangles of the one above.
2. For an AAA prop, bake it onto a game mesh first. A large static piece,
   such as a cliff, a building or a scan, can keep its detailed mesh:
   null3d's `--clusters` option splits it into patches that draw fine near
   the camera and coarse far from it, up to about 4 million triangles.
3. Optimize the files. The tool encodes textures as KTX2, at most 2048
   texels a side, so 4K or 8K maps gain nothing there. `--texture-quality
   high` keeps more detail in the maps at a larger size:

   ```bash
   bunx @null3d/cli assets optimize build/ public/models/ --lod \
     --texture-quality high
   ```

   Add `--clusters` for large static meshes, and `--stages` to download the
   finer levels after the first picture. A Vite project can do the same at
   import with `@null3d/vite-plugin`.
4. Load each file once with `await assets.loadGltf(url)` and place it with
   `scene.instantiate(prefab)`, or many copies with `scene.createInstances`.
5. Check the model in the engine: `bunx @null3d/cli shot --out shot.png`
   draws one frame of the project's page in a headless browser.

`finish_model.py` leaves the front facing -y in Blender, which the glTF
export turns into +Z, glTF's own front.

## Live Blender

A live Blender suits work that needs eyes and hands: sculpting a face,
painting moss, comparing views. Blender Lab's MCP add-on and server connect an
agent to the open Blender.

1. Download the add-on (`mcp-<version>.zip`) and the server bundle
   (`blender-<version>.mcpb`) from
   <https://projects.blender.org/lab/blender_mcp/releases>. Version 1.0.3 was
   tested.
2. In Blender, install the add-on zip as an extension from disk (Preferences,
   Get Extensions, the menu at the top right, Install from Disk).
3. Unpack the server bundle into a folder; it is a zip file. Register it:

   ```bash
   claude mcp add --scope user blender -- \
     uv run --directory <server-folder> blender-mcp
   ```

4. The human turns on *Allow Online Access* in Preferences, System, Network,
   and restarts Blender. The add-on does not start without it.

The add-on listens on `localhost:9876`. Check it before you call any tool:

```bash
lsof -nP -iTCP:9876 -sTCP:LISTEN
```

If nothing listens, Blender is closed or *Allow Online Access* is off: ask
the human. Do not change Blender's preferences from the command line while it
is open, because it saves its preferences when it quits and overwrites the
change. The server's tools include `execute_blender_code`,
`get_objects_summary`, `render_viewport_to_path` and
`get_screenshot_of_window_as_image`.

## Fitting into a project's build

A hand edit in a live session cannot be repeated or reviewed, and the next
regeneration loses it. So every change that ships ends up in a script that
rebuilds the model from the raw file, headless:

1. try the change live and look at it;
2. write the same steps into the build script;
3. rebuild from the raw file and render the previews;
4. commit the script with the raw file.

If the project already has a Blender build for its models, add these steps to
it. Its exporter knows the project's conventions, such as how levels of
detail are stored and how textures are compressed.
