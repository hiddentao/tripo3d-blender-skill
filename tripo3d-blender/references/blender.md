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
> Merge the doubled vertices first, as the first snippet does, or import with
> `bpy.ops.import_scene.gltf(filepath=src, merge_vertices=True)`. Without it,
> filling holes patches the seams, and splitting by loose parts gave 2,266
> pieces where the model had 2.

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

Export only what you selected:

```python
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=True)
```

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
