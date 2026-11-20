# Generation

How to get the best base model for the fewest credits: the inputs, the
models, the parameters, Tripo's own processing steps and the costs.

## Inputs

`tripo make` reads its inputs and picks the endpoint itself:

| You pass | It runs |
| --- | --- |
| A quoted prompt | Text to model |
| One picture (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`) or its address | Image to model |
| Two to four pictures | Multiview to model |
| A model file (`.glb`, `.gltf`, `.fbx`, `.obj`, `.stl`) or its address | Import, which needs `--then` |
| A task id, `@last` or `@name` | More steps on that task, which needs `--then` |

For several pictures, file names that contain `front`, `back`, `left` or
`right` set each view. Without them the order is front, left, back, right. A
front view is required.

The picture decides the result. Give the whole object, alone, on a plain
background, lit softly and evenly. The model copies the surface, so wear,
moss, rust and colour must be in the picture. When a picture of one object is
cut from a larger scene, crop it close and clear the background first.
Pictures up to 20 MB are accepted.

## Models

`tripo models` lists the current IDs. On 2026-11-20 they were:

| Alias | ID | Faces | Notes |
| --- | --- | --- | --- |
| `tripo-v3.1` (H3.1) | `v3.1-20260211` | Up to 1,500,000; 2,000,000 with `geometry_quality=detailed` | Dense, detailed geometry. Has `geometry_quality`, `smart_low_poly` and `generate_parts` |
| `tripo-p2` (P2) | `P2-20260801` | 48 to 50,000 triangles, or 48 to 25,000 quads | The default. Clean, editable topology |
| `tripo-p1` (P1) | `P1-20260311` | 50 to 20,000 | The cheapest low-poly model. No quads |

Older H3.0 (`v3.0-20250812`) and H2.5 (`v2.5-20250123`) still run as legacy
models. Pass an alias to `--model` and let the CLI turn it into the dated ID,
because the API accepts only the dated form.

## Parameters

| Parameter | Status | Why |
| --- | --- | --- |
| `--model` | required in practice | Without it every run uses P2, about three times the cost of H3.1 |
| `--seed N` | recommended | Fixes the geometry seed: the same input, seed and model version give the same mesh |
| `-p pbr=true` | recommended | PBR maps (colour, roughness, metal, normal) are off by default since CLI 0.9.0 |
| `-p delight=true` with `-p texture_version=v3.5-20260815` | recommended | Removes the light baked into the picture, so the scene's own lights shade the model. If `tripo models` no longer lists v3.5, use the newest texture version it lists |
| `-p face_limit=N` | recommended | Without it the count is adaptive and often far above what a real-time scene can draw |
| `-p texture_seed=N` | optional | New textures on the same geometry: keep `--seed` and change this |
| `-p texture_quality=detailed` | optional | Sharper maps at a higher price. `extreme` gives 8K maps |
| `-p geometry_quality=detailed` | optional | H3.1 only. Finer geometry, 20 credits more |
| `-p auto_size=true` | optional | Rough real-world size in metres. Set the exact height in Blender anyway |
| `-p quad=true` | optional | Quad topology. Forces FBX, because glTF cannot store quads |
| `-n N` | optional | Up to four candidates with different seeds, each one billed |

Do not set `export_orientation` when you generate. A later processing step
then comes out wrongly turned, and nothing reports an error. Turn the model
in Blender, or on a final `convert` step.

Do not invent parameters. `tripo docs --topic commands/make` lists the ones
this version accepts, and a dry run shows which it removed.

## Costs

List prices from dry runs with `tripo-cli` 0.11.2 on an international
account, 2026-11-20:

| Request | Estimate |
| --- | --- |
| One picture on H3.1, detailed textures, PBR, delighting | 40 credits |
| The same picture on P2 with the CLI's defaults | 110 credits |

Tripo's price list for H3.1 on the same day:

| Input | No texture | Standard | Detailed | 8K |
| --- | --- | --- | --- | --- |
| Text | 10 | 20 | 30 | 40 |
| One picture, or several | 20 | 30 | 40 | 50 |

Extras on H3.1: detailed geometry 20 credits, quads 5, smart low-poly 10,
parts 20. Processing steps, from the CLI's docs: `decimate` 30 credits on
v2.0 and 35 on v3.0 (40 with quads); `uv` 20; `smartsegment` 85 from a
picture and 55 from a model. The CLI does not estimate texture or convert
steps, and a convert with any non-default option bills as a complex convert.

After a run, the result's `credits_consumed` gives what was billed.
`tripo balance` shows available and frozen credits (frozen means held for a
running task), and `tripo usage` lists recent spending. Read credit figures
as decimals: the API returns values such as `48.00`.

## Tripo's own processing steps

`--then` chains steps after the generation, separated by commas:
`texture`, `convert`, `rig-check`, `rig`, `retarget`, `segment`, `complete`,
`decimate` and `uv`. A bare value goes to the step's main setting.

```bash
tripo make ref.png --model tripo-v3.1 --then decimate:20000,uv
tripo make @last --then convert:fbx
```

Each step is a separate task, billed on its own and left out of the dry
run's estimate. The same steps run alone on a task or a file:

```bash
tripo mesh decimate hero.glb --model v3.0 --face-limit 5000 --smart-uv
tripo mesh uv hero.glb              # input must be under 80,000 triangles
tripo model texture @last -p pbr=true
tripo model convert @last --format GLTF --pivot-to-center-bottom
```

Decimation in Blender is free, so use Tripo's `decimate` only when
Blender's result spoils the shape. Tripo's retopology rebuilds the mesh and
bakes the textures onto it, which keeps a low-poly model looking like the
original.

## Keeping results

Tripo deletes a task's files after a while (status `expired`), and its
download links stop working after about five minutes. While the task lives,
`tripo task get <task_id> --download` fetches the files again. After that,
only your copy remains. Keep the raw folder with the model, `task.json` and
`preview.png`, and keep the exact command beside it, so a person can see how
the model was made and run it again.

## Concurrency

Each account has separate pools, so a full pool blocks only its own kind of
task:

| Pool | Tasks at once |
| --- | --- |
| H-series generation | 10 |
| P-series generation | 5 |
| Image generation | 1 |
| Rigging and animation | 10 |
| Texture and convert | 5 |
| Segment, complete and decimate | 10 |

`tripo batch run <manifest.yaml>` runs many jobs with retries and can resume
after a stop. Run `tripo docs --topic commands/batch` for its manifest
format.
