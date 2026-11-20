"""
Finishes a raw Tripo3D model in Blender with no window, so a generated GLB becomes a clean,
measured, engine-ready GLB plus coarser copies for levels of detail.

  blender --background --factory-startup --python finish_model.py -- \
      raw.glb out.glb --height 3.2 [--name statue] [--turn 90] [--levels 0.4,0.12] [--texture 1024]

What it does, in order:
  1. Imports the GLB into an empty scene.
  2. Bakes every object's world transform into its vertices, drops parents and empties, and joins
     the meshes into one object, so the result has no hidden rotation or scale.
  3. Merges vertices that sit on top of each other.
  4. Turns the model about the vertical axis by --turn degrees, so its front faces the project's way.
  5. Scales it so it stands --height metres tall, centres it, and puts its lowest point on the ground.
  6. Shrinks every texture whose longer side is over --texture texels.
  7. Makes one decimated copy for each share in --levels.
  8. Writes out.glb, then out-1.glb, out-2.glb ... for the levels, and prints a JSON summary.

It never calls the network, so the same raw file always gives the same output.
"""
import argparse
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser(prog='finish_model.py')
    p.add_argument('src', help='raw GLB from Tripo3D')
    p.add_argument('dst', help='finished GLB to write')
    p.add_argument('--height', type=float, required=True, help='final height in metres')
    p.add_argument('--name', default='model', help='object and mesh name')
    p.add_argument('--turn', type=float, default=0.0, help='degrees about the vertical axis')
    p.add_argument('--levels', default='', help='triangle shares for coarser copies, e.g. 0.4,0.12')
    p.add_argument('--texture', type=int, default=0, help='largest texture side in texels; 0 keeps them')
    return p.parse_args(argv)


def triangles(obj):
    return sum(len(poly.vertices) - 2 for poly in obj.data.polygons)


def positions(mesh):
    co = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', co)
    return co.reshape(-1, 3)


def join_meshes(name):
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        sys.exit('finish_model: the file holds no mesh')
    # World matrices first: clearing a parent changes its children's matrices.
    worlds = [(o, o.matrix_world.copy()) for o in meshes]
    for o, world in worlds:
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(world)
    for o, _ in worlds:
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.data.name = name
    return obj


def merge_close(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(obj.data)
    bm.free()


def stand(obj, height, turn):
    mesh = obj.data
    if turn:
        mesh.transform(Matrix.Rotation(math.radians(turn), 4, 'Z'))
    co = positions(mesh)
    low, high = co.min(axis=0), co.max(axis=0)
    tall = float(high[2] - low[2])
    if tall <= 0:
        sys.exit('finish_model: the model has no height')
    foot = Matrix.Translation((-(low[0] + high[0]) / 2, -(low[1] + high[1]) / 2, -low[2]))
    mesh.transform(Matrix.Scale(height / tall, 4) @ foot)
    mesh.update()


def shrink_textures(limit):
    shrunk = []
    for image in bpy.data.images:
        w, h = image.size
        if limit and max(w, h) > limit:
            k = limit / max(w, h)
            image.scale(max(1, round(w * k)), max(1, round(h * k)))
            shrunk.append(f'{image.name}: {w}x{h} -> {image.size[0]}x{image.size[1]}')
    return shrunk


def coarser_copy(obj, share, index):
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.name = f'{obj.name}-{index}'
    bpy.context.collection.objects.link(copy)
    mod = copy.modifiers.new('decimate', 'DECIMATE')
    mod.ratio = share
    depsgraph = bpy.context.evaluated_depsgraph_get()
    copy.data = bpy.data.meshes.new_from_object(copy.evaluated_get(depsgraph))
    copy.data.name = copy.name
    copy.modifiers.clear()
    return copy


def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True)


def main():
    a = parse()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a.src)
    obj = join_meshes(a.name)
    merge_close(obj)
    stand(obj, a.height, a.turn)
    shrunk = shrink_textures(a.texture)
    shares = [float(s) for s in a.levels.split(',') if s.strip()]
    levels = [coarser_copy(obj, share, k) for k, share in enumerate(shares, 1)]
    base, ext = os.path.splitext(a.dst)
    files = []
    for k, o in enumerate([obj] + levels):
        path = a.dst if k == 0 else f'{base}-{k}{ext}'
        export(o, path)
        files.append({'file': path, 'triangles': triangles(o), 'bytes': os.path.getsize(path)})
    size = obj.dimensions
    print('FINISHED ' + json.dumps({
        'name': a.name,
        'size_m': [round(size.x, 3), round(size.y, 3), round(size.z, 3)],
        'textures_shrunk': shrunk,
        'files': files,
    }))


main()
