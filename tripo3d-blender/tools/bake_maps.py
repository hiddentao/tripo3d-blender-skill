"""
Bakes a detailed model onto a lighter game mesh with no window, so the game mesh keeps the
detailed model's surface detail, colour and materials in texture maps.

  blender --background --factory-startup --python bake_maps.py -- \
      detailed.glb game.glb [--triangles 30000 | --low low.glb] [--size 2048] [--cage 0.01] \
      [--margin 16] [--unwrap]

The detailed model is a finished GLB, such as finish_model.py writes from a Tripo3D run with
geometry_quality=detailed. The game mesh comes from --low (a retopologised mesh in the same place,
such as one from Tripo's smart_low_poly or made by hand), or else from the detailed model cut down
to --triangles. Then it:
  1. lays the game mesh's surface flat for texturing (UV unwrap) when it was cut down here, has no
     UV map, or --unwrap is given; a supplied mesh keeps its own UV map otherwise;
  2. bakes, with Cycles from the detailed model onto the game mesh, a base colour map, a tangent
     normal map, and a roughness and metalness map in glTF's layout (green roughness, blue metal);
  3. gives the game mesh one material that uses the maps and writes game.glb with them inside.
It prints BAKED with the triangle counts, the map size and the file size.

--cage is how far the bake looks out from the game mesh for the detailed surface, as a share of
the model's largest side. Raise it if the normal map has holes or smears; lower it if detail from
another part of the model shows up.
"""
import argparse
import json
import os
import sys

import bmesh
import bpy
import numpy as np

CHANNELS = (('base_colour', 'Base Color', 'sRGB'),
            ('roughness', 'Roughness', 'Non-Color'),
            ('metallic', 'Metallic', 'Non-Color'))


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser(prog='bake_maps.py')
    p.add_argument('src', help='detailed finished GLB')
    p.add_argument('dst', help='game GLB to write')
    p.add_argument('--triangles', type=int, default=30000, help='triangles in the game mesh')
    p.add_argument('--low', default='', help='game mesh GLB to use instead of cutting one down')
    p.add_argument('--size', type=int, default=2048, help='side of each map in texels')
    p.add_argument('--cage', type=float, default=0.01, help='bake reach, as a share of the largest side')
    p.add_argument('--margin', type=int, default=16, help='texels of bleed around each UV island')
    p.add_argument('--unwrap', action='store_true', help='unwrap the game mesh even if it has UVs')
    return p.parse_args(argv)


def triangles(obj):
    return sum(len(poly.vertices) - 2 for poly in obj.data.polygons)


def only_mesh(objects, what):
    meshes = [o for o in objects if o.type == 'MESH']
    if len(meshes) != 1:
        sys.exit(f'bake_maps: {what} holds {len(meshes)} meshes; finish it with finish_model.py first')
    return meshes[0]


def import_one(path, what):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    obj = only_mesh([o for o in bpy.context.scene.objects if o not in before], what)
    # A GLB stores each texture seam as separate vertices. Unmerged, cutting the mesh down
    # tears it apart along every seam. The importer's merge_vertices option does not join them.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def select(active, *others):
    bpy.ops.object.select_all(action='DESELECT')
    for o in (active,) + others:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def cut_down(high, target):
    low = high.copy()
    low.data = high.data.copy()
    low.name = low.data.name = 'game'
    bpy.context.collection.objects.link(low)
    mod = low.modifiers.new('decimate', 'DECIMATE')
    mod.ratio = min(1.0, target / max(1, triangles(high)))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    low.data = bpy.data.meshes.new_from_object(low.evaluated_get(depsgraph))
    low.modifiers.clear()
    return low


def unwrap(low):
    while low.data.uv_layers:
        low.data.uv_layers.remove(low.data.uv_layers[0])
    low.data.uv_layers.new(name='UVMap')
    select(low)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')


def target_material(low, size):
    material = bpy.data.materials.new('baked')
    if material.node_tree is None:
        material.use_nodes = True
    low.data.materials.clear()
    low.data.materials.append(material)
    nodes = material.node_tree.nodes
    images = {}
    for name, _, space in CHANNELS + (('normal', None, 'Non-Color'),):
        image = bpy.data.images.new(name, size, size, alpha=False)
        image.colorspace_settings.name = space
        node = nodes.new('ShaderNodeTexImage')
        node.image = image
        images[name] = (image, node)
    return material, images


def emit(materials, socket):
    """Sends one Principled input of every material straight to its output, for an emission bake."""
    undo = []
    for material in materials:
        tree = material.node_tree
        out = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
        shader = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        node = tree.nodes.new('ShaderNodeEmission')
        source = shader.inputs[socket] if shader else None
        if source is not None and source.links:
            tree.links.new(source.links[0].from_socket, node.inputs['Color'])
        elif source is not None:
            value = source.default_value
            node.inputs['Color'].default_value = (tuple(value)[:3] + (1,)) if hasattr(value, '__len__') \
                else (value, value, value, 1)
        before = out.inputs['Surface'].links[0].from_socket if out.inputs['Surface'].links else None
        tree.links.new(node.outputs['Emission'], out.inputs['Surface'])
        undo.append((tree, node, out, before))
    return undo


def restore(undo):
    for tree, node, out, before in undo:
        tree.nodes.remove(node)
        if before is not None:
            tree.links.new(before, out.inputs['Surface'])


def pixels(image):
    px = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    return px.reshape(-1, 4)


def wire(material, images, size):
    """Builds the game material: glTF reads metal and roughness from one map, green and blue."""
    tree = material.node_tree
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    combined = bpy.data.images.new('metal_rough', size, size, alpha=False)
    combined.colorspace_settings.name = 'Non-Color'
    px = np.ones((size * size, 4), dtype=np.float32)
    px[:, 1] = pixels(images['roughness'][0])[:, 0]
    px[:, 2] = pixels(images['metallic'][0])[:, 0]
    combined.pixels.foreach_set(px.ravel())
    combined.pack()
    for name in ('roughness', 'metallic'):
        image, node = images.pop(name)
        tree.nodes.remove(node)
        bpy.data.images.remove(image)
    mr = tree.nodes.new('ShaderNodeTexImage')
    mr.image = combined
    split = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(mr.outputs['Color'], split.inputs['Color'])
    tree.links.new(split.outputs['Green'], shader.inputs['Roughness'])
    tree.links.new(split.outputs['Blue'], shader.inputs['Metallic'])
    tree.links.new(images['base_colour'][1].outputs['Color'], shader.inputs['Base Color'])
    bump = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(images['normal'][1].outputs['Color'], bump.inputs['Color'])
    tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])


def main():
    a = parse()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    high = import_one(a.src, 'the detailed model')
    high.name = 'detailed'
    if a.low:
        low = import_one(a.low, 'the game mesh')
        low.name = 'game'
        needs_unwrap = a.unwrap or not low.data.uv_layers
    else:
        low = cut_down(high, a.triangles)
        needs_unwrap = True
    if needs_unwrap:
        unwrap(low)

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 4
    bake = scene.render.bake
    bake.use_selected_to_active = True
    bake.cage_extrusion = a.cage * max(high.dimensions)
    bake.margin = a.margin

    material, images = target_material(low, a.size)
    sources = [m for m in high.data.materials if m is not None and m.node_tree is not None]
    select(low, high)
    for name, socket, _ in CHANNELS:
        image, node = images[name]
        material.node_tree.nodes.active = node
        undo = emit(sources, socket)
        bpy.ops.object.bake(type='EMIT')
        restore(undo)
        image.pack()
    image, node = images['normal']
    material.node_tree.nodes.active = node
    bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT')
    image.pack()
    wire(material, images, a.size)

    select(low)
    bpy.ops.export_scene.gltf(filepath=a.dst, export_format='GLB', use_selection=True)
    print('BAKED ' + json.dumps({
        'detailed_triangles': triangles(high),
        'game_triangles': triangles(low),
        'unwrapped': needs_unwrap,
        'map_size': a.size,
        'file': a.dst,
        'bytes': os.path.getsize(a.dst),
    }))


main()
