"""
Blender side of the self-test that tools/selftest.sh runs.

  blender --background --factory-startup --python-exit-code 1 \
      --python selftest.py -- make raw.glb
  blender --background --factory-startup --python-exit-code 1 \
      --python selftest.py -- check out.glb out-1.glb out-2.glb

"make" writes an awkward model: two textured parts under a parent that is
moved, turned and scaled, with a 2048-texel texture, like a generated file
with stray transforms. "check" fails unless every finished file holds one
object with no rotation or scale, stands 2 m tall with its lowest point at
height 0, is centred, keeps its textures at 512 texels or less, and has fewer
triangles than the file before it.
"""
import os
import sys

import bpy
import numpy as np


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
    for part in (sphere, cube):
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


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    if args[:1] == ['make'] and len(args) == 2:
        make(args[1])
    elif args[:1] == ['check'] and len(args) > 1:
        check(args[1:])
    else:
        sys.exit('usage: selftest.py -- make <raw.glb> | check <file.glb>...')


main()
