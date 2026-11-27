# Tripo3D + Blender

An [Agent Skill](https://agentskills.io) that lets coding agents make 3D models
with [Tripo3D](https://www.tripo3d.ai) and finish them in
[Blender](https://www.blender.org), from a written spec to an engine-ready
GLB. The agent writes the spec, gets concept art accepted, makes matched
reference views from every side and has them reviewed, then pays for one
Tripo3D run. It keeps that mesh and makes every refinement in Blender: size,
facing, cleanup, repairs, baking onto a game mesh, texture size, levels of
detail and GLB export.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Validate](https://github.com/hiddentao/tripo3d-blender-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/hiddentao/tripo3d-blender-skill/actions/workflows/validate.yml)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-spec%20compliant-7c3aed)](https://agentskills.io/specification)

## What this is

Each Tripo3D run costs credits, and a model update gives a different mesh for
the same request. An agent that fixes a model by tweaking the prompt and
running again spends credits and loses the earlier result. Blender costs
nothing, and a script gives the same output every time. So this skill splits
the work: Tripo3D makes the base shape, and Blender does everything after it.

The skill also records the setup details that are easy to get wrong. The
official `tripo-cli` is the route that works for an agent, signed in from a
key kept in the system's secret store. The older `tripo-mcp` server and the
Tripo Bridge Blender add-on both look right and fail. The default model costs
about three times as much as the one most jobs need. And a GLB stores every
texture seam as separate vertices, which breaks simple Blender repairs unless
the seams are merged first.

The mesh copies its input pictures, so the cheapest fix is a better picture.
The skill has the agent write a spec, get concept art accepted, and make the
front, left, back and right views from it, in one scale and one light. A
script measures how far the views agree, and a separate reviewer, another
agent or a person, tries to fail them against the concept. Only pictures
that pass go to Tripo3D. In the project this skill comes from, eight models
made this way each took one run.

A scene concept, such as a furnished room, becomes an inventory of items.
Each item gets its own pictures and its own run, or is built in Blender, and
Blender puts the scene back together. For AAA work, the skill asks Tripo3D
for its most detailed mesh and bakes it onto a game mesh. For the web, it
hands the models to the null3d engine.

The agent gets:

- setup steps, tested on macOS, that keep the API key out of the chat;
- a spec, quality tiers and tested prompts for concept art and for each view,
  including a way to fix a side view's outline by flipping the view opposite;
- a way to break a scene concept into items and draw each one on its own;
- a review loop for the input pictures: a checklist written from the target,
  fresh candidates for each view, and a separate reviewer that measures each
  one before any credits are spent;
- a generation flow that dry-runs every request for free first, picks the
  model on purpose and asks the human above set credit limits;
- five Blender scripts that run with no window. They prepare and measure the
  view pictures; finish a raw model (transforms, seams, facing, height,
  ground contact, texture size and levels of detail); render previews;
  compare the finished model with the views; and bake a detailed model onto
  a game mesh;
- the hand-off to null3d for web targets;
- tested Blender code for common repairs, and a table of when a paid Tripo3D
  step is worth it instead;
- what to do for every CLI exit code.

## The rules

1. **Take the base from Tripo3D, do the fine work in Blender.** Pay for a new
   run only when the shape is wrong.
2. **Write the spec, then get the concept accepted** by the human.
3. **Break a scene into items,** each with its own run, or built in Blender.
4. **Have the views reviewed before you pay.** A fault in a picture comes
   back in the mesh, and a new run costs the credits again.
5. **Use the official CLI.** `npm install -g tripo-cli`, then
   `tripo login --key` with the key read from the secret store.
6. **Keep the key out of chat.** The human stores it; the agent never asks
   for it or prints it.
7. **Name the model and dry-run first.** The default P2 model costs about
   three times as much as H3.1, and a dry run shows the cost for free.
8. **Keep the raw download.** Links expire in minutes and a model update
   changes the mesh.
9. **Finish headless from the raw file,** compare it with the views, and look
   at rendered previews after every change.
10. **Merge seams before repairs,** or every seam counts as a hole.
11. **Bake AAA models onto a game mesh.**
12. **For the web, use null3d.**
13. **Use live Blender to try things,** then write the steps into the build
    script.
14. **Stop on credit errors.** Retries fail the same way.

## Requirements

- A paid Tripo3D API account at
  [developers.tripo3d.ai](https://developers.tripo3d.ai) (international) or
  [developers.tripo3d.com](https://developers.tripo3d.com) (China mainland),
  with credits. Tripo's terms give paid users the rights to their models,
  publishing and sale included. Free users' models belong to Tripo.
- Node.js 22.12 or later, for `tripo-cli` 0.11.4.
- Blender 5.x, with the `blender` command on the path.
- For live control of an open Blender, Blender Lab's
  [MCP add-on and server](https://projects.blender.org/lab/blender_mcp).

Tested on 2026-11-20 with `tripo-cli` 0.11.2, Blender 5.3.0 and Node 24 on
macOS. The path from concept to finished model was tested on 2026-11-27 on
Linux with Blender 5.3.0, dry runs of `tripo-cli` 0.11.4, Nano Banana Pro for
the pictures and one H3.1 run, both through fal.ai.

## Install

This skill follows the
[Agent Skills specification](https://agentskills.io/specification), so you
install it the same way in every tool: copy the `tripo3d-blender` directory
into the folder where your tool looks for skills. Do not rename the directory.
The spec requires it to match the skill's name.

```bash
git clone https://github.com/hiddentao/tripo3d-blender-skill.git
```

Then copy the skill directory to the right place:

| Tool | Project-level | User-level |
| --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex CLI, ChatGPT desktop | `.agents/skills/` | `~/.agents/skills/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| GitHub Copilot, VS Code | `.github/skills/` | `~/.copilot/skills/` |
| Gemini CLI, Zed | native skills support | see tool docs |

For example, for Claude Code:

```bash
mkdir -p ~/.claude/skills
cp -r tripo3d-blender-skill/tripo3d-blender ~/.claude/skills/
```

To get updates with `git pull`, use a symlink instead:

```bash
ln -s "$PWD/tripo3d-blender-skill/tripo3d-blender" ~/.claude/skills/
```

### Claude Code plugin

Run these two commands in a shell, or as slash commands in a session:

```bash
claude plugin marketplace add hiddentao/tripo3d-blender-skill
claude plugin install tripo3d-blender@tripo3d-blender-skill
```

### claude.ai and the Claude desktop app

The chat apps install skills from a zip file that has the skill folder at its
root:

```bash
cd tripo3d-blender-skill
zip -r tripo3d-blender.zip tripo3d-blender/
```

Their sandbox has no Blender, so there the skill can help plan a model but not
finish one. Use it in a coding agent on your own machine to run the commands.

### Any other agent

Most tools without skills support read [AGENTS.md](https://agents.md). Copy
[`AGENTS.md`](AGENTS.md) to your repo root. It has a short version of the
rules. For the full detail, copy the skill directory into your repo as well,
so your agent can open the [references](tripo3d-blender/references/) and run
the [scripts](tripo3d-blender/tools/).

## Using it

Ask for the outcome. The agent reads the skill and follows it:

- "Set up Tripo3D on this machine. The API key is in the keychain under
  `tripo3d-api-key`."
- "Make a weathered stone lantern, 2.2 m tall, from `lantern.png`. I need a
  GLB with two lower levels of detail and textures no larger than 512 texels."
- "Make the lantern in `concept.png` as a 3D model. Have the input pictures
  reviewed against the concept before you spend credits."
- "Here is a concept of a games room. Make the pool table, the chairs and the
  trophy cabinet as separate AAA models for our null3d web game."
- "The statue's hands look melted. Fix them in Blender without generating it
  again."

The agent shows the credit estimate and waits for your answer before any run
over 50 credits, any run on the more expensive P2 model, and any batch over
150 credits.

## How it is laid out

`tripo3d-blender/SKILL.md` takes one model from setup to a finished GLB in
308 lines. The seven files in `references/` cover setup, the spec and
concept, scenes, input pictures, generation, Blender and errors, and the
agent reads each one only when a task needs it.
`tools/` holds the five Blender scripts that the skill runs.

Outside the skill directory, `tools/validate.mjs` checks the skill against the
spec and its own conventions, and `tools/selftest.sh` runs the Blender scripts
on a test model.

## Testing the scripts

```bash
./tools/selftest.sh                 # BLENDER=/path/to/blender if it is not on the path
```

It builds an awkward model, finishes it, checks every output file, renders
the previews, prepares and compares reference views, and bakes the model onto
a lighter mesh. It takes about 25 seconds and spends no Tripo3D credits.

## Contributing

Issues and pull requests are welcome. [CONTRIBUTING.md](CONTRIBUTING.md)
covers the checks a change goes through: the `humanizer` skill over any prose
you add, the validator, and the Blender self-test.

```bash
node tools/validate.mjs
```

## License

[MIT](LICENSE).
