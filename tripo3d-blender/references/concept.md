# Spec and concept art

The mesh copies its input pictures, and the pictures copy the concept art.
So a model starts with a written spec and a concept that the human accepts.
Every later step is checked against these two. A model that must match a
whole scene, such as a furnished room, starts here too and then goes on to
[scenes](scenes.md).

## The spec

Write the spec before any picture exists, and keep it in the project as
`spec.md` beside the raw files. Ask the human for each field you cannot
take from their brief. Do not guess a size or a budget.

| Field | Example | Used by |
| --- | --- | --- |
| Name and use | A hero prop, seen up close in a game | The quality tier below |
| Target | A web game on null3d; a desktop engine; a film render | The Blender finish and the hand-off |
| Size in metres | 1.0 wide, 0.7 deep, 0.75 tall | `--height`, and the ratios the reviewer checks |
| The front | The face with the control panel | The front view and `--turn` |
| Parts by side | Front: screen; own left: cable; back: fins | The view prompts and the checklist |
| Materials and wear | Olive-drab painted steel, chipped edges, rubber bumpers | The concept prompt and the colour checks |
| Parts for Blender | A 0.4 m antenna; glass; rope; foliage | What the pictures leave out |
| Pose and movement | A-pose for rigging; a lid that opens | The views, and whether parts are separate runs |
| Game mesh | 30,000 triangles, 2048-texel maps, two levels of detail | `bake_maps.py` and `finish_model.py` |

Name each part by the object's own side: front, back, own left, own right,
top. The object's own left is on the viewer's right when you face its front.

Parts that Tripo3D cannot make well go in the "Parts for Blender" row from
the start: anything only a few pixels thick in a picture (antennas, wires,
rope, chains, twigs), glass and water, foliage, and cloth that hangs free.
The pictures leave them out, and Blender builds them.

## Quality tiers

The tier decides the picture size, the Tripo3D settings and the Blender
work. Credit figures are list prices from dry runs with `tripo-cli` 0.11.4
on 2026-11-27.

| Tier | Pictures | Tripo3D run | Blender |
| --- | --- | --- | --- |
| AAA hero | 2048 px, four views | H3.1 with `geometry_quality=detailed` and `texture_quality=detailed`: 60 credits, or 70 with 8K maps | Bake onto a game mesh with `bake_maps.py` |
| Standard prop | 1024 to 2048 px, two to four views | H3.1 with detailed textures: 40 credits | `finish_model.py` with `--levels` |
| Background | One 1024 px picture | H3.1 with standard textures and a low `face_limit`: 30 credits | `finish_model.py` with `--levels` |

Every AAA run is over 50 credits, so ask the human before it, as SKILL.md
says.

## Concept art

The concept is the design target: what the finished model must look like.
It comes from the human, or you make it with an image model and the human
accepts it.

A concept for a 3D model shows:

- the whole object, alone, with space around it;
- a three-quarter view from a little above, so that two sides and the top
  show;
- real materials and every detail the mesh must have, because the views
  and then the mesh copy only what a picture shows;
- a plain light grey or white background and soft, neutral white light.
  A warm or coloured light moves every colour that the views copy from the
  concept.

For a character, ask for the pose the views need, A-pose or T-pose (see
[pictures](pictures.md#characters-and-creatures)). Tripo's own image tools
have a `t_pose` template that puts a figure into that pose.

### Say where a detail sits in the picture

Image models confuse an object's own left and right. In a test on
2026-11-27, a concept prompt that put details on "the crate's own left side"
and "the crate's own right side" gave two pictures that both had the sides
mixed up. The same prompt with each visible face named by its place in the
picture gave two pictures with every detail in the right place. So:

- name the faces that show by where they are in the picture: "the face on
  the LEFT of the picture is the front";
- leave the hidden sides out of the concept prompt. The back and the far
  side come in with the views, from the spec.

A concept prompt that passed:

```text
Concept art for one AAA game prop, to be built as a 3D model: a rugged
military field supply crate for a realistic sci-fi game, 1.0 m wide, 0.7 m
deep, 0.75 m tall. Photorealistic, physically based materials, high detail:
olive-drab painted steel with paint chipped on the edges down to bare steel,
black rubber corner bumpers, steel bolts, light dust. Three-quarter view
from above the crate's top edge, so exactly two side faces and the top show.
The face on the LEFT of the picture is the front: a recessed control panel
with a small dark screen and a red latch handle, and nothing else. The face
on the RIGHT of the picture is a side: a blue-grey panel with a coiled black
cable hanging on a steel hook, and nothing else. A thin antenna mast about
0.4 m tall stands on the top at the far corner of that right-hand face. The
whole crate in frame with space around it. Plain light grey background, soft
studio light, a faint contact shadow only. No text, no other objects.
```

### Choosing an image model

Any image model that takes reference pictures as input works for the
concept and the views. Tripo3D's own image tools run through `tripo-cli`
and bill Tripo credits:

```bash
tripo generate text-to-image "<prompt>" --model banana_pro -p size=2K
tripo generate image-to-image concept.png --prompt "<prompt>" -p template=t_pose
```

`tripo docs --topic commands/generate` lists the models (Seedream, Google's
"banana" family and OpenAI's `chat_image` family) and their size rules. On
Tripo's price list, read on 2026-11-27, a picture costs 5 to 20 credits by
model and size. These commands have no dry run.

The test on 2026-11-27 used Google's Nano Banana Pro through fal.ai
(`fal-ai/nano-banana-pro` and `fal-ai/nano-banana-pro/edit`), at USD 0.15
for a 2048-pixel picture. Use the image model the human already pays for
when it can take reference pictures.

### Accepting the concept

1. Make two to four candidates, each a fresh generation.
2. Check each against the spec: every part on the right side, the ratios,
   the materials. Drop the ones that fail.
3. Show the rest to the human. The human picks one, or asks for changes.
   Make changes as fresh generations from the brief and the best candidate,
   not as edit after edit of one picture.
4. Keep the accepted concept with its prompt, its model, its seed and the
   date. It is the target for the checklist in [pictures](pictures.md).

When the concept and the spec disagree, for example on a size, ask the
human which one wins.
