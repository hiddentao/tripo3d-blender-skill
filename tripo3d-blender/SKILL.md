---
name: tripo3d-blender
description: Make 3D models with Tripo3D and finish them in Blender. Tripo3D generates the base mesh from a prompt or a picture, and every fine refinement happens in Blender, headless or live, such as size, facing, pivot, cleanup, sculpted fixes, repainting, texture size, levels of detail and GLB export. Use when asked to generate or make a 3D model, statue, prop, building, rock, character or game asset from text or an image, or one that must match concept art or a photo, including making and reviewing the input pictures before any credits are spent; when setting up Tripo3D on a machine (API key, keychain, tripo-cli, tripo login, the Tripo MCP server); when a generated model needs fixing, retopology, LODs or engine-ready export; or when someone mentions tripo-mcp, Tripo Bridge, Tripo credits, tripo make or Blender MCP for generated models.
license: MIT
metadata:
  repository: https://github.com/hiddentao/tripo3d-blender-skill
---

# Tripo3D models, finished in Blender

Tripo3D turns a picture or a prompt into a textured mesh in about a minute.
Each run costs credits, its controls are coarse, and a new model version gives
a different mesh for the same request. Blender is free and exact, and a script
gives the same result every time. So take the base mesh from Tripo3D once,
keep it, and make every refinement in Blender. Pay for a new run only when the
shape is wrong. Size, facing, a lumpy hand, a texture tint and a triangle
budget are all Blender fixes.

Tested on 2026-11-20 with `tripo-cli` 0.11.2, Blender 5.3.0 and Node 24 on
macOS. If `tripo --version` prints a newer version, trust
`tripo docs --topic commands/make` over this file for flags.

## Reference files

This file takes one model from setup to a finished GLB. Open a reference only
when the task needs its detail.

| Reference | Open it when you are | Lines |
| --- | --- | --- |
| [setup](references/setup.md) | installing or signing in, adding the MCP server, working on Linux, or tempted by another Tripo route | 146 |
| [pictures](references/pictures.md) | making the input pictures for a model that must match a target picture, and having them reviewed | 123 |
| [generation](references/generation.md) | choosing a model or parameters, using several pictures, chaining Tripo's own steps, or counting credits | 146 |
| [blender](references/blender.md) | fixing a generated model, working in a live Blender, or fitting these steps into a project's build | 283 |
| [errors](references/errors.md) | reading a failed command's exit code, or a Blender script error | 43 |

The two scripts this file runs are in `tools/` beside it. Below, `<skill-dir>`
means the folder that holds this `SKILL.md`.

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

Never ask for the key in chat, and never write it into a file you create. Read
it from the secret store inline, as section 2 does.

## 2. Set up Tripo3D

Once per machine:

```bash
node --version                      # needs 20 or later
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

## 3. Generate a base model

**Choose the input.** One picture of the whole object, alone, on a plain
background, in a front or three-quarter view. Two to four pictures cover the
hidden sides; name the files `front`, `left`, `back` and `right`. The model
copies the picture's shape, surface and colour, so wear, moss and colour must
be in the picture. A quoted prompt also works, with less control.

**Have the pictures reviewed before you pay.** A fault in a picture comes
back in the mesh, and a new run costs the credits again. When the human gives
a target, such as concept art or a photo, and wants the model to match it:

1. write a checklist from the target alone: what each part shows, what fails,
   and ratios and colours that can be measured;
2. make two to eight fresh candidates for each view, the front first, and the
   other views from the passed front;
3. give the target, the checklist and the candidates to a separate reviewer,
   another agent or a person who did not make them, whose job is to fail them;
4. run Tripo3D only on pictures that passed, and write down the points the
   reviewer let through, for the Blender finish.

[pictures](references/pictures.md) has the loop, how to brief the reviewer,
what fails a picture and how to measure one.

**Choose the model.** Without `--model`, every run uses P2, which costs about
three times as much as H3.1.

| Model | Flag | Dry-run estimate | Use it for |
| --- | --- | --- | --- |
| H3.1 | `--model tripo-v3.1` | 10 to 50 credits; a picture with detailed PBR maps is 40 | Detailed solid objects: statues, props, rocks |
| P2 (default) | `--model tripo-p2` | 100 to 130 credits; a plain picture is 110 | Clean low-poly topology, quads |

**Dry-run it.** A dry run sends nothing and spends nothing:

```bash
tripo make ref.png --model tripo-v3.1 --seed 7 \
  -p face_limit=30000 -p pbr=true -p texture_quality=detailed \
  -p texture_version=v3.5-20260815 -p delight=true \
  --name statue -o tripo-out/statue --dry-run --json
```

`valid` must be `true` and `errors` empty. Each entry in `warnings` is a
setting the CLI removed, so that requirement will not be met; settle it
before paying. `generation_credits_estimate` is the list price of the
generation alone.

**Run it** without `--dry-run`. The command blocks until the model,
`preview.png` and `task.json` are in the `-o` folder, then prints one JSON
line. Take the model's path from its `model_file` field, because the file name
changes with the options (`pbr_model.glb`, for example). Look at
`preview.png` before you go on.

**Keep the raw result.** Download links expire after about five minutes, and
a later model version gives another mesh from the same seed, so the downloaded
files are the only copy:

```bash
mkdir -p assets/raw/statue
cp tripo-out/statue/* assets/raw/statue/    # model, task.json, preview.png
```

Commit that folder, or keep it with the project's source assets. Every Blender
step reads this copy and never the network, so a rebuild gives the same files.

**Stop and ask the human:**

- before any run estimated at more than 50 credits, any P2 run, and any batch
  whose estimates add up to more than 150 credits;
- after exit code 4, not enough credits, because every retry fails the same
  way: give the human `tripo topup` and wait;
- before `tripo redo`, because it is a new paid run with a new seed and no dry
  run.

## 4. Finish it in Blender

Both scripts run with no window and never use the network.

**Find the front.** Tripo's docs give +x as a generated model's forward axis.
Blender's front view looks along +y and shows the side that faces -y, so
turning +x to -y is `--turn -90`. Not every mesh follows the default, so
render the raw model first and look at `front.png`:

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/preview_model.py -- \
  assets/raw/statue/<model>.glb build/statue-raw --size 640
```

It writes `front.png`, `side.png` and `top.png` in about two seconds.

**Finish it:**

```bash
blender --background --factory-startup \
  --python <skill-dir>/tools/finish_model.py -- \
  assets/raw/statue/<model>.glb build/statue.glb \
  --height 6.5 --name statue --turn -90 --levels 0.4,0.12 --texture 1024
```

The script bakes every transform into the vertices, joins the parts into one
object and merges doubled vertices. It turns the model by `--turn` degrees
about the vertical axis, scales it to `--height` metres, centres it and
stands its lowest point on the ground. Then it shrinks textures longer than
`--texture` texels and writes `statue.glb`, plus `statue-1.glb` and
`statue-2.glb` cut to 40% and 12% of the triangles. Its last line,
`FINISHED {...}`, gives the size, the shrunk textures, and each file's
triangles and bytes. Only `--height` is required. `--turn` defaults to 0, and
without `--levels` or `--texture` it makes no copies and keeps the textures.

Render the finished file the same way and look again. If it faces the wrong
way, change `--turn` and finish again from the raw file. Never rotate the
exported file.

**Fix in Blender before you pay for a new run.** Scale, facing, pivot,
triangle count, texture size, colour, small lumps and holes, and fused parts
are Blender work. Go back to Tripo3D only when the shape itself is wrong.
[blender](references/blender.md#which-fix-goes-where) has the table.

**Use live Blender to try things,** such as sculpting a hand or comparing
views. Every change that ships goes into a script that rebuilds the model
from the raw file, because a hand edit cannot be repeated or reviewed, and
the next regeneration loses it. If the project already builds its models with
Blender scripts, add these steps to that build instead of shipping this
script's output.
