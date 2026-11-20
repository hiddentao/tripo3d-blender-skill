"""
Renders a GLB from the front, the side and above with no window, so an agent can look at a model
before and after each change.

  blender --background --factory-startup --python preview_model.py -- model.glb out_folder [--size 640]

Writes front.png, side.png and top.png into out_folder. The cameras are orthographic and frame the
whole model; a gray sky and one sun light it, and Cycles renders on the CPU, which works headless.
Blender's front view looks along +y, so "front" shows the side of the model that faces -y.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser(prog='preview_model.py')
    p.add_argument('src')
    p.add_argument('out')
    p.add_argument('--size', type=int, default=640)
    return p.parse_args(argv)


def bounds():
    points = [o.matrix_world @ Vector(c) for o in bpy.context.scene.objects if o.type == 'MESH' for c in o.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def main():
    a = parse()
    os.makedirs(a.out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a.src)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.render.resolution_x = scene.render.resolution_y = a.size
    world = bpy.data.worlds.new('sky')
    # A new world has its node tree from Blender 5 on; older versions need the switch.
    if world.node_tree is None:
        world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.57, 0.6, 1)
    scene.world = world
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    scene.collection.objects.link(sun)
    low, high = bounds()
    middle = (low + high) / 2
    reach = max((high - low).length, 1e-3)
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = reach * 1.1
    camera.data.clip_end = reach * 10
    scene.collection.objects.link(camera)
    scene.camera = camera
    views = {
        'front': (Vector((0, -reach * 3, 0)), (math.radians(90), 0, 0)),
        'side': (Vector((reach * 3, 0, 0)), (math.radians(90), 0, math.radians(90))),
        'top': (Vector((0, 0, reach * 3)), (0, 0, 0)),
    }
    for name, (offset, turn) in views.items():
        camera.location = middle + offset
        camera.rotation_euler = turn
        scene.render.filepath = os.path.join(a.out, f'{name}.png')
        bpy.ops.render.render(write_still=True)
        print(f'PREVIEW {scene.render.filepath}')


main()
