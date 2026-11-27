# Contributing

Issues and pull requests are welcome.

The skill is prose and five scripts that an agent runs as written, so a wrong
command or a stale flag fails on someone else's machine. Three checks stand
between a change and a merge, and CI runs two of them.

## Write it through the humanizer skill

Put new or reworded text through the `humanizer` skill before you commit it.
That covers `SKILL.md`, the references, `AGENTS.md`, the README, this file,
commit messages and pull request descriptions. If your tool cannot run the
skill, work from Wikipedia's
["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
which it is based on. A reference that reads like a sales page is a reference
an agent will summarise back at you instead of following.

## Run the validator

```bash
node tools/validate.mjs
```

It checks:

- the frontmatter against the Agent Skills spec;
- that every reference exists, and that the line counts in the routing table
  are the real ones;
- that every script the prose runs exists;
- that links and anchors between files resolve;
- that prose wraps at 80 columns and has no em or en dashes;
- that nothing from the machine the skill was written on (a home folder, a
  tool's name, a project's name) has reached the files that travel;
- that the skill directory holds exactly one `SKILL.md`, and that the
  marketplace manifest matches the repository.

CI runs it on every pull request, and byte-compiles the Python scripts.

## Run the Blender self-test

```bash
./tools/selftest.sh                 # BLENDER=/path/to/blender if it is not on the path
```

It builds an awkward model (four textured parts under a parent that is
moved, turned and scaled), runs `finish_model.py` and `preview_model.py` on
it, and fails unless every finished file holds one object with no rotation or
scale, stands 2 m tall on the ground, is centred, keeps its textures at 512
texels or less, and has fewer triangles than the level before it. Then it
renders reference views of the finished model, prepares them with
`prepare_views.py`, compares the model with them with `compare_views.py`,
checks that swapped left and right views score low, and bakes the model onto
a tenth of its triangles with `bake_maps.py`. It takes about 25 seconds and
spends no Tripo3D credits.

The scripts run on Blender's own Python, with its bundled `numpy` and nothing
else, so a user needs no other package.

CI cannot run it, because it needs Blender. Run it after any change to
`tripo3d-blender/tools/`, and say in the pull request which Blender version
you used. A code snippet you add to a reference must also have run against a
real model on that version.

## Tripo3D facts and numbers

Credit prices, model IDs, face limits and the CLI's flags change between
releases. Each one in this skill names the date and the `tripo-cli` version it
came from. When you change one, take it from `tripo --version`,
`tripo models`, `tripo docs --topic ...` or a dry run, and record the date,
the version and how you got it. A dry run costs nothing, so use it to check a
flag before you document it.

Never paste an API key, a download link or a task id from your own account
into an issue or a pull request.
