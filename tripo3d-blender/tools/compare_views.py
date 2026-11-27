"""
Compares a finished model with the reference views it was made from, with no window, so an agent
can see where the shape differs and by how much before it changes anything.

  blender --background --factory-startup --python compare_views.py -- \
      model.glb views/ out_folder [--size 512]

The views folder is the output of prepare_views.py: front.png, left.png, back.png, right.png,
top.png and views.json. The model is a finished GLB whose front faces -y, as finish_model.py
leaves it. For each view it:
  1. renders the model with an orthographic camera, framed the way prepare_views.py framed the
     picture: the same height in pixels, the same ground line, centred across;
  2. lights it with an even white sky, so the colours are close to an unlit picture;
  3. writes out_folder/<view>.png: the reference, the render, and an overlay in which grey is
     shared, red is in the reference only (missing from the model) and blue is in the model only;
  4. measures how far the outlines agree, and the colour of each.
It prints COMPARED with the figures and writes them to out_folder/compare.json.

"left" is the model's own left side, seen from that side. With the front facing -y, the model's
left is +x, so the left camera stands at +x and looks along -x. The top view looks down, with the
model's front at the bottom of the picture.
"""
import argparse
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prepare_views import colour, load, overlap, resample, write_png  # noqa: E402

# Camera direction (from the model's centre) and turn for each view.
CAMERAS = {
    'front': (Vector((0, -1, 0)), (math.radians(90), 0, 0)),
    'left': (Vector((1, 0, 0)), (math.radians(90), 0, math.radians(90))),
    'back': (Vector((0, 1, 0)), (math.radians(90), 0, math.radians(180))),
    'right': (Vector((-1, 0, 0)), (math.radians(90), 0, math.radians(-90))),
    'top': (Vector((0, 0, 1)), (0, 0, 0)),
}
# The direction that points right in each picture, to centre the camera across.
ACROSS = {'front': Vector((1, 0, 0)), 'left': Vector((0, 1, 0)), 'back': Vector((-1, 0, 0)),
          'right': Vector((0, -1, 0)), 'top': Vector((1, 0, 0))}


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser(prog='compare_views.py')
    p.add_argument('model', help='finished GLB, front facing -y')
    p.add_argument('views', help='folder written by prepare_views.py')
    p.add_argument('out', help='folder for the comparison pictures and compare.json')
    p.add_argument('--size', type=int, default=512, help='side of each picture in pixels')
    return p.parse_args(argv)


def corners():
    return [o.matrix_world @ Vector(c) for o in bpy.context.scene.objects if o.type == 'MESH'
            for c in o.bound_box]


def reference_cover(px, settings):
    if settings['backdrop'] is None:
        return px[..., 3]
    far = np.abs(px[..., :3] - np.array(settings['backdrop'], dtype=np.float32)).max(axis=2)
    t = settings['tolerance']
    return np.clip((far - t / 2) / (t / 2), 0, 1)


def setup_scene(size):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.max_bounces = 2
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('sky')
    if world.node_tree is None:
        world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1)
    scene.world = world
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    camera.data.type = 'ORTHO'
    scene.collection.objects.link(camera)
    scene.camera = camera
    return scene, camera


def main():
    a = parse()
    if not os.path.exists(os.path.join(a.views, 'views.json')):
        sys.exit(f'compare_views: no views.json in {a.views}; prepare the views with prepare_views.py')
    with open(os.path.join(a.views, 'views.json')) as f:
        settings = json.load(f)
    os.makedirs(a.out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a.model)
    points = corners()
    if not points:
        sys.exit('compare_views: the file holds no mesh')
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    tall = high.z - low.z
    if tall <= 0:
        sys.exit('compare_views: the model has no height')
    canvas = settings['size']
    metres_per_px = tall / settings['object_height_px']
    reach = (high - low).length
    scene, camera = setup_scene(a.size)
    camera.data.clip_end = reach * 10

    report = {'model': a.model, 'views': {}}
    for view in ('front', 'left', 'back', 'right', 'top'):
        path = os.path.join(a.views, f'{view}.png')
        if view not in settings['views'] or not os.path.exists(path):
            continue
        direction, turn = CAMERAS[view]
        across = ACROSS[view]
        spread = [p.dot(across) for p in points]
        middle = (low + high) / 2
        centre = middle + across * ((min(spread) + max(spread)) / 2 - middle.dot(across))
        if view == 'top':
            if settings['top_scale'] == 'alone':
                metres = max(high.x - low.x, high.y - low.y) / (settings['fill'] * canvas)
            else:
                metres = metres_per_px
            camera.data.ortho_scale = metres * canvas
            centre.y = middle.y
        else:
            camera.data.ortho_scale = metres_per_px * canvas
            centre.z = low.z + (settings['foot_row'] - canvas / 2) * metres_per_px
        camera.location = centre + direction * reach * 3
        camera.rotation_euler = turn
        render_path = os.path.join(a.out, f'render-{view}.png')
        scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)
        model_px = load(render_path)
        os.remove(render_path)

        ref_px = load(path)
        ref_cover = reference_cover(ref_px, settings)
        ref_px = np.concatenate([ref_px[..., :3] * ref_cover[..., None], ref_cover[..., None]], axis=2)
        if ref_px.shape[0] != a.size:
            ref_px = resample(ref_px.astype(np.float32), a.size, a.size)
        ref_cover = np.clip(ref_px[..., 3], 0, 1)
        ref_rgb = np.clip(ref_px[..., :3] / np.maximum(ref_cover[..., None], 1e-4), 0, 1)
        ref, mod = ref_cover >= 0.5, model_px[..., 3] >= 0.5

        white = np.ones(3, dtype=np.float32)
        left_pic = ref_rgb * ref_cover[..., None] + white * (1 - ref_cover[..., None])
        mid_pic = model_px[..., :3] * model_px[..., 3:] + white * (1 - model_px[..., 3:])
        right_pic = np.ones((a.size, a.size, 3), dtype=np.float32)
        right_pic[ref & mod] = (0.6, 0.6, 0.6)
        right_pic[ref & ~mod] = (0.9, 0.15, 0.15)
        right_pic[mod & ~ref] = (0.15, 0.35, 0.9)
        write_png(os.path.join(a.out, f'{view}.png'), np.concatenate([left_pic, mid_pic, right_pic], axis=1))

        ref_area, mod_area = int(ref.sum()), int(mod.sum())
        cols_r, cols_m = np.nonzero(ref.any(axis=0))[0], np.nonzero(mod.any(axis=0))[0]
        rows_r, rows_m = np.nonzero(ref.any(axis=1))[0], np.nonzero(mod.any(axis=1))[0]
        report['views'][view] = {
            'outline_agreement': overlap(ref, mod),
            'missing_from_model': round((ref & ~mod).sum() / max(ref_area, 1), 3),
            'extra_in_model': round((mod & ~ref).sum() / max(mod_area, 1), 3),
            'width_model_to_reference': round((np.ptp(cols_m) + 1) / (np.ptp(cols_r) + 1), 3)
            if len(cols_r) and len(cols_m) else None,
            'height_model_to_reference': round((np.ptp(rows_m) + 1) / (np.ptp(rows_r) + 1), 3)
            if len(rows_r) and len(rows_m) else None,
            'colour_reference': colour(ref_rgb[ref_cover > 0.9]),
            'colour_model': colour(model_px[..., :3][model_px[..., 3] > 0.9]),
        }
        print(f'COMPARE {view}: outline agreement {report["views"][view]["outline_agreement"]}')

    with open(os.path.join(a.out, 'compare.json'), 'w') as f:
        json.dump(report, f, indent=2)
    print('COMPARED ' + json.dumps(report))


main()
