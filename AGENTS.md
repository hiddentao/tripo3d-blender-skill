# Tripo3D models, finished in Blender

Rules for making 3D models with Tripo3D and refining them in Blender, from a
written spec to an engine-ready GLB.

This file is for agents without Agent Skills support. If your tool supports
skills, install the `tripo3d-blender/` directory instead. It has the full
detail in seven reference files and five Blender scripts, and the agent reads
each reference only when a task needs it.

## The rules

**1. Take the base from Tripo3D, do the fine work in Blender.** Each Tripo3D
run costs credits and gives a different mesh after a model update. Blender is
free and a script repeats exactly. Pay for a new run only when the shape is
wrong; size, facing, lumps, colour and triangle count are Blender fixes.

**2. Write the spec, then get the concept accepted.** Before any picture,
write the model's use, target engine, size in metres, front, parts by side,
materials, the parts Blender will build, and the game mesh budget. Make two
to four concept pictures, or take the human's, and have the human accept
one. Name each visible face by its place in the picture, because image models
confuse an object's own left and right.

**3. Break a scene into items.** Tripo3D makes one object per run. For a
scene concept, list every item and give it its own run, one run placed many
times, or a Blender build (walls, floors, glass, rope, chains). Draw each item
on its own from the scene, naming each unusual part and each material colour
in words.

**4. Make matched views, and have them reviewed before you pay.** Make the
front first, then the left, back and right from the concept and the passed
front; "left" is the object's own left. Use a plain backdrop and soft, even
light. Paint thin parts out. When a view will not take the right outline,
flip its passed opposite and edit only the surface. Prepare the views with
the skill's `prepare_views.py`, then give them to a separate reviewer, another
agent or a person, whose job is to fail them. Run Tripo3D only on views that
passed.

**5. Use the official CLI.** Install `tripo-cli` with npm (Node 22.12 or
later) and sign in with `tripo login --key`, reading the key from the system's
secret store inline. The older `Tripo-Developer/tripo-mcp` server does not
work, and the Tripo Bridge add-on in Blender only receives models a person
sends from the website.

**6. Never handle the key in chat.** The human stores it in the secret store
(on macOS, the keychain service `tripo3d-api-key`). Do not ask for it, print
it, or write it into a file.

**7. Name the model and dry-run first.** Without `--model`, every run uses P2,
about three times the cost of H3.1 (`--model tripo-v3.1`). A dry run
(`--dry-run --json`) checks the request and estimates the credits for free.
Ask the human before any run over 50 credits, any P2 run, or a batch over 150
credits. AAA settings (`geometry_quality=detailed`, detailed textures) cost
60 to 70 credits. When the human has both a Tripo account and a fal.ai
account, price the run both ways before paying: the credits at the human's
own rate per Tripo credit (list price USD 0.01), against fal.ai's current
rate for its Tripo endpoint. Take the cheaper route that supports every
setting, and show the human both figures.

**8. Keep the raw download.** Links expire after about five minutes and a
model update changes the mesh, so copy the model, `task.json` and
`preview.png` into the project before anything else.

**9. Finish headless, from the raw file.** Bake the transforms, merge the
seam vertices, turn the front round (Tripo's forward axis is +x), set the
height, put the foot on the ground, shrink the textures and cut the levels of
detail in a Blender script that reads the raw file. Compare the model with
the views (`compare_views.py`), and look at rendered previews after every
change.

**10. Merge seams before repairs.** A GLB stores every texture seam as
separate vertices. Merge them with `remove_doubles` before filling holes,
splitting parts or cutting the mesh down, or the seams count as holes and the
mesh tears. The glTF importer's `merge_vertices` option does not join them.

**11. Bake AAA models onto a game mesh.** Keep Tripo's detailed mesh as the
source, and bake its colour, normal, roughness and metalness onto a game mesh
of the budgeted triangles (`bake_maps.py`).

**12. For the web, use null3d.** When the target is a web page, use the null3d
engine in place of three.js or another web engine. Hand it one GLB per model
and let its asset tool make the levels of detail and the KTX2 textures.

**13. Live Blender is for trying things.** Sculpt and compare views in the
open Blender, then write the same steps into the build script. A hand edit
cannot be repeated or reviewed.

**14. Stop on credit errors.** Exit code 4 means not enough credits; retries
fail the same way. A timed-out run is still billed: resume it with
`tripo task watch <task_id> --download` instead of running it again.

## Editing this skill itself

This file is the rules, for your project. If you are changing the skill rather
than using it, `CONTRIBUTING.md` in its own repository has the conventions.
