"""
Blender side of the self-test that tools/selftest.sh runs.

  blender --background --factory-startup --python-exit-code 1 \
      --python selftest.py -- make raw.glb
  blender --background --factory-startup --python-exit-code 1 \
      --python selftest.py -- check out.glb out-1.glb out-2.glb
  blender --background --factory-startup --python-exit-code 1 \
      --python selftest.py -- views out.glb pictures/
  blender --background --factory-startup --python-exit-code 1 \
      --python selftest.py -- agreement compare.json below 0.8 left right
  blender --background --factory-startup --python-exit-code 1 \
      --python selftest.py -- baked game.glb 450 256

"make" writes an awkward model: four textured parts, one of them on a single
side and one at the front, under a parent that is moved, turned and scaled,
with a 2048-texel texture, like a generated file with stray transforms.
"check" fails unless every finished file holds one object with no rotation or
scale, stands 2 m tall with its lowest point at height 0, is centred, keeps
its textures at 512 texels or less, and has fewer triangles than the file
before it.

"views" renders a finished model from the front, left, back, right and top
into pictures of different sizes, off centre, some on a plain backdrop and
some transparent, as reference pictures might arrive. Its cameras are set up
here, apart from compare_views.py, so a camera mistake in either one shows.
"agreement" fails unless every outline agreement in a views.json or
compare.json, or every one for the views named, is above, or below, the
given value.

"baked" fails unless a baked game GLB holds one mesh of at most the given
triangles, with a base colour, a normal and a metal-roughness map of the
given size, and a base colour that is not blank.
"""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector


def make(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    image = bpy.data.images.new('grid', 2048, 2048)
    image.generated_type = 'UV_GRID'
    image.pack()
    material = bpy.data.materials.new('grid')
    if material.node_tree is None:
        material.use_nodes = True
    texture = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = image
    shader = material.node_tree.nodes['Principled BSDF']
    material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    root = bpy.data.objects.new('root', None)
    bpy.context.collection.objects.link(root)
    root.location = (5, -3, 7)
    root.rotation_euler = (0.4, 0.2, 1.1)
    root.scale = (3, 3, 3)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.5, location=(0, 0, 1))
    sphere = bpy.context.active_object
    bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 0.2))
    cube = bpy.context.active_object
    # An arm on one side and a nose on another, so no view is a mirror of its opposite.
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.45, 0, 0.35), scale=(1.5, 1, 1))
    arm = bpy.context.active_object
    bpy.ops.mesh.primitive_cube_add(size=0.15, location=(0, -0.5, 1.05))
    nose = bpy.context.active_object
    for part in (sphere, cube, arm, nose):
        part.data.materials.append(material)
        part.parent = root
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB')
    print(f'SELFTEST made {path}')


def check(paths):
    previous = None
    for path in paths:
        name = os.path.basename(path)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=path)
        meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        assert len(meshes) == 1, f'{name}: {len(meshes)} objects, expected 1'
        obj = meshes[0]
        assert max(abs(r) for r in obj.rotation_euler) < 1e-6, f'{name}: has a rotation'
        assert max(abs(s - 1) for s in obj.scale) < 1e-6, f'{name}: has a scale'
        co = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
        obj.data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        low, high = co.min(axis=0), co.max(axis=0)
        assert abs(low[2]) < 1e-3, f'{name}: lowest point at {low[2]:.4f}, expected 0'
        assert abs(high[2] - low[2] - 2) < 0.02, f'{name}: {high[2] - low[2]:.4f} m tall, expected 2'
        middle = (low + high) / 2
        assert abs(middle[0]) < 0.02 and abs(middle[1]) < 0.02, f'{name}: not centred'
        sides = [max(image.size) for image in bpy.data.images]
        assert sides and max(sides) <= 512, f'{name}: texture sides {sides}, expected 512 or less'
        triangles = sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
        assert previous is None or triangles < previous, f'{name}: {triangles} triangles, not fewer'
        previous = triangles
        print(f'SELFTEST ok {name}: {triangles} triangles, textures {sides}')


def views(path, folder):
    os.makedirs(folder, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('sky')
    if world.node_tree is None:
        world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1)
    scene.world = world
    points = [o.matrix_world @ Vector(c) for o in scene.objects if o.type == 'MESH' for c in o.bound_box]
    middle = sum(points, Vector()) / len(points)
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    camera.data.type = 'ORTHO'
    camera.data.clip_end = 100
    scene.collection.objects.link(camera)
    scene.camera = camera
    # The front faces -y, so the model's own left side is +x.
    where = {'front': (0, -1, 0), 'left': (1, 0, 0), 'back': (0, 1, 0), 'right': (-1, 0, 0), 'top': (0, 0, 1)}
    sizes = {'front': (300, 400), 'left': (420, 420), 'back': (500, 360), 'right': (360, 480), 'top': (400, 400)}
    shifts = {'front': (0.08, 0.03), 'left': (-0.06, 0), 'back': (0.03, -0.08), 'right': (0, 0.06), 'top': (0.05, 0.05)}
    backdrop = np.array([0.1, 0.7, 0.75], dtype=np.float32)
    for k, (view, direction) in enumerate(where.items()):
        scene.render.resolution_x, scene.render.resolution_y = sizes[view]
        camera.data.ortho_scale = 3.5 + k * 0.4
        # A camera looks along its own -z with its own +y up. Looking down, up is the back (+y).
        back = Vector(direction)
        up = Vector((0, 1, 0)) if view == 'top' else Vector((0, 0, 1))
        right = up.cross(back).normalized()
        camera.rotation_euler = Matrix((right, back.cross(right), back)).transposed().to_euler()
        camera.location = middle + Vector(direction) * 10
        camera.data.shift_x, camera.data.shift_y = shifts[view]
        out = os.path.join(folder, f'{view}.png')
        scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        if view in ('front', 'back', 'top'):                 # these on a plain backdrop
            image = bpy.data.images.load(out, check_existing=False)
            w, h = image.size
            px = np.empty(w * h * 4, dtype=np.float32)
            image.pixels.foreach_get(px)
            px = px.reshape(-1, 4)
            px[:, :3] = px[:, :3] * px[:, 3:] + backdrop * (1 - px[:, 3:])
            px[:, 3] = 1
            image.pixels.foreach_set(px.ravel())
            image.filepath_raw = out
            image.file_format = 'PNG'
            image.save()
        print(f'SELFTEST rendered {out}')


def agreement(path, side, limit, names):
    with open(path) as f:
        report = json.load(f)
    if 'agreement' in report:
        figures = {k: v for k, v in report['agreement'].items() if k in ('front_back', 'left_right')}
    else:
        figures = {k: v['outline_agreement'] for k, v in report['views'].items() if not names or k in names}
    assert figures, f'{path}: no outline agreement to check'
    for name, value in figures.items():
        ok = value > limit if side == 'above' else value < limit
        assert ok, f'{path}: {name} agreement {value}, expected {side} {limit}'
    print(f'SELFTEST ok {os.path.basename(path)}: {figures}')


def baked(path, most, size):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert len(meshes) == 1, f'{path}: {len(meshes)} meshes, expected 1'
    obj = meshes[0]
    count = sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
    assert count <= most, f'{path}: {count} triangles, expected at most {most}'
    shader = next(n for n in obj.active_material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')

    def image_behind(socket):
        stack = [socket]
        while stack:
            for link in stack.pop().links:
                node = link.from_node
                if node.type == 'TEX_IMAGE':
                    return node.image
                stack.extend(i for i in node.inputs if i.is_linked)
        return None

    for name in ('Base Color', 'Normal', 'Roughness', 'Metallic'):
        image = image_behind(shader.inputs[name])
        assert image is not None, f'{path}: no map behind {name}'
        assert tuple(image.size) == (size, size), f'{path}: {name} map is {tuple(image.size)}'
    colour = image_behind(shader.inputs['Base Color'])
    px = np.empty(size * size * 4, dtype=np.float32)
    colour.pixels.foreach_get(px)
    spread = float(px.reshape(-1, 4)[:, :3].std())
    assert spread > 0.05, f'{path}: base colour map is blank (spread {spread:.3f})'
    print(f'SELFTEST ok {os.path.basename(path)}: {count} triangles, maps {size}, colour spread {spread:.2f}')


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    if args[:1] == ['make'] and len(args) == 2:
        make(args[1])
    elif args[:1] == ['check'] and len(args) > 1:
        check(args[1:])
    elif args[:1] == ['views'] and len(args) == 3:
        views(args[1], args[2])
    elif args[:1] == ['baked'] and len(args) == 4:
        baked(args[1], int(args[2]), int(args[3]))
    elif args[:1] == ['agreement'] and len(args) >= 4 and args[2] in ('above', 'below'):
        agreement(args[1], args[2], float(args[3]), args[4:])
    else:
        sys.exit('usage: selftest.py -- make <raw.glb> | check <file.glb>... | views <file.glb> <folder>'
                 ' | agreement <json> above|below <value> [view...] | baked <file.glb> <triangles> <size>')


main()
