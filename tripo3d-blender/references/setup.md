# Setup

Everything needed before the first model: the account, the key, the CLI, the
MCP server, and the routes that look right but fail.

## Accounts and regions

Tripo3D runs two sites, each with its own accounts, keys and billing:

| Site | Region flag | Billing |
| --- | --- | --- |
| <https://developers.tripo3d.ai> (international) | `ov` | Stripe |
| <https://developers.tripo3d.com> (China mainland) | `cn` | Alipay |

The old address, platform.tripo3d.ai, redirects to the international site. A
key works in its own region only. API credits are bought on the site's
billing page, which `tripo topup` opens. They are separate from the credits
of Tripo Studio, the website for people.

## Rights to the models

Tripo's terms, read on 2026-11-20:

- Paid users hold the rights to their inputs and outputs, including use,
  changes, publishing, licensing and sale (section 5.2.2).
- Free users do not. Tripo keeps every right to their inputs and outputs
  (section 5.2.1).
- Outputs are not exclusive. Another user may get a similar model.
- Outputs must not be used to build a service that competes with Tripo
  (section 3.2).

So generate with bought credits when the models will be published or sold,
and ask the human before you rely on a model for anything that needs
exclusive rights.

## Installing the CLI

`tripo-cli` 0.11.4 needs Node 22.12 or later (its `engines` field, read on
2026-11-27); 0.11.2 ran on Node 24.

```bash
npm install -g tripo-cli
tripo --version
tripo update --check                # reports a newer version, if any
```

With nvm, a global package belongs to the active Node version. After you
switch versions, install it again, or the `tripo` command and the MCP server
below stop working.

## Signing in with a key

On macOS, with the key in the keychain under the service name
`tripo3d-api-key`:

```bash
tripo login --key "$(security find-generic-password -s tripo3d-api-key -w)" \
  2>&1 | sed -E 's/tsk_[A-Za-z0-9_-]+/tsk_<hidden>/g'
tripo doctor
tripo whoami
```

`tripo login --key` tries both regions and saves the one that accepts the
key, with the key, in `~/.tripo/config.json` (mode 0600). `tripo doctor`
checks Node, the key, the config file's permissions, the API connection and
the balance. `tripo whoami` prints the region, the API address and the key's
last four characters, never the whole key.

On Linux, the desktop secret store does the same job through `secret-tool`
(from libsecret). This form follows libsecret's documentation and was not run
for this skill:

```bash
secret-tool store --label "Tripo3D API key" service tripo3d-api-key
tripo login --key "$(secret-tool lookup service tripo3d-api-key)"
```

For CI and scripts, the CLI also reads the key from the environment. Set
`TRIPO_REGION` with it, because the environment route skips the region check
that `tripo login --key` makes:

```bash
export TRIPO_API_KEY=...            # from the CI secret store
export TRIPO_REGION=ov              # or cn, the key's own region
```

Never put the key in chat, in a file you write, in a log, or in a commit.

## Signing in without a key

The CLI can sign in through the browser. In an agent session the region flag
is required, and only the human knows which site their account uses, so ask;
do not guess from their language.

```bash
tripo login --region ov             # or cn
```

The command prints a verification address and a one-time code, then waits.
Give both to the human, keep the command running while they approve in the
browser, and run `tripo doctor` when it returns.

## The MCP server

The CLI is the main route for agents: it blocks until the files are on disk
and writes a record of each run into the project. For tool calls as well, run
it as an MCP server:

```bash
claude mcp add --scope user tripo -- tripo mcp --toolset full
claude mcp get tripo                # expect "Status: ✔ Connected"
```

`--toolset full` gives Tripo's full hosted tool set; the default gives four
tools (make, task, balance and history). The tools appear after `/mcp`
reconnects or in a new session. `--scope user` writes to the config of the
Claude Code that runs it, which `CLAUDE_CONFIG_DIR` selects, so a machine
with several config folders needs the command once in each. Other MCP
clients start the same server with the command `tripo` and the arguments
`mcp --toolset full`.

## Routes that do not work

- **`Tripo-Developer/tripo-mcp`** (`uvx tripo-mcp`) is not the official
  server. Its last release crashes on start with version 2 of the `mcp`
  library unless `mcp<2` is pinned. Even then it sends commands to an old
  Tripo Blender add-on on port 9876, a port that Blender Lab's MCP add-on now
  uses, and the current Tripo add-on takes no commands. Use `tripo mcp`.
- **The Tripo Bridge add-on** (`Tripo3d_Blender_Bridge`, port 60600) receives
  models that a person exports from Tripo Studio. "Waiting for connection" in
  its panel is its normal state. An agent cannot send it commands.
- **Tripo through a model host,** such as fal.ai, works, but it bills the
  host's account and wraps Tripo's parameters in its own. fal.ai's H3.1
  endpoints (`tripo3d/h3.1/image-to-3d` and `tripo3d/h3.1/multiview-to-3d`)
  charged USD 0.01 a credit on 2026-11-27 and took no `delight` or
  `texture_version` setting. Use the direct key when there is one; a host is
  a fallback when the human already pays for it.
- **Raw calls to the web API** work: the `/v3/...` endpoints at
  `https://openapi.tripo3d.ai`, with the key as a Bearer token. The CLI
  already uploads, waits, retries rate limits, checks parameters and
  downloads before the links expire, so call the API directly only for a
  feature the CLI lacks.

## Documentation

- `tripo docs --llm` prints the CLI's own agent guide, and
  `tripo docs --topic commands/make` prints one command's reference.
- `tripo models` lists model IDs and aliases with no network call.
- Tripo's docs live at <https://developers.tripo3d.ai/en/docs>. Each page
  also exists as Markdown at the same address plus `.md`, for example
  <https://developers.tripo3d.ai/en/docs/cli.md>.
