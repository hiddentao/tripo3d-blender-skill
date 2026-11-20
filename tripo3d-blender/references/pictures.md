# Input pictures

Tripo3D builds the mesh from its input pictures and copies them: shape,
proportions, surface and colour. A fault in a picture comes back in the mesh,
and a new run to fix it costs the credits again. A picture costs little to
make and to check. So make the pictures first, have a separate reviewer try
to fail each one against the target, and pay for a run only on pictures that
passed.

In the project this skill comes from, about 200 candidate pictures gave 24
that passed. Eight models were made from them, one run each, and none has
needed a second run for its shape so far.

## The loop

1. **Fix the target.** The target is the picture that says what right looks
   like: concept art, a photo or a sketch from the human. If you have only a
   prompt, make a target first and ask the human to accept it.
2. **Write a checklist from the target alone,** before any candidate exists.
   For each part of the object, write what the target shows and what fails,
   and mark the parts that fail a picture by themselves. Give figures that can
   be measured: proportions as ratios, such as height to knee width, and the
   colours of named regions (see [Measuring](#measuring)). A checklist written
   after you have seen candidates drifts toward them.
3. **Make candidates.** Give an image model that takes pictures as input the
   target, a close crop of the object from it, and a prompt for one view. Make
   two to eight candidates for each view, each one a fresh generation.
4. **Check them yourself** with the reviewer's measuring tools, and send only
   the best candidate for each view.
5. **Have them reviewed.** A separate reviewer judges each picture against
   the target and the checklist (see [The reviewer](#the-reviewer)). Its
   verdict is pass, pass with points to carry, or fail with the reasons.
6. **Pay only on a pass.** Spend no credits on a picture without a passing
   verdict. While the front fails, spend none on the other views either,
   because they are made from it.
7. **Carry the points.** Write each point the reviewer let through, such as a
   head 10% small or stone too light, into the notes for the Blender finish.
   Blender fixes them for free.
8. **Judge the model the same way.** After the run and the finish, the same
   reviewer judges renders of the model against the same target and
   checklist.

## The reviewer

The reviewer's job is to find what differs from the target. A maker who
judges its own pictures sees what it meant to make, and passes them.

- Use a separate agent, such as a subagent or another session, or a person.
  It must not have made the pictures.
- Brief it with the target, the checklist and the candidates. Do not send
  your opinion of them or your figures. It measures again with its own tools.
- Give it the standard: a picture passes only when the object would sit in
  the target without looking out of place. "Close" and "in the spirit of"
  fail.
- Have it write each verdict to a file, with its figures and the comparison
  pictures it made. The maker acts on the file, and a later reader can check
  it.
- When the checklist and the human's brief disagree, for example on a size,
  the reviewer reports it and you ask the human which one wins. Do not settle
  it yourself.

## Views

Tripo3D's multiview input has four slots: front, left, back and right (see
[generation](generation.md#inputs)). All the pictures must show one object.

- Make and pass the front first. Then make the other views from the passed
  front, not from the target alone, so that every view shows the same object.
- A side view that disagrees with the front fails, even if it looks good
  alone. Limbs at other heights, or a different tree, give a mesh that mixes
  two objects.
- A three-quarter view fits none of the four slots. Use it to judge the
  model, not as an input.
- If a view fails and a new one does not pass, run on the views that passed.
  The front alone still gives a usable mesh. A wrong side view gives a wrong
  one.
- Give every view the same backdrop, light, scale and framing: one plain
  colour behind, soft even light, no cast shadow, and the whole object in the
  frame.

## What fails a picture

| Fault | What it does to the model | Do this instead |
| --- | --- | --- |
| A picture edited again and again | Each edit smears detail and shifts colour, and a wrong pose stays | Make a fresh generation from the target and a crop. Never edit a failed picture again |
| Hair-thin parts: twigs, wires, fringes | They become blobs, webs or holes | Paint them out of the picture and build them in Blender |
| Foliage, grass, water or smoke | The mesh is a solid lump | For a tree, make a picture of the bare trunk and limbs, and build the leaves in Blender |
| Extra or missing parts: a sixth finger, toes on the wrong leg, a rail the target lacks | The mesh copies them | Count fingers, toes, posts and rails against the target |
| A mirrored object | Every part sits on the wrong side | Check one part that tells the sides apart, from the object's own point of view |
| A gradient or busy backdrop | It turns into geometry or a base | Flatten the backdrop to one plain colour under a mask, leave the object's pixels alone, and record the step |
| Hard light and shadow | They are painted into the texture | Ask for soft, even light, and generate with `delight=true` |
| Colour left to fix later | The run copies the picture's colour. In one model, a repaint in Blender ended further from the target than the raw texture | Judge colour in the picture as well as shape |
| A close-up made from a small region of the target | It invents detail that the target is too small to show | Use close-ups to judge and to guide Blender work, not as proof of what the target shows |

## Measuring

Measure the candidate and the target the same way, and compare the figures.

- **Same size.** Shrink the candidate until the object is as many pixels tall
  as in the target. Enlarge both by the same factor and put them side by
  side. A detail that the target shows at its size must show in the
  candidate at that size. Detail that the target is too small to show does
  not count.
- **Shape.** Cut the object from the plain backdrop and read its outline:
  ratios such as height to the widest width, or the head to the whole height.
  A ratio holds at any picture size.
- **Colour.** For each named region, such as the face, the robe or the moss,
  read hue, colour strength and lightness: the middle value of a box and the
  range of its middle half. The range shows whether a surface is mottled or
  flat, which one middle value cannot.
- **Camera.** A target that looks down on the object shortens its height.
  Compare ratios from views at the same angle, or correct for the angle.
- Write each figure with how it was measured, so that another agent can
  repeat it.

## Keeping the pictures

- Keep each picture that passed with its prompt, its input pictures, the name
  of the image model and the verdict. It is the input of a paid run, so a
  person must be able to see how it was made.
- Delete the pictures that failed and the candidates you did not use, and
  keep a one-line record of each failed verdict. A folder of near-copies makes
  it hard to tell which picture went into the run.
