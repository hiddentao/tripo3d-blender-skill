# Errors

What to do when a command fails. For Tripo's API error codes behind these,
run `tripo docs --topic common-errors`.

## CLI exit codes

| Exit | Meaning | Do this |
| --- | --- | --- |
| 0 | Success | Read `preview.png`, then keep the raw result |
| 1 | Unexpected error | Run `tripo doctor`; if it passes, run the command once more with `--json` and read the error |
| 2 | Bad parameter or usage | Fix it against `tripo docs --topic commands/make`, then dry-run until `valid` is `true` |
| 3 | Authentication failed | Sign in again as in [setup](setup.md#signing-in-with-a-key); if that fails too, ask the human whether the key was revoked |
| 4 | Not enough credits | Stop. Every retry fails the same way. Give the human `tripo topup` and wait for them to confirm |
| 5 | Content policy | Change the picture or the prompt |
| 6 | Task failed, or the wait timed out | Failed: the frozen credits come back; ask before `tripo redo`, which is a new paid run. Timed out: the task still runs and is billed, so run `tripo task watch <task_id> --download` and never `make` again |
| 7 | Network error | The task may exist and be billed. Check `tripo balance` for frozen credits before you send it again. If the task succeeded and only the download failed, run `tripo task get <task_id> --download` |
| 8 | Not found | A task belongs to one key and one region. Use the same key, and check the region with `tripo whoami` |
| 9 | Rate limited | The CLI already waited and retried three times. Wait longer, then retry |

## Messages that are normal

- A model file is named `pbr_model.glb` or similar. Take its path from the
  result's `model_file`.
- Download links expire after about five minutes. Never store them; run
  `tripo task get <task_id> --download` for fresh ones.
- `frozen` credits are held for a running task. They are charged or returned
  when it ends.
- A task status of `banned` means the content policy refused the input, and
  `expired` means Tripo deleted the files. Both are final.
- A step after a generation that set `export_orientation` comes out wrongly
  turned, with no error. Turn the model in Blender instead.

## Blender errors

| Message | Cause | Do this |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'bpy'` | The script ran under plain `python3` | Run it with `blender --background --python` |
| `finish_model: the file holds no mesh` | The download is incomplete, or not a model | Check the file size and `task.json`, then download again with `tripo task get` |
| `finish_model: the model has no height` | Every vertex sits at one height, a flat or empty mesh | Look at the raw file's preview; the generation failed |
| Thousands of parts after splitting by loose parts | The seams were not merged | Merge the doubled vertices first, as in [blender](blender.md#fixes-as-code) |
| A preview shows the back of the model | The turn is wrong | Change `--turn` by 180 and finish again from the raw file |
| Nothing listens on port 9876 | Blender is closed, or *Allow Online Access* is off | Ask the human, as in [blender](blender.md#live-blender) |
