---
name: tripo3d-blender
description: Make 3D models with Tripo3D and finish them in Blender, from a written spec to an engine-ready GLB. Covers the spec, concept art, breaking a scene concept into single items, matched reference views from every side with plain or transparent backgrounds and controlled light, a review of those pictures before any credits are spent, AAA settings, and every refinement in Blender, such as size, facing, cleanup, repairs, baking a detailed mesh onto a game mesh, levels of detail and GLB export, with null3d as the engine for web targets. Use when asked to generate or make a 3D model, prop, character, building, environment or game asset from text, concept art, a scene or a photo; when setting up Tripo3D on a machine (API key, keychain, tripo-cli, tripo login, the Tripo MCP server); when a generated model needs fixing, retopology, baking, LODs or export; or when someone mentions tripo-mcp, Tripo Bridge, Tripo credits, tripo make, Tripo on fal.ai or Blender MCP for generated models.
license: MIT
metadata:
  repository: https://github.com/hiddentao/tripo3d-blender-skill
---

# Tripo3D models, finished in Blender

Tripo3D turns a picture or a prompt into a textured mesh in about a minute.
Each run costs credits, its controls are coarse, and a new model version gives
a different mesh for the same request. Blender is free and exact, and a script
gives the same result every time. So this skill spends its care on the
pictures before the run, takes the base mesh from Tripo3D once, keeps it, and
makes every refinement in Blender. Pay for a new run only when the shape is
wrong. Size, facing, a lumpy hand, a texture tint and a triangle budget are
all Blender fixes.

The path has seven steps: what the human does first, setup, the spec, the
concept art, the reference views, the run, and the Blender finish.

Tested on 2026-11-20 with `tripo-cli` 0.11.2, Blender 5.3.0 and Node 24 on
macOS. The path from concept to finished model was tested on 2026-11-27 on
Linux, with Blender 5.3.0, dry runs of `tripo-cli` 0.11.4, and one real H3.1
run through fal.ai. If `tripo --version` prints a newer version, trust
`tripo docs --topic commands/make` over this file for flags.

## Reference files

This file takes one model from setup to a finished GLB. Open a reference only
when the task needs its detail.

| Reference | Open it when you are | Lines |
| --- | --- | --- |
| [setup](references/setup.md) | installing or signing in, adding the MCP server, working on Linux, or tempted by another Tripo route | 156 |
| [concept](references/concept.md) | writing the spec, choosing a quality tier, or making and accepting concept art | 135 |
| [scenes](references/scenes.md) | making the items of a scene or environment, such as a furnished room, from one scene concept | 141 |
| [pictures](references/pictures.md) | making the reference views, preparing and measuring them, and having them reviewed | 376 |
| [generation](references/generation.md) | choosing a model or parameters, AAA settings, using several pictures, chaining Tripo's own steps, or counting credits | 226 |
| [blender](references/blender.md) | fixing a model, checking it against the views, baking a game mesh, handing it to null3d, or working in a live Blender | 443 |
| [errors](references/errors.md) | reading a failed command's exit code, or a script error | 51 |

The five scripts this file runs are in `tools/` beside it. Below,
`<skill-dir>` means the folder that holds this `SKILL.md`.

## 1. What a human must do first

An agent cannot do these. Ask for them before you run anything.

1. **A paid Tripo3D API account,** at <https://developers.tripo3d.ai>
   (international) or <https://developers.tripo3d.com> (China mainland). API
   credits are separate from Tripo Studio credits. Paid matters for rights:
   Tripo's terms give paid users the rights to their outputs, publishing and
   sale included (section 5.2.2), and keep free users' outputs for Tripo
   (section 5.2.1).
2. **The API key in the system's secret store.** On macOS the human runs this
   and types the key at the prompt, so the key never passes through chat:

   ```bash
   security add-generic-password -a "$USER" -s tripo3d-api-key -w
   ```

   Without a key, the browser sign-in in
   [setup](references/setup.md#signing-in-without-a-key) works too.
3. **Blender 5.x,** with `blender` on the path. Live control also needs the
   Blender Lab MCP add-on with *Allow Online Access* on; see
   [blender](references/blender.md#live-blender).
4. **The brief and the go-ahead.** What the model is for, its size, and the
   concept they accept. The human also answers before any run over the credit
   limits in section 6.

Never ask for the key in chat, and never write it into a file you create. Read
it from the secret store inline, as section 2 does.

## 2. Set up Tripo3D

Once per machine:

```bash
node --version                      # needs 22.12 or later
npm install -g tripo-cli            # installs the `tripo` command
tripo login --key "$(security find-generic-password -s tripo3d-api-key -w)" \
  2>&1 | sed -E 's/tsk_[A-Za-z0-9_-]+/tsk_<hidden>/g'
tripo doctor                        # every check "ok": true
```

`tripo login --key` tries both regions, keeps the one that accepts the key and
saves it in `~/.tripo/config.json` with mode 0600, so no later command needs
the key. A zero balance in `tripo doctor` is a warning, not a failure.

Use `tripo-cli`, Tripo's official tool, for every Tripo call. The older
`Tripo-Developer/tripo-mcp` server crashes on start and drives a Blender
add-on that no longer exists. The Tripo Bridge add-on in Blender only takes
models that a person sends from the Tripo website.
[setup](references/setup.md#routes-that-do-not-work) has the detail.

## 3. Write the spec

Before any picture, write `spec.md` with the human: what the model is for,
the target engine, its size in metres, which face is the front, each part and
the side it is on, the materials, the parts that Blender will build instead
(thin parts, glass, foliage), and the game mesh budget. Choose a quality
tier: an AAA hero model gets 2048-pixel views, Tripo's most detailed settings
and a bake onto a game mesh.
[concept](references/concept.md#the-spec) has the fields and the tiers.

When the concept shows a whole scene, such as a furnished room, list every
item in it and give each a route: its own run, one run placed many times, or
built in Blender. A separate run for each item gives better models than one
run for a group. [scenes](references/scenes.md) has the inventory, how to
measure each item, and how to draw each item on its own from the scene.

## 4. Make the concept art

The concept is the design target. The human gives it, or you make two to four
candidates with an image model that takes reference pictures, and the human
accepts one. It shows the whole object alone, in a three-quarter view from a
little above, in soft neutral light on a plain background.

Image models confuse an object's own left and right. Name each face that
shows by its place in the picture ("the face on the LEFT of the picture is the
front"), and leave the hidden sides out of the concept prompt.
[concept](references/concept.md#concept-art) has a prompt that passed.

## 5. Make the reference views

Tripo3D copies its input pictures: shape, proportions, surface and colour. A
fault in a picture comes back in the mesh, and a new run costs the credits
again. So:

1. **Write a checklist** from the spec and the concept alone: each part,
   its side, ratios and colours that can be measured.
2. **Make the front** from the concept: straight on, level with the middle of
   the object, from far away, on a plain white or light grey background, in
   soft even light. Pass it before you make anything else.
3. **Make the left, back and right** from the concept and the passed front.
   "Left" is the object's own left side. When a view will not take the right
   outline, flip its passed opposite view and edit only its surface.
4. **Paint thin parts out** (antennas, wires, rope), and leave glass out.
   Blender builds them.
5. **Prepare and measure** the views:

   ```bash
   blender --background --factory-startup \
     --python <skill-dir>/tools/prepare_views.py -- \
     pictures/crate views/crate --size 2048
   ```

   It gives the views one scale and ground line, a plain or transparent
   backdrop (`--alpha`), and figures: how far opposite views agree in outline
   (views that passed in the test scored 0.97 to 0.99), each view's
   proportions and colour, and warnings.
6. **Have them reviewed** by a separate reviewer, another agent or a person
   who did not make them, whose job is to fail them against the concept and
   the checklist. Run Tripo3D only on views that passed, and write down the
   points the reviewer let through, for the Blender finish.

[pictures](references/pictures.md) has the prompts, the camera, background
and light rules, the rules for characters, props, buildings and organic
models, Tripo's own picture tools, and the reviewer's brief.

## 6. Generate the base model

**Choose the input.** Four passed views give the best mesh; name the files
`front.png`, `left.png`, `back.png` and `right.png`, as `prepare_views.py`
does. One passed front view also works. A quoted prompt works too, with less
control.

**Choose the model.** Without `--model`, every run uses P2, which costs about
three times as much as H3.1.

| Model | Flag | Dry-run estimate | Use it for |
| --- | --- | --- | --- |
| H3.1 | `--model tripo-v3.1` | 10 to 50 credits; a picture with detailed PBR maps is 40; AAA settings are 60 to 70 | Detailed solid objects: statues, props, rocks, AAA models |
| P2 (default) | `--model tripo-p2` | 100 to 130 credits; a plain picture is 110 | Clean low-poly topology, quads |

**Dry-run it.** A dry run sends nothing and spends nothing. For an AAA model:

```bash
tripo make views/crate/front.png views/crate/left.png \
  views/crate/back.png views/crate/right.png \
  --model tripo-v3.1 --seed 7 -p geometry_quality=detailed \
  -p face_limit=500000 -p pbr=true -p texture_quality=detailed \
  -p texture_version=v3.5-20260815 -p delight=true \
  --name crate -o tripo-out/crate --dry-run --json
```

`valid` must be `true` and `errors` empty. Each entry in `warnings` is a
setting the CLI removed, so that requirement will not be met; settle it
before paying. `generation_credits_estimate` is the list price of the
generation alone. For a standard prop, drop `geometry_quality=detailed` and
lower `face_limit`; [generation](references/generation.md) has the
parameters.

**Choose the route.** When the human has a Tripo account and a fal.ai
account, compare the two before you pay: the dry run's credits at the
human's own rate per Tripo credit (list price USD 0.01), against fal.ai's
current rate for its Tripo endpoint. Check `tripo balance` too, because
credits already bought are already paid for. fal.ai's H3.1 endpoints lack
`delight`, `texture_version` and 8K textures, so a request that needs them
goes direct. Show the human both figures.
[generation](references/generation.md#tripo-direct-or-falai) has the steps.

**Run it** without `--dry-run`. The command blocks until the model,
`preview.png` and `task.json` are in the `-o` folder, then prints one JSON
line. Take the model's path from its `model_file` field, because the file name
changes with the options (`pbr_model.glb`, for example). Look at
`preview.png` before you go on.

**Keep the raw result.** Download links expire after about five minutes, and
a later model version gives another mesh from the same seed, so the downloaded
files are the only copy:

```bash
mkdir -p assets/raw/crate
cp tripo-out/crate/* assets/raw/crate/      # model, task.json, preview.png
```

Commit that folder, or keep it with the project's source assets, beside the
spec, the concept and the passed views. Every Blender step reads this copy
and never the network, so a rebuild gives the same files.

**Stop and ask the human:**

- before any run estimated at more than 50 credits, any P2 run, and any batch
  whose estimates add up to more than 150 credits;
- after exit code 4, not enough credits, because every retry fails the same
  way: give the human `tripo topup` and wait;
- before `tripo redo`, because it is a new paid run with a new seed and no dry
  run.

## 7. Finish it in Blender

All five scripts run with no window and never use the network.

**Find the front.** Tripo's docs give +x as a generated model's forward axis,
and the test run on 2026-11-27 faced +x. Blender's front view looks along +y
and shows the side that faces -y, so turning +x to -y is `--turn -90`. Not
every mesh follows the default, so render the raw model first and look at
`front.png`:

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/preview_model.py -- \
  assets/raw/crate/<model>.glb build/crate-raw --size 640
```

It writes `front.png`, `side.png` and `top.png` in a few seconds.

**Finish it:**

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/finish_model.py -- \
  assets/raw/crate/<model>.glb build/crate.glb \
  --height 0.75 --name crate --turn -90 --levels 0.4,0.12 --texture 1024
```

The script bakes every transform into the vertices, joins the parts into one
object and merges doubled vertices. It turns the model by `--turn` degrees
about the vertical axis, scales it to `--height` metres, centres it and
stands its lowest point on the ground. Then it shrinks textures longer than
`--texture` texels and writes `crate.glb`, plus `crate-1.glb` and
`crate-2.glb` cut to 40% and 12% of the triangles. Its last line,
`FINISHED {...}`, gives the size, the shrunk textures, and each file's
triangles and bytes. Only `--height` is required. `--turn` defaults to 0, and
without `--levels` or `--texture` it makes no copies and keeps the textures.

Render the finished file the same way and look again. If it faces the wrong
way, change `--turn` and finish again from the raw file. Never rotate the
exported file.

**Check it against the views.** `compare_views.py` renders the finished model
the way `prepare_views.py` framed each view, and measures how far the
outlines agree. A good Tripo3D crate scored 0.93 to 0.95 against its four
views. Look at the overlay of any view that scores well under that, and give
the pictures to the same reviewer.
[blender](references/blender.md#checking-the-model-against-the-views) has the
detail.

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/compare_views.py -- \
  build/crate.glb views/crate build/crate-compare
```

**Fix in Blender before you pay for a new run.** Scale, facing, pivot, one
dimension off the spec, triangle count, texture size, colour, small lumps
and holes, fused parts and thin parts left out of the pictures are Blender
work. Go back to Tripo3D only when the shape itself is wrong.
[blender](references/blender.md#which-fix-goes-where) has the table.

**Bake an AAA model onto a game mesh.** `bake_maps.py` cuts the detailed
model down to a game mesh, or takes your own with `--low`, and bakes colour,
normal, roughness and metalness maps onto it. It took a 440,650-triangle crate
to 30,000 triangles with 2048-texel maps in 37 seconds, with the same outline
agreement:

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/bake_maps.py -- \
  build/crate.glb build/crate-game.glb --triangles 30000 --size 2048
```

**For the web, use null3d.** When the target is a web page, use the null3d
engine in place of three.js or another web engine. Finish one GLB without
`--levels`, then optimize it with null3d's asset tool, which adds its own
levels of detail and KTX2 textures of up to 2048 texels.
[blender](references/blender.md#for-the-web-null3d) has the steps.

**Use live Blender to try things,** such as sculpting a hand or comparing
views. Every change that ships goes into a script that rebuilds the model
from the raw file, because a hand edit cannot be repeated or reviewed, and
the next regeneration loses it. If the project already builds its models with
Blender scripts, add these steps to that build instead of shipping this
script's output.
