# Input pictures

Tripo3D builds the mesh from its input pictures and copies them: shape,
proportions, surface and colour. A fault in a picture comes back in the mesh,
and a new run to fix it costs the credits again. A picture costs little to
make and to check. So make the pictures first, have a separate reviewer try
to fail each one against the target, and pay for a run only on pictures that
passed.

In the project this skill comes from, about 200 candidate pictures gave 24
that passed. Eight models were made from them, one run each, and none has
needed a second run for its shape so far.

## The loop

1. **Fix the target.** The target is the accepted concept from
   [concept](concept.md), or concept art, a photo or a sketch from the
   human. For one item of a larger scene, it is the item's own concept from
   [scenes](scenes.md).
2. **Write a checklist from the target and the spec alone,** before any
   candidate exists. For each part of the object, write what the target
   shows, on which side, and what fails, and mark the parts that fail a
   picture by themselves. Give figures that can be measured: proportions as
   ratios, such as height to width, and the colours of named regions (see
   [Measuring](#measuring)). A checklist written after you have seen
   candidates drifts toward them.
3. **Make candidates** for each view, as in
   [Making the views](#making-the-views).
4. **Prepare and check them yourself** with `prepare_views.py` (see
   [Preparing the views](#preparing-the-views)), and send only the best
   candidate for each view.
5. **Have them reviewed.** A separate reviewer judges each picture against
   the target and the checklist (see [The reviewer](#the-reviewer)). Its
   verdict is pass, pass with points to carry, or fail with the reasons.
6. **Pay only on a pass.** Spend no credits on a picture without a passing
   verdict. While the front fails, spend none on the other views either,
   because they are made from it.
7. **Carry the points.** Write each point the reviewer let through, such as
   a side 8% too deep or stone too light, into the notes for the Blender
   finish. Blender fixes them for free.
8. **Judge the model the same way.** After the run and the finish, render the
   model against the same views with `compare_views.py`, and the same
   reviewer judges the renders against the same target and checklist.

## Making the views

Tripo3D's multiview input has four slots: front, left, back and right (see
[generation](generation.md#inputs)). "Left" is the object's own left side.
In a run on 2026-11-27, the picture sent in the left slot came out on the
model's own left, and the right one on its own right. All the pictures must
show one object.

Make them in this order:

1. **The front,** from the accepted concept. Make two to eight candidates
   and pass one before you make anything else.
2. **The other views,** each from the concept and the passed front, so that
   every view shows the same object.
3. **A view that will not take the right outline,** by flipping its passed
   opposite and editing only the surface (see
   [Flip and edit](#flip-and-edit)).

A three-quarter or top view fits none of the four slots. Tripo's guide says
a top-down view rarely helps. Use these views to judge the model, not as
inputs.

If a view fails and a new one does not pass, run on the views that passed.
The front alone still gives a usable mesh. A wrong side view gives a wrong
one.

### Camera

- Look straight at one face, from level with the middle of the object and
  far away, so that no top and no other side shows. Tripo's own tool
  descriptions call its multiview input "orthographic views".
- Say in the prompt which way the object faces in the picture. In the left
  view, the front faces the left edge of the picture. In the right view, it
  faces the right edge. In the back view, the object's own left side is on
  the left of the picture.
- Give the object the same height in every side view, on the same ground
  line. `prepare_views.py` does this for you, but only for pictures that
  show one object of one shape.

### Prompts

These prompts passed in a test on 2026-11-27. Image 1 is the accepted
concept and image 2 is the passed front.

The front:

```text
Image 1 is the approved design of a supply crate. Draw the same crate from
directly in front, as an orthographic front elevation for a 3D model
reference sheet: the camera is level with the middle of the crate and far
away, with no perspective, so the top and the sides do not show at all.
Show the front face: the recessed control panel with the small dark screen
and the red latch handle, the black rubber corner bumpers, the chipped
olive-drab paint, exactly as in image 1. The front face is 1.0 m wide and
0.75 m tall: width to height exactly 4 to 3. The whole crate centred,
filling about 80% of the picture width, with space on every side. Plain
pure white background. Soft, even, diffuse light from all sides, no cast
shadow, no strong highlights, no reflections. Keep every material, colour
and wear mark the same as image 1. No text.
```

A side:

```text
Image 1 is the approved design of a supply crate. Image 2 is its approved
front view. Draw the same crate seen from its own LEFT side, as an
orthographic side elevation for a 3D model reference sheet: the camera is
level with the middle of the crate and far away, with no perspective, so
only this one side face shows. In this picture the crate's front faces the
LEFT edge of the picture and its back faces the right edge. This side face
shows the blue-grey panel with the coiled black cable hanging on a steel
hook, as in image 1. The side face is 0.7 m deep and 0.75 m tall, and the
crate is exactly as tall here as in image 2. [Background, light and "keep
every material" lines as for the front.]
```

### Flip and edit

Seen straight on from far away, the outline of the back is the outline of
the front, flipped left to right, and the outline of the right side is the
outline of the left side, flipped. Image models often draw a side view as
wide as the front. In the test, two fresh right views failed that way: the
left and right outlines agreed at 0.73 and 0.67. So:

1. flip the passed opposite view left to right;
2. give the flipped picture to the image model as the only input, and ask it
   to change the surface and nothing else.

```text
Edit this picture of a supply crate. Keep its outline, its size and
position in the picture, the olive-drab frame, the black rubber corner
bumpers, the bolts, the antenna mast, the camera and the soft even light
exactly as they are. Change only the recessed panel in the middle of the
face: remove the small screen and the red latch, and fill the whole recessed
panel with vertical ribbed heat-sink fins of dark weathered steel.
```

The right view made this way agreed with the left at 0.985, and the back with
the front at 0.973. Give only the one picture to edit. When the test added a
second whole picture as a style example, the model copied the second picture
and ignored the edit. The cost of this method is that wear marks near the
edges repeat, mirrored, on the opposite side; the reviewer judges whether
that shows.

### Background

- Use one plain colour behind the object in every view: white or a light
  grey, far from the object's own colours. Tripo's guide asks for plain
  white or grey and warns that a gradient or a reflective backdrop bleeds
  colour into the texture. A light-coloured object needs a mid grey.
- A transparent PNG works too. `prepare_views.py` writes a plain backdrop by
  default (`--backdrop`), or a transparent one with `--alpha`. The test on
  2026-11-27 used plain white.
- When an image model will not give a plain backdrop, cut the object out
  with a background-removal model, such as BiRefNet or Bria RMBG 2.0 (both on
  fal.ai, under USD 0.02 a picture on 2026-11-27). Those models can lose thin
  parts and leave a halo on soft edges, so look at the check pictures that
  `prepare_views.py` writes.

### Light

- **For the inputs,** soft, even, white light from all sides, no cast shadow,
  no strong highlight, no reflection, and the same light in every view. Keep
  some soft shading: a study of image-to-3D models found that they do worse
  on flat-coloured pictures such as hand drawings. Generate with
  `delight=true` to remove the light that remains (see
  [generation](generation.md#parameters)).
- **For the review only,** other lighting shows other faults. A clay render
  (one mid-grey material) shows the shape without colour. A low raking light
  from one side shows surface relief such as panel lines and dents. A render
  in the scene's own light shows how the material reads. Make these from the
  passed views with an edit, and never send them to Tripo3D, because every
  input view must share one light. No vendor documents these variants; they
  are review aids.

### Size and framing

- Make each view at 2048 pixels for an AAA model, and never under 1024.
  Tripo's guide asks for 1024 x 1024 or more and says that under about 512
  there is not enough information.
- Let the object fill 70% to 90% of the frame, with nothing touching the
  edge. `prepare_views.py` fills 85% by default (`--fill`).
- Do not enlarge a small picture to reach the size; make it again larger.
  `prepare_views.py` warns when it enlarges a picture by more than 5%.

### Thin parts

Paint parts that are only a few pixels thick out of every view before you
prepare them, and build them in Blender (see
[blender](blender.md#fixes-as-code)). Tripo3D turns them into blobs, and they
also upset the scale between views. In the test, an antenna drawn longer in
the side views than in the front made the side views' crate 5.8% smaller
after preparing, because the script scales each view by its total height.
With the antenna painted out by a fill of the backdrop colour above the
crate, the views agreed at 0.975 and 0.992.

## Kinds of model

### Characters and creatures

- Pose: Tripo's guide suggests an A-pose (arms angled down) when cloth
  matters and a T-pose (arms straight out) when rigging comes first. Keep
  the pose symmetric, the mouth closed, the hands open with the fingers
  apart, and the feet apart.
- Leave out held props, such as a sword or a bag. Make them as separate
  items, so that they can move.
- Hair as a mass, not strands; fur as a surface, not tufts.
- Faces and hands drift most between views. Check that the face, the hair
  line and every finger count match the front in each view.
- Tripo's `t_pose` template turns a figure into a T-pose:
  `tripo generate image-to-image hero.png -p template=t_pose`.

### Props and hard-surface objects

- Check ratios against the spec in every view: width to height on the front,
  depth to height on the sides.
- Name each panel, handle and vent by where it sits in the picture.
- Leave small text, labels and logos out, and add them as decals in Blender
  or the engine. Image models often draw small text badly, and the texture
  copies what they draw.
- Tripo's guide says to use an opaque stand-in for chrome and glass. A
  mirror finish in a picture shows reflections, and the texture copies
  them.

### Buildings and set pieces

- One module for each run: a wall section, a door frame, a stair. Give its
  footprint and its door and floor heights in the spec, and check them in
  the views.
- Show it on a flat base, standing level.
- Long plain walls, floors and roofs are better as simple meshes with tiling
  materials in Blender (see [scenes](scenes.md#make-an-inventory)).

### Rocks, trees and statues

- Put the weathering, moss and stains in the pictures. The mesh copies them.
- For a tree, make pictures of the bare trunk and limbs, and build the
  leaves in Blender.
- A rock or a statue often has no clear front. Choose one, write it in the
  spec, and keep it in every view.

## Tripo's own picture tools

`tripo-cli` 0.11.4 has picture commands that bill Tripo credits. They have
no dry run, and they were not tested for this skill.

- `tripo generate image-to-multiview front.png` makes front, left, back and
  right views from one picture, for 10 credits on Tripo's price list.
  `tripo generate multiview-to-model @last` then runs on those four views.
  Tripo's help says the tool is trained for 3D assets.
- `tripo generate edit-multiview` edits single views of such a task, for 5
  credits a view:

  ```bash
  tripo generate edit-multiview <task_id> \
    -p 'prompts=[{"view":"back","prompt":"fins instead of the panel"}]'
  ```

- `tripo generate image-to-image photo.png -p template=3d_enhance` cleans a
  photo for image-to-model.

Views from these tools still go through `prepare_views.py` and the reviewer.

## Preparing the views

`prepare_views.py` puts every view on one footing and measures it, with no
window and no network:

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/prepare_views.py -- \
  pictures/crate views/crate --size 2048
```

The input folder holds `front.png`, `left.png`, `back.png`, `right.png` and,
for review, `top.png`. For each, the script finds the object from the
picture's transparency, or from how far each pixel is from the backdrop
colour at the border. It gives the four side views one scale and one ground
line, centres each on a square canvas, and writes:

- `views/crate/<view>.png`, ready for Tripo3D;
- `views/crate/check/<view>.png`, the object on magenta, which shows any
  shadow or backdrop left in it;
- `views/crate/views.json` and a `PREPARED` line with the figures.

Keep the file names it writes. `tripo-cli` picks each slot from the file
name, and it matches any name that contains `front`, `back`, `left` or
`right`, so a file named `background_left.png` lands in the back slot.

Read these figures before the reviewer sees the views:

| Figure | What it shows | In the test |
| --- | --- | --- |
| `agreement.front_back`, `agreement.left_right` | How far opposite views share one outline, from 0 to 1 | 0.97 to 0.99 passed. 0.92 flagged an antenna drawn at two lengths. 0.73 and 0.67 were side views drawn as wide as the front |
| `width_to_height` of each view | The proportions, to check against the spec | Front 1.32 against the spec's 1.33 |
| `colour` of each view | Hue, colour strength and lightness of the object, and the spread of lightness | The same material should read the same in every view |
| `warnings` | A busy backdrop, an object touching the edge, an object close to the backdrop colour, an enlarged picture | Fix the picture before review |

## The reviewer

The reviewer's job is to find what differs from the target. A maker who
judges its own pictures sees what it meant to make, and passes them.

- Use a separate agent, such as a subagent or another session, or a person.
  It must not have made the pictures.
- Brief it with the target, the spec, the checklist and the candidates. Do
  not send your opinion of them or your figures. It measures again with its
  own tools.
- Give it the standard: a picture passes only when the object would sit in
  the target without looking out of place. "Close" and "in the spirit of"
  fail.
- Have it write each verdict to a file, with its figures and the comparison
  pictures it made. The maker acts on the file, and a later reader can check
  it.
- When the checklist and the human's brief disagree, for example on a size,
  the reviewer reports it and you ask the human which one wins. Do not settle
  it yourself.

## What fails a picture

| Fault | What it does to the model | Do this instead |
| --- | --- | --- |
| A picture edited again and again | Each edit smears detail and shifts colour, and a wrong pose stays | Make a fresh generation from the target and a crop. A single edit of a passed view, as in flip and edit, is fine |
| A detail on the wrong side | The mesh puts it there | Name sides by their place in the picture, and check one part that tells the sides apart, from the object's own point of view |
| A side view as wide as the front | The mesh mixes two depths | Flip the passed opposite view and edit its surface |
| A second whole picture given with an edit | The model copies that picture and ignores the edit | Give only the picture to edit, and describe the change in words |
| Hair-thin parts: twigs, wires, antennas, fringes | They become blobs, webs or holes, and they upset the scale between views | Paint them out of the picture and build them in Blender |
| Foliage, grass, water or smoke | The mesh is a solid lump | For a tree, make a picture of the bare trunk and limbs, and build the leaves in Blender |
| Glass or chrome | The texture copies what shows through it or in it | Show an opaque stand-in, as Tripo's guide says, or leave it out and build it in Blender |
| Extra or missing parts: a sixth finger, a rail the target lacks | The mesh copies them | Count fingers, toes, posts and rails against the target |
| A mirrored object | Every part sits on the wrong side | Check one part that tells the sides apart |
| A gradient or busy backdrop | It turns into geometry or a base | Flatten the backdrop to one plain colour under a mask, or cut the object out; leave the object's pixels alone, and record the step |
| Hard light and shadow | They are painted into the texture | Ask for soft, even light, and generate with `delight=true` |
| Coloured light from a scene | Every colour shifts | Ask for neutral white light, and judge the colour of the material |
| Colour left to fix later | The run copies the picture's colour. In one model, a repaint in Blender ended further from the target than the raw texture | Judge colour in the picture as well as shape |
| A close-up made from a small region of the target | It invents detail that the target is too small to show | Use close-ups to judge and to guide Blender work, not as proof of what the target shows |

## Measuring

Measure the candidate and the target the same way, and compare the figures.
`prepare_views.py` gives most of them for the views. The checks below are
for comparing a view with the concept.

- **Same size.** Shrink the candidate until the object is as many pixels tall
  as in the target. Enlarge both by the same factor and put them side by
  side. A detail that the target shows at its size must show in the
  candidate at that size. Detail that the target is too small to show does
  not count.
- **Shape.** Cut the object from the plain backdrop and read its outline:
  ratios such as height to the widest width, or the head to the whole height.
  A ratio holds at any picture size.
- **Colour.** For each named region, such as the face, the robe or the moss,
  read hue, colour strength and lightness: the middle value of a box and the
  range of its middle half. The range shows whether a surface is mottled or
  flat, which one middle value cannot.
- **Camera.** A target that looks down on the object shortens its height.
  Compare ratios from views at the same angle, or correct for the angle.
- Write each figure with how it was measured, so that another agent can
  repeat it.

## Keeping the pictures

- Keep each picture that passed with its prompt, its input pictures, the name
  of the image model, the seed and the verdict. It is the input of a paid
  run, so a person must be able to see how it was made.
- Keep the steps you applied to it, such as a flip or a backdrop fill, as a
  script or a written list.
- Delete the pictures that failed and the candidates you did not use, and
  keep a one-line record of each failed verdict. A folder of near-copies
  makes it hard to tell which picture went into the run.
