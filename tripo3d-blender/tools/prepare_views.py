"""
Prepares the reference pictures for a Tripo3D run with no window, so every view shows the object
at one scale, on one ground line, centred on a square canvas, against one plain backdrop or none,
and measures them before any credits are spent.

  blender --background --factory-startup --python prepare_views.py -- \
      pictures/ views/ [--size 1024] [--fill 0.85] [--backdrop 1,1,1 | --alpha] [--tolerance 0.1]

Reads the pictures named after a view (front, left, back, right or top; PNG, JPG or WebP) from the
first folder. For each it finds the object, from the picture's transparency or else by how far each
pixel's colour is from the backdrop colour at the picture's border. Then:
  1. The four side views get one scale, so the object is as many pixels tall in each, and one
     ground line. The top view gets the front view's scale, or fits the canvas alone.
  2. Each object is centred across the canvas and set on a plain backdrop, or on a transparent one
     with --alpha. Edge pixels lose the old backdrop's colour.
  3. It writes views/<view>.png, views/check/<view>.png (the object on magenta, which shows any
     shadow or backdrop left in it) and views/views.json.
  4. It prints PREPARED with the measurements: each object's size and width-to-height ratio,
     its colour, how well opposite views agree in outline, and warnings.

Opposite views of one object have mirrored outlines, front and back, left and right, when the
camera is level and far away. A low agreement means the views show two different objects.
"""
import argparse
import json
import os
import struct
import sys
import zlib

import bpy
import numpy as np

VIEWS = ('front', 'left', 'back', 'right', 'top')
SIDES = VIEWS[:4]
PICTURES = ('.png', '.jpg', '.jpeg', '.webp')


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser(prog='prepare_views.py')
    p.add_argument('src', help='folder with front.png, left.png, back.png, right.png, top.png')
    p.add_argument('dst', help='folder to write the prepared views into')
    p.add_argument('--size', type=int, default=1024, help='side of the square canvas in pixels')
    p.add_argument('--fill', type=float, default=0.85, help='share of the canvas the object may fill')
    p.add_argument('--backdrop', default='1,1,1', help='plain backdrop colour as R,G,B from 0 to 1')
    p.add_argument('--alpha', action='store_true', help='write a transparent backdrop instead')
    p.add_argument('--tolerance', type=float, default=0.1,
                   help='colour difference from the backdrop that counts as object, 0 to 1')
    return p.parse_args(argv)


def load(path):
    image = bpy.data.images.load(path, check_existing=False)
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    bpy.data.images.remove(image)
    return px.reshape(h, w, 4)[::-1].copy()              # rows from the top down


def write_png(path, px):
    # Blender's own save applies colour management; this writes the values as they are.
    data = np.clip(np.round(px * 255), 0, 255).astype(np.uint8)
    h, w, c = data.shape
    rows = np.concatenate([np.zeros((h, 1), np.uint8), data.reshape(h, w * c)], axis=1)

    def chunk(kind, body):
        return (struct.pack('>I', len(body)) + kind + body
                + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff))

    header = struct.pack('>IIBBBBB', w, h, 8, 6 if c == 4 else 2, 0, 0, 0)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header)
                + chunk(b'IDAT', zlib.compress(rows.tobytes(), 6)) + chunk(b'IEND', b''))


def resample(px, w, h):
    image = bpy.data.images.new('resample', px.shape[1], px.shape[0], alpha=True, float_buffer=True)
    image.pixels.foreach_set(px[::-1].ravel())
    image.scale(w, h)
    out = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(out)
    bpy.data.images.remove(image)
    return out.reshape(h, w, 4)[::-1]


def border(a, band):
    return np.concatenate([a[:band].reshape(-1, *a.shape[2:]), a[-band:].reshape(-1, *a.shape[2:]),
                           a[:, :band].reshape(-1, *a.shape[2:]), a[:, -band:].reshape(-1, *a.shape[2:])])


def despeck(solid):
    # Keeps pixels with at least two solid neighbours: a one-pixel wire stays, a lone speck goes.
    padded = np.pad(solid, 1).astype(np.int8)
    h, w = solid.shape
    near = sum(padded[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
               for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return solid & (near >= 2)


def find_object(px, tolerance):
    """Returns the object's cover (0 to 1 per pixel), the backdrop colour or None, and warnings."""
    warnings = []
    band = max(2, round(min(px.shape[:2]) * 0.02))
    if (px[..., 3] < 0.5).mean() > 0.01:
        cover, backdrop = np.clip(px[..., 3], 0, 1), None
    else:
        edge = border(px[..., :3], band)
        backdrop = np.median(edge, axis=0)
        if np.percentile(np.abs(edge - backdrop).max(axis=1), 90) > tolerance / 2:
            warnings.append('the backdrop is not one plain colour')
        far = np.abs(px[..., :3] - backdrop).max(axis=2)
        cover = np.clip((far - tolerance / 2) / (tolerance / 2), 0, 1)
        solid = cover >= 0.5
        if solid.any() and np.median(far[solid]) < 2 * tolerance:
            warnings.append('much of the object is close to the backdrop colour')
    solid = despeck(cover >= 0.5)
    if border(solid, band).mean() > 0.001:
        warnings.append('the object touches the edge of the picture')
    return cover, backdrop, solid, warnings


def bounds(solid):
    rows = np.nonzero(solid.any(axis=1))[0]
    cols = np.nonzero(solid.any(axis=0))[0]
    if not len(rows):
        return None
    return int(cols[0]), int(cols[-1]) + 1, int(rows[0]), int(rows[-1]) + 1


def hsv(rgb):
    top, low = rgb.max(axis=1), rgb.min(axis=1)
    span = np.maximum(top - low, 1e-6)
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    hue = np.where(top == r, (g - b) / span % 6, np.where(top == g, (b - r) / span + 2, (r - g) / span + 4))
    return hue * 60, np.where(top > 0, (top - low) / np.maximum(top, 1e-6), 0), top


def colour(rgb):
    """Hue, colour strength and lightness of the pixels (middle values), and the spread of lightness."""
    if not len(rgb):
        return None
    hue, sat, val = hsv(rgb)
    angle = np.radians(hue)
    weight = sat + 1e-6                                   # grey pixels have no real hue
    mean = np.degrees(np.arctan2((np.sin(angle) * weight).sum(), (np.cos(angle) * weight).sum())) % 360
    q1, q3 = np.percentile(val, [25, 75])
    strength = float(np.median(sat))
    return {'hue': round(float(mean)) if strength >= 0.05 else None,   # a grey has no hue
            'strength': round(strength, 3),
            'lightness': round(float(np.median(val)), 3), 'lightness_spread': round(float(q3 - q1), 3)}


def overlap(a, b):
    union = (a | b).sum()
    return round(float((a & b).sum() / union), 3) if union else None


def main():
    a = parse()
    backdrop_out = np.array([float(v) for v in a.backdrop.split(',')], dtype=np.float32)
    os.makedirs(os.path.join(a.dst, 'check'), exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    found = {}
    for name in sorted(os.listdir(a.src)):
        stem, ext = os.path.splitext(name)
        if ext.lower() in PICTURES and stem.lower() in VIEWS:
            found[stem.lower()] = os.path.join(a.src, name)
    if not found:
        sys.exit('prepare_views: no picture named front, left, back, right or top in ' + a.src)

    views = {}
    for view in VIEWS:
        if view not in found:
            continue
        px = load(found[view])
        cover, backdrop, solid, warnings = find_object(px, a.tolerance)
        box = bounds(solid)
        if box is None:
            sys.exit(f'prepare_views: found no object in {found[view]}')
        views[view] = dict(px=px, cover=cover, backdrop=backdrop, box=box, warnings=warnings)

    room = a.fill * a.size
    sides = [v for v in SIDES if v in views]
    ratios = [(views[v]['box'][3] - views[v]['box'][2]) / (views[v]['box'][1] - views[v]['box'][0])
              for v in sides]
    tall = room * min([1.0] + ratios)                   # the widest side view still fits
    foot = round((a.size + tall) / 2)
    for view, v in views.items():
        x0, x1, y0, y1 = v['box']
        if view in SIDES:
            v['scale'] = tall / (y1 - y0)
        elif 'front' in views:
            fx0, fx1 = views['front']['box'][:2]
            v['scale'] = min((fx1 - fx0) * views['front']['scale'] / (x1 - x0),
                             room / (x1 - x0), room / (y1 - y0))
        else:
            v['scale'] = room / max(x1 - x0, y1 - y0)

    report = {'size': a.size, 'fill': a.fill, 'object_height_px': round(tall, 1), 'foot_row': foot,
              'backdrop': None if a.alpha else [round(float(c), 3) for c in backdrop_out],
              'tolerance': a.tolerance, 'top_scale': 'front' if 'front' in views else 'alone',
              'views': {}, 'agreement': {}}
    masks = {}
    for view, v in views.items():
        px, cover, x0, x1, y0, y1, s = v['px'], v['cover'], *v['box'], v['scale']
        pad = 2
        cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
        cx1, cy1 = min(px.shape[1], x1 + pad), min(px.shape[0], y1 + pad)
        crop = px[cy0:cy1, cx0:cx1]
        alpha = cover[cy0:cy1, cx0:cx1, None]
        if v['backdrop'] is None:
            colour_part = crop[..., :3] * alpha
        else:                                           # take the old backdrop out of edge pixels
            colour_part = np.clip(crop[..., :3] - (1 - alpha) * v['backdrop'], 0, None)
        piece = np.concatenate([colour_part, alpha], axis=2).astype(np.float32)
        w, h = max(1, round((cx1 - cx0) * s)), max(1, round((cy1 - cy0) * s))
        piece = resample(piece, w, h)
        left = round(a.size / 2 - ((x0 + x1) / 2 - cx0) * s)
        top = round(foot - (y1 - cy0) * s) if view in SIDES else round(a.size / 2 - ((y0 + y1) / 2 - cy0) * s)
        canvas = np.zeros((a.size, a.size, 4), dtype=np.float32)
        px0, py0 = max(0, left), max(0, top)
        px1, py1 = min(a.size, left + w), min(a.size, top + h)
        if px1 <= px0 or py1 <= py0:
            sys.exit(f'prepare_views: the {view} view does not fit the canvas')
        canvas[py0:py1, px0:px1] = piece[py0 - top:py1 - top, px0 - left:px1 - left]
        if px0 > left or py0 > top or px1 < left + w or py1 < top + h:
            v['warnings'].append('the object was cut by the canvas; lower --fill')
        cover_out = np.clip(canvas[..., 3:], 0, 1)
        straight = np.where(cover_out > 1e-4, canvas[..., :3] / np.maximum(cover_out, 1e-4), 0)
        straight = np.clip(straight, 0, 1)
        if a.alpha:
            out = np.concatenate([straight, cover_out], axis=2)
        else:
            out = straight * cover_out + backdrop_out * (1 - cover_out)
        write_png(os.path.join(a.dst, f'{view}.png'), out)
        magenta = np.array([1, 0, 1], dtype=np.float32)
        write_png(os.path.join(a.dst, 'check', f'{view}.png'), straight * cover_out + magenta * (1 - cover_out))
        solid = cover_out[..., 0] >= 0.5
        masks[view] = solid
        if s > 1.05:
            v['warnings'].append(f'enlarged {s:.2f} times; make the picture larger')
        report['views'][view] = {
            'file': found[view],
            'object_px': [x1 - x0, y1 - y0],
            'width_to_height': round((x1 - x0) / (y1 - y0), 3),
            'scale': round(s, 3),
            'colour': colour(straight[cover_out[..., 0] > 0.9]),
            'warnings': v['warnings'],
        }

    for first, second in (('front', 'back'), ('left', 'right')):
        if first in masks and second in masks:
            report['agreement'][f'{first}_{second}'] = overlap(masks[first], masks[second][:, ::-1])
    if 'top' in views and 'left' in views:
        top_box, left_box = bounds(masks['top']), bounds(masks['left'])
        report['agreement']['top_depth_to_left_width'] = round(
            (top_box[3] - top_box[2]) / (left_box[1] - left_box[0]), 3)

    with open(os.path.join(a.dst, 'views.json'), 'w') as f:
        json.dump(report, f, indent=2)
    print('PREPARED ' + json.dumps(report))


if __name__ == '__main__':
    main()
