# Tripo3D models, finished in Blender

Rules for making 3D models with Tripo3D and refining them in Blender.

This file is for agents without Agent Skills support. If your tool supports
skills, install the `tripo3d-blender/` directory instead. It has the full
detail in four reference files and two Blender scripts, and the agent reads
each reference only when a task needs it.

## The rules

**1. Take the base from Tripo3D, do the fine work in Blender.** Each Tripo3D
run costs credits and gives a different mesh after a model update. Blender is
free and a script repeats exactly. Pay for a new run only when the shape is
wrong; size, facing, lumps, colour and triangle count are Blender fixes.

**2. Use the official CLI.** Install `tripo-cli` with npm and sign in with
`tripo login --key`, reading the key from the system's secret store inline.
The older `Tripo-Developer/tripo-mcp` server does not work, and the Tripo
Bridge add-on in Blender only receives models a person sends from the website.

**3. Never handle the key in chat.** The human stores it in the secret store
(on macOS, the keychain service `tripo3d-api-key`). Do not ask for it, print
it, or write it into a file.

**4. Name the model and dry-run first.** Without `--model`, every run uses P2,
about three times the cost of H3.1 (`--model tripo-v3.1`). A dry run
(`--dry-run --json`) checks the request and estimates the credits for free.
Ask the human before any run over 50 credits, any P2 run, or a batch over 150
credits.

**5. Keep the raw download.** Links expire after about five minutes and a
model update changes the mesh, so copy the model, `task.json` and
`preview.png` into the project before anything else.

**6. Finish headless, from the raw file.** Bake the transforms, merge the
seam vertices, turn the front round (Tripo's forward axis is +x), set the
height, put the foot on the ground, shrink the textures and cut the levels of
detail in a Blender script that reads the raw file. Look at rendered previews
after every change.

**7. Merge seams before repairs.** A GLB stores every texture seam as
separate vertices. Merge them before filling holes or splitting parts, or the
seams count as holes and every face as a part.

**8. Live Blender is for trying things.** Sculpt and compare views in the
open Blender, then write the same steps into the build script. A hand edit
cannot be repeated or reviewed.

**9. Stop on credit errors.** Exit code 4 means not enough credits; retries
fail the same way. A timed-out run is still billed: resume it with
`tripo task watch <task_id> --download` instead of running it again.

## Editing this skill itself

This file is the rules, for your project. If you are changing the skill rather
than using it, `CONTRIBUTING.md` in its own repository has the conventions.
