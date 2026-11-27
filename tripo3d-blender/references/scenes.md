# Scenes and environments

Tripo3D makes one object per run, as one closed mesh with one texture. A
scene concept, such as a furnished room, a street or a cliff path, holds
dozens of objects, large flat surfaces and repeated parts. Break the scene
into items, make each item as a model of its own, and put the scene back
together in Blender or in the engine.

A separate run for each item gives better models than one run for a group.
Each item then fills its own pictures, gets the whole face budget, and keeps
its own materials. Group items only when the rules below allow it. And not
every item needs a model at all: items that the player never comes near can
stay as pictures in the background.

## Ask about the scene

Not every item in a scene needs a model. The player cares about what they
use and what they walk past; the rest is background. Before you list the
items, ask the human four questions about the scene:

1. Where can the player go: walk around inside it, see it only from fixed
   views, or pass it at a distance?
2. What can the player touch, use, move or collide with here?
3. How close does the camera come to the walls and the furniture?
4. What is the scene's budget: triangles, texture memory, or the slowest
   device it must run on?

With these answers you can propose a tier for every item, and the human only
corrects the exceptions. Do not ask about each item in turn.

## Sort the items into tiers

List every item in the scene concept, with how many there are and where they
stand. Give each one a tier and a one-line reason:

| Tier | Items | How it is made |
| --- | --- | --- |
| Interactive | What the player uses, moves or collides with: the pool table, the balls, the cues, a door that opens | Its own run at the AAA tier (see [concept](concept.md#quality-tiers)), baked onto a game mesh, with its moving parts as separate items and a collision shape |
| Set dressing | Still items that the camera passes close to and sees from more than one side: chairs, a display cabinet, an oar rack, a canoe overhead | One run each at the standard tier, placed as copies where it repeats, with a simple collision shape or none |
| Background | Items seen from one side or from far away: ropes and buoys hung on a wall, framed pictures, trophies behind glass | No run. A flat card with the item's picture on it, or relief painted into the wall's texture and normal map. A far item that needs real depth gets one run at the distant-prop tier |
| Backdrop | The view beyond the playable space: the sea, the boats, the sky | One wide picture on a backdrop plane or as a sky map |

Four tests decide the tier. Does the player interact with it? Does it move?
Is it seen close up, or from more than one side? Does it repeat? An item that
fails all four is background. When an item is unclear, put it in the
background. Moving it up a tier later costs one run. Making every item a
model spends credits, and the scene's triangle and texture budget, on things
that no one looks at.

Show the human the whole table, with the tiers and the reasons, and let them
move items between tiers. Spend nothing until they confirm it.

## Choose how each item is made

Some items need a route other than a Tripo3D run, whatever their tier:

| What the item is | Route |
| --- | --- |
| An item that repeats: chairs, oars, trophies, buoys, barrels | One run, placed many times. Two designs, such as a low chair and a bar stool, are two items |
| A simple shape: a ball, a plain plank, a pipe | Model it in Blender. A run costs credits for a shape that takes a minute to build |
| The shell: walls, floor, ceiling, beams, door frames | Build in Blender with tiling materials. Tripo3D gives a closed object with one texture that does not repeat, and a wall needs exact sizes and a texture that does |
| A part only a few pixels thick against the item it belongs to: rope, chains, cables, rigging, a hanging lamp's rod | Build in Blender. A coiled rope or a bundle that forms a solid mass can be a run |
| Glass, water, flames and lights: lamp glass, a glass dome, the glass of a cabinet door, a harbour | Build in Blender or in the engine. In the pictures, show glass as an opaque stand-in or leave it out |
| Text and logos: signs, labels, framed certificates | A plain shape from Tripo3D, with the text added as a decal in Blender or the engine |

Group items into one run only when all of these hold: they touch, they never
move apart, they share a material, they are small, and they always appear
together. A trophy fixed to its plinth is one item. Three loose trophies on
a shelf are three items, or one item placed three times. The table and the
balls on it are separate items, because the balls move.

Write the inventory into the scene's spec, one row for each item, before
any picture is made:

| Item | Count | Tier | Size (m) | Route | Notes |
| --- | --- | --- | --- | --- | --- |
| Pool table | 1 | Interactive | 2.1 x 1.2 x 0.8 | Own run | Cloth dark teal; coin slot on the long side |
| Pool balls | 16 | Interactive | about 0.05 across | Blender spheres | |
| Tall chair | 2 | Set dressing | 1.0 tall | One run, placed twice | Back legs hidden in the concept: invented |
| Oar | 12 | Set dressing | 2.4 long | One run, placed 12 times | Rack built in Blender |
| Rope coil on the wall | 3 | Background | 0.4 across | Card from the item's picture | Seen from the front only |
| Harbour view | 1 | Backdrop | | Wide picture beyond the door | |
| Stone wall | 4 | Shell | from the floor plan | Blender, tiling material | |

The rows here are an example. Every tier is the human's to confirm, every
size comes from the human or from the measuring below, and the human
confirms the inventory before you spend anything on it.

### Cards and backdrops

A background card is a flat plane that shows the item's picture, with a
transparent background, placed where the item stands. Make the picture as in
[Draw each item on its own](#draw-each-item-on-its-own), facing the camera,
name it `front.png`, and cut it out with `prepare_views.py --alpha`. A card
looks right only from the front, so use it for items that the camera sees
from one side.
null3d's asset tool can also turn a finished model into cards for its
impostors add-on (`assets impostor`), for far copies of a model that has one;
see null3d's documentation.

A backdrop is one wide picture of the view beyond the playable space. Ask an
image model to extend the concept's view outside into a wide picture with
nothing in front of it, and place it on a plane beyond the openings, or use
it as a sky map. It shows no change of angle as the camera moves, so keep it
for what is far away.

## Measure each item

A scene concept gives few sizes, so measure from objects whose size is
known: a door is about 2 m tall, a seat about 0.45 m high, a stair step
about 0.18 m. Compare items that stand at about the same distance from the
camera, because perspective shrinks the far ones. Write each size into the
inventory and ask the human to confirm the sizes that matter, such as a
table that must fit the room.

## Draw each item on its own

Each item that gets a run needs its own concept: the item alone, whole, in
the scene's design. Make it from the scene picture:

1. Crop the item from the scene, with some margin. The crop is a reference
   for you and the reviewer. It is not an input for Tripo3D.
2. Give an image model the whole scene and the crop, and ask for the item
   alone (the prompt is below). The result is the item's concept, and the
   human accepts it as in [concept](concept.md#accepting-the-concept).
3. Make the item's views from that concept, as in
   [pictures](pictures.md).

A prompt for drawing an item out of a scene. It passed in a test on
2026-11-27 with a games room picture, for a pool table and a tall chair:

```text
Image 1 is a scene. Image 2 is a close crop of one item in it: the <item>
that stands <where it is in the picture, for example: at the right of the
picture, beside the trophy niche>. Draw only that item, alone and whole, as
a product photograph for a 3D model reference: three-quarter view from a
little above, the whole item in frame with space around it. Keep its design
exactly as in images 1 and 2: <every distinctive part in words, for example:
its legs are SQUARE in section, straight and slightly tapered, not turned,
not round; a long slot is cut through the middle of the top rail>. <The
material and its colour in words, for example: the whole chair is light
honey-coloured pine with a clear varnish, the same light wood as the pool
table in image 1, not a dark brown.> Complete the parts that image 1 hides,
such as <the back legs>, in the same style. Leave out everything else: no
wall, floor or other object, <no balls, and no cloth draped over the end>.
Plain light grey background, soft, even, neutral white light, no coloured
light from the scene, no cast shadow. No text.
```

The first drawings in that test named the parts in general terms only, and
both failed. The model gave the table turned, round legs where the scene has
square ones, made its dark teal cloth grass green, made the honey-coloured
chair dark brown, and dropped the slot in the chair's top rail. With each
distinctive part and each colour named in words, as above, both passed. An
image model puts the common version of a part in place of an unusual one,
and when it takes out the scene's light it guesses the material colour, so
say both.

Rules for this step:

- **Take out the scene's light.** Lamp light, dusk or coloured light in the
  scene shifts every colour. Ask for neutral white light, and judge the
  item's colour as the colour of its material, not as it looks in the lit
  scene.
- **Mark what was invented.** Parts that the scene hides, such as the far
  side of a cabinet or legs behind a table, are invented in this step. List
  them in the item's checklist, and have the human accept them.
- **Small items invent detail.** An item that is only a few dozen pixels
  tall in the scene shows almost no detail, and the drawing invents it.
  Accept that, or ask the human for a close design of the item.
- **One style for every item.** Give the whole scene with each drawing, not
  only the crop, so that wear and colour stay the same across items.
- **Straighten the item.** The scene shows each item at an angle and in
  perspective. The drawing shows it upright and whole. Check its
  proportions against the sizes in the inventory, not against the
  perspective picture.
- **Leave out what Blender builds.** Chains, ropes, glass and lamp rods stay
  out of the item's pictures, as the inventory says.

## Put the scene back together

1. Finish each item with `finish_model.py`, at the height from the
   inventory and with its front to -y.
2. Build the shell in Blender: walls, floor and beams as simple meshes at
   the sizes from the inventory, with tiling materials from a material
   library or the project's own. Tripo3D is not the tool for these.
3. Place the items with a layout script that reads the finished files,
   never by hand, so that the scene rebuilds from the raw files. Place a
   repeated item as linked copies that share one mesh: `obj.copy()` without
   copying `obj.data`.
4. Render the scene from a camera placed to match the concept, and give the
   render and the concept side by side to the reviewer.

For a web scene on null3d (see
[blender](blender.md#for-the-web-null3d)), keep each item as its own GLB. The
page loads each file once with `assets.loadGltf(url)` and places copies with
`scene.instantiate(prefab)`, or with `scene.createInstances` for many copies
of one mesh. Large static pieces of the shell, such as a cliff or a whole
building, can keep a detailed mesh with the asset tool's `--clusters`
option.
