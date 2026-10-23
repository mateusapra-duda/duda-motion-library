# Duda motion spec

How Duda product and marketing animations move. It is written for two readers: the AI agent that builds the animations and the people who review them.

- **Numbers:** they live in `tokens.json`, and both the Rive pipeline and the HTML pipeline read from it.
- **Measured values:** they come from Duda's own curated Rive files: hero, small-and-medium agencies, and AI built for agencies. The measurements are in `reference/motion-extract.md`.
- ***rule* values:** they come from reviewing AI-made videos that looked wrong.

## Character
- **Smooth, rhythmic, nothing jumps.** Elements that appear **arrive and settle**: they travel 6–10 px (or scale 0.92–0.96 → 1) while fading in, and decelerate into place. They never pop in already placed ("snap") and never overshoot or bounce ("wobble").
  - **Where it applies:** menus opening, chat lines, cards, chips, rows.
  - **Where it doesn't:** the cursor (see Cursor) and the camera (see Camera).
- **Transitions are match cuts, not morphs.** One continuous motion hides the cut: the outgoing scene accelerates away, and the incoming scene continues that same motion, decelerating. Never morph one UI element into another, and never crossfade two screens.
- **The camera never stops.** Every scene keeps a slow, constant zoom or pan, so no frame is ever fully still.
- **AI elements breathe.** Anything AI-related gets a slow animated gradient, and nothing else does. That covers connecting an AI tool, AI buttons, the AI star, and "thinking" or "updating" states.
- **Movement does the work, opacity doesn't.** Duda's files use opacity almost only as a cut or a ≤167 ms fade.
- **One state at a time.** When an element changes state (loader → check, icon → icon), the new state starts on the old one's last visible frame. Never both on screen.

## House curves
| token | cubic-bezier | used for |
|---|---|---|
| `duda` | (0.75, 0, 0.25, 1) | default in-out: short moves of visible elements, scale, size, gradients |
| `duda_strong` | (0.8, 0, 0.2, 1) | medium moves (~500 ms), panels, size changes |
| `settle` | (0, 0, 0, 1) | arrive-and-settle: elements that **appear while moving**, the incoming half of a match cut |
| `match_cut.exit_ease` | (1, 0, 1, 1) | the outgoing half of a match cut: starts at rest, ends at full speed, right at the cut |
| `gradient` | (0.6, 0, 0.4, 1) | slow AI gradient sweeps (1.5–2.7 s) |
| `linear` | — | opacity, cursor press/release, spinners, camera drift, scene remap time |

`settle` starts at very high speed. That reads as "arrived" when the element was invisible a frame earlier, but as a jolt on something already on screen. On visible elements use `duda` or `duda_strong`.

## Match cuts
How Duda cuts between scenes, as measured in the hero file: scene 2 → 3 and scene 3 → 4.

1. **Exit.** The outgoing scene moves with `(1, 0, 1, 1)` for 400–600 ms (up to ~1 s), reaching its top speed on the last frame.
2. **Hard cut.** On the next frame only the incoming scene is visible. There is no overlap or crossfade.
3. **Entry.** The incoming scene continues the **same kind of motion in the same direction** with `settle` for 700–1000 ms.
   - Zoom in continues as zoom in, zoom out as zoom out, left as left, up as up.
   - A motion that changes direction across the cut breaks the illusion.
4. **Speed at the cut.** The entry's first frame moves at ~0.4× the average of the exit's last 4 frames. The measurement in hero1 is 0.34–0.36, and the allowed range is 0.25–1.0. A slight drop reads as "landing"; a bigger first step reads as a jump.
5. **Zoom cuts are subtler and shorter** (`match_cut.zoom`). *(eComm review)*
   - Exit: the scale changes 10% (to 110% zooming in, 90% zooming out) in 20 frames.
   - Entry: starts 7% away from rest (93% → 100% zooming in, 107% → 100% out) and lands in 35 frames.
   - Beats leave out the amount and the durations, so the token applies. The entry still lands: its first frame is ~0.6× the exit's last frame.
6. **Zoom cuts scale about the frame's centre, on both sides.** Only the scale animates. Each scene's pivot (`PIVOT` in `build.py`) is the centre of the frame. A pivot away from the centre makes the content slide toward or away from it. Two scenes with different pivots make the zoom's centre jump at the cut, which reads as a position move. The build fails a zoom cut whose pivots aren't the centre. *(eComm review)*

**Kinds:** zoom in / zoom out (scale about the frame's centre), up / down / left / right. Two different but similar motions also work, such as one element falling and the next scene rising from the same direction.

**Bleed:** the incoming scene starts offset, so it needs content beyond the frame on the side it comes from. Use replicated edges, a bigger photo, or a longer panel.

**Vary them:** within one video, use different kinds or directions for different cuts.

## Camera drift
- Each scene's camera keeps moving at a slow constant rate, `linear`.
  - **Zoom:** ~0.6%/s.
  - **Pan:** ~0.2 px/frame at 1920.
- Usually the drift continues the motion the scene entered with, so the match-cut entry decelerates *into* the drift instead of to a dead stop.
- **The drift follows the last move.** After a move inside the scene (the page sliding sideways, a pan), the drift continues in that move's direction. A drift that goes back to another direction after the move reads as a hiccup. *(eComm review)*
- The drift lives on its own node (`DRIFT_X`), separate from the cut moves (`SCENE_X`), so the two add up.
- Everything that belongs to the scene moves with the camera, cursor included, so clicks still land on their targets.

## Push-in (only when the storyboard draws the same screen at two scales)
**Never zoom into part of a scene on your own.** Don't zoom to make small text readable, to point at a detail, or to fill time. It crops the designer's composition into an off-centre framing, and the design looks bad. A scene rests only on its storyboard frames' own compositions (rule 11). When a must-read string is too small, fix it in the storyboard (`design-spec/STORYBOARD.md` §4), never with the camera. *(eComm review)*

When two storyboard frames show **the same screen at different zoom** (video 2: the Copilot panel, then its chat 2.5x), the designer drew both framings. Don't cut between them: a match cut between identical content shows the speed drop as a hiccup.
The same goes for the same screen **in another state or framing** (the eComm release note: the settings page, then the same page with a preview open and laid out differently). A cut there reads as a scene change that lands back on the same scene. It is one scene: the camera moves and the states change, with no cut. *(eComm review)*
- **One continuous camera move** (`push`) on its own node (`PUSH_X`, under the drift), rest to rest.
- **Pivot:** the fixed point between the two frames (the point that sits at the same place in both).
- **Ease:** `scroll`, ~1.5 s, applied in **log-scale** space so a big zoom looks even (the build bakes it as one fitted cubic).
- The text the viewer reads stays under the 30 px/frame cap; what leaves the frame may go faster, like a cut exit.
- Cursors live outside the push (in screen space of the zoomed frame), so their paths and speeds are what you see.

## Scrolling
A long scroll of readable content inside a scene (a table, a list) uses `ease.scroll` (peak ~2.5x its mean; `duda` peaks at ~4x): ~1.4 s for ~830 px keeps the text under 30 px/frame. The top of the list stays readable ~1 s before it scrolls.

## Timing
- **Durations** (ms): press/release 50 · fade ≤167 · short 333 · medium 500 · panel 767 · long 850 · transition ~1000 · gradient sweep 1600 · reading hold ~1000.
- **Stagger:**
  - 17 ms (1 frame) for clustered micro elements;
  - **67–83 ms** for list rows and cards.
- **Reading:** every message the viewer must read stays at least ~1 s once fully visible. The camera keeps drifting during that time.

## Cursor
- **Enters and leaves the frame.**
  - Every visit starts off-frame, already moving, and ends off-frame, accelerating.
  - It never appears, vanishes, or sits parked inside the frame.
  - **It never leaves with a cut.** A cursor that rides the match-cut exit vanishes on screen at the cut, and it reads as the mouse disappearing on the click. The build fails it. *(eComm review)* Either:
    - after its last click it flies off the frame before the scene's cut; or
    - **when its click opens the next screen, it crosses the cut.** The cut starts on the press (see Interactions), and the cursor lives above the scenes (`screen: true` on the visit, its points in frame coordinates). The page changes under it, as under a real mouse. It holds still through the exit, then leaves the frame from the next scene. *(eComm review)*
- **Curved path.**
  - The cursor rides a Follow Path, an open cubic path that the motion designer can edit in the Rive editor.
  - Each leg bows gently to the same side: ~8% of the leg's length, up to ~14% around a pass point.
- **Clicks land a moment before it stops.**
  - The press starts ~5 frames before the approach ends, while the cursor is still creeping its last 1–3 px.
  - The release ends with the arrival, and the next leg leaves 2 frames later. There is no dwell.
  - The press is scale 1 → 0.85 in 3 frames and back in 3 frames, linear.
  - Measured in hero_smb: the press starts 4–10 frames before the path ends.
- **Waiting aside.** When the cursor has to wait ~1.5–2 s for something on screen, it uses the Duda typing pattern below: it drifts aside and swoops back, and it never parks. For longer waits, or at the end of its job in a scene, it leaves the frame.
- **Follow Path keys are derived, never typed.** The cursor's `distance` keys are % of the path. The build recomputes them from the waypoints and times in `beats.yaml`, so you can edit the path freely.
- **A short "thought".** When it hovers something that opens more options (a menu row with a submenu), it pauses softly. It does not brake into the pause:
  - **Approach.** Ease `cursor.think.approach_ease` ≈ cubic (0.61, 0, 0.11, y2). It leaves the previous click slowly, then slows down over most of the approach. y2 (~0.91–0.96) is solved so the arriving speed equals the creep speed.
  - **Creep.** It moves ~4 px in ~350 ms at a constant speed (a straight line in the value graph) while the submenu opens.
  - **Leave.** Ease `cursor.think.depart_ease` ≈ cubic (0.55, y1, 0.4, 1). It picks up from the creep speed gently.
- **A breath between two clicks** (`cursor.breath`). This is lighter than a thought, and the cursor never stops:
  - after a click it leaves fast (`ease: go`), peaking about 0.3 s after the press;
  - it slows to a crawl at a pass point, at about a quarter of that peak;
  - it picks up again and lands on the next control with a long soft deceleration of about 0.75 s (`ease: land`).
  - It gives the viewer a beat to follow and reads human. Use it where it helps, not on every visit. *(eComm review, Mateus's editor edit)*
- **No kinks in the value graph.** At every keyframe, the speed coming in equals the speed going out. The graph shows only smooth curves or straight lines; a kink reads as a jolt (stop, start) even when both sides are slow. The build lints the cursor's graph for this.
- **Passing over** a point without hovering anything: it keeps ~30% of the leg's mean speed.
- **Duration** grows with distance: `clamp(450 + 1.4·d, 550, 900)` ms, where d is the path length in design px (measured median: 658 ms). The off-frame entry and exit legs stretch as needed to stay under the speed cap.
- **Focus first:** before typing into a field, the cursor clicks it. The caret appears and the field's border darkens on that click.
- **One cursor per task.** When the next action continues the same task in the same scene (open Copilot, then click its field), the same cursor travels there. It doesn't leave the frame and come back as another cursor. *(video 2 review)*
  - Through a push-in it keeps a **screen-space** path (what the viewer sees is one simple curve) and grows with the zoom to the size the design shows (`push ... carry: {CURSOR.size: s}`).

## Duda pattern: typing into a field
This is the standard whenever text gets typed into an input. It is copied from the user's reference, hero_smb CENA 1.2, `ROOT/BG/CURSOR 2`.

1. **Click the field.** The caret appears and the border darkens (focus). Typing starts ~150 ms later.
2. **Away.** After the click, the cursor drifts off along **one simple arc toward the next control**, bulging away from the text being typed (below it), sagitta ~16% of the distance (`cursor.aside.arc_sagitta`). *(video 2 review: a hook toward a control on the right reads as a strange loop)*
   - Ease `cursor.aside.ease.away` = cubic (0.338, 0, 0.228, 0.44).
   - It leaves from rest, slowly, and is still moving when it reaches the arc's midpoint.
   - **Hook (video 1 only):** when the next control sits *behind* the field (video 1's "+" was left of and below the prompt), the away move may be the reference's hook instead: to the side, then curving down toward the bottom-right, bow ~20% (`{aside: hook}`).
3. **Turn.** It turns without stopping (on the arc it simply keeps going). The speed coming in equals the speed going out; the build splits the time so this holds.
4. **Back.** It swoops to the next control.
   - Ease `cursor.aside.ease.back` = cubic (0.546, 0.355, 0.061, 1).
   - It picks up speed, peaks at ~40% of the leg, and lands with a long, very soft tail.
   - The press happens in that tail, a moment before it stops.
5. **The last character lands with the cursor.** Typing speed is set so the text finishes as the cursor arrives on the next control.

**Timing:**
- The reference takes 0.70 + 0.75 s. Video 1 uses ~1.45× that (1.0 + 1.1 s).
- Don't stretch beyond ~1.45×. If the text is long, type faster (video 1: ~57 chars/s) rather than slowing the cursor or parking it.
- The swoop's peak stays under the cursor cap. The build pulls the turn closer if needed; video 1 peaks at 43 px/frame, the same as the reference.

**In `beats.yaml`:**
```yaml
points: [{at: [252, 150], t: 1.30, click: true},   # the field
         {aside: true},                             # arc midpoint and time are computed ({aside: hook} = video 1)
         {at: [146, 202], t: 3.43, click: true}]    # next control
...
- {t: 1.45, do: type, target: PROMPT_TEXT.run0, until: 3.38, text: "..."}
```

## Duda pattern: the closing line
The closing line (the title and its subline on the closing frame) comes in **word by word**. *(eComm review, approved on v11 as the standard)*
1. **Soon.** The first word starts ~0.1 s after the closing scene's cut, while the scene's entry is still landing (`closing_words.delay_after_cut_ms`).
2. **Word by word, a minimal delay.** 60 ms between the title's words, 35 ms between the subline's. The subline starts ~20 ms after the title's last word.
3. **Each word** fades in, rises 6 px and sharpens from a **light** blur over 0.5 s (`duda`).
   - The blur is 6 px on the title and 3.5 px on the subline, in a 1360 frame.
   - More reads as out of focus.
4. **Every word lands exactly where the line sets it.** The end state is the storyboard frame's own composition.

**How:**
- In `build.py`: `V.words("E_L1", x, y, text, style, width=..., align="center")`, one call per line. Each word is a copy of the line with only that word visible, plus a Feather on its fill.
- In `beats.yaml`: `{t: 15.85, do: words, target: E_L1, kind: title}` and `{t: 16.05, do: words, target: E_L2, kind: subline}`. Timing, rise and blur come from `closing_words`.

## Interactions
- **Every control the cursor clicks reacts, twice:**
  - **Hover:** ~150 ms before the press, for example a fill change or a highlighted row. A hover that opens something stays on while that thing is open.
  - **Press:** on the press frame. The control squeezes (scale 0.9 for icon buttons, 0.96 for wide buttons, then springs back with `duda`) and/or its colour deepens.
  - **List and table rows don't squeeze.** A row's hover (its highlight) is its reaction, and its colour may deepen on the press. A whole row scaling reads as the page jumping. *(eComm review)*
  - The result of the click appears on the press frame, not after it.
  - **When the result is the next screen** (opening an order, a page, a project), the match-cut exit starts on the press frame. A cut that waits after the click reads as a click with no effect. The cursor crosses the cut (see Cursor). *(eComm review)*
- **Colours come from the design itself.** In the Claude prompt, for example, the send button hovers in the same orange as the Duda MCP toggle (`#ED7F5B`) and deepens on the press.
- The build lints this: a click with no reaction within 150 ms before the press is reported.

## State swaps
- **Loader → check.** The loader fades out in 100 ms, and the check (a trimmed stroke) starts drawing on the loader's last visible frame with `settle` over 300 ms. If the line has a label, it swaps from shimmering to solid at that same moment. In beats, write `do: resolve`.
- **The same rule holds for any swap:** an icon changing to another, a button label changing, a status flip. The outgoing state is gone by the time the incoming one is readable.
- The build lints loader/check pairs: they may share at most one frame.

## Reveal order and progress
- **Content first, then its label.** A badge or chip that describes something (for example "Sent from Claude · via Duda MCP") appears right after the thing it describes, never before it.
- **Agent progress is a list that keeps moving.**
  1. The active step has a loader and the AI shimmer on its text.
  2. When it finishes, it resolves into a drawn check (see State swaps), and the text settles to a solid colour. This is a swap between two identical copies of the text, so there is no ghosting.
  3. The next step enters below.

  There is always something happening, and the loop may cut in the middle of a step.
- **Figma is the visual reference, not the limit.** Motion may add states that the static design implies (hover, press, focus, progress steps), as long as they use the design's own components and colours.

## AI rewrite (the AI changes text that is already there)
Video 2's product description. In beats: `do: rewrite` per line.
1. **The AI button lights up** (soft purple glow + a gradient glint) while the AI works.
2. **Each line, left to right:** a purple highlight (the design's `bright-purple` at 70%, fading to transparent) sweeps in with the `gradient` ease, 0.6–0.85 s, lines staggered 67–83 ms.
3. **The edge is the swap.** Left of the edge is already the new text, right of it still the old one: every pixel shows one of them, never both (no ghost). A soft lilac light rides the edge.
4. **Source first, then where it shows:** the editor rewrites first, the live preview ~0.35 s later.
5. **Then it breathes:** a slow shine runs along the highlights while the new text is read (≥ 1 s), ending on the designed state.

## Speed limits (px per frame on the 1920-wide output, 60 fps)
| content | cap | why |
|---|---|---|
| anything with readable text | **30** | p90 of Duda's own moves. Above this the eye can't track it and it reads as flicker |
| chips, icons | 40 | |
| cursor | 45 | |
| match-cut exit, last frame | 150 | the cut hides it; measured exits go faster |

Panels and chat content don't slide their full width inside a scene; they are revealed or enter with a short `settle`.

## Rules (*rule*: from what went wrong in earlier AI videos)
1. **Rest to rest, relative to the camera.** Anything visible starts and ends at zero velocity within its scene. No move may start at full speed on screen; `settle` is only allowed where the start is invisible.
2. **Velocity is continuous.**
   - No direction reversal or speed jump between consecutive moves of the same element or of the camera.
   - The one deliberate discontinuity is the match cut, and it keeps its direction.
3. **One camera action at a time:** drift plus at most one cut move.
4. **No ghosts.** Never two dense layers (UI, text) above 15% opacity on the same frame. Scenes never overlap: a cut is a cut.
5. **No layout reflow while animating.** New chat lines or rows animate the space they take; nothing pushes text around in one frame.
6. **Seamless loop.** The last frame flows into the first. The seam is either a hold of ≥ 8 still frames or a match cut, in which case the video starts mid-entry. Ambient loops (shimmer, spinner) either stop before the seam or are hidden by it.
7. **Never fully static.** Something moves on every frame: the camera drift at minimum.
8. **Every video in a series moves differently.** The shared motifs (cursor, AI gradient, match cuts) are deliberate; the rest isn't copy-paste.
9. **A cut always changes screen.** Both sides of every cut show different screens. The build fails a cut whose two scenes share an interface layer. *(eComm review)*
10. **No cut-off edge ever shows.** The background and the interface continue past the frame wherever the camera, a drift or a cut exit looks. They come from Figma that way: square corners, the frame grown past its edges. Nothing is mirrored, stretched or repeated to fake it. The build fails when any plate edge, or any edge where an interface layer is cut off, enters the frame. *(eComm review)*
11. **Rest on the designer's compositions.** The Figma frames are curated layouts. A scene rests only on a frame's own framing, and motion travels between those framings: a camera move, a push between two frames the designer drew at two scales, or the page itself moving the way the next frame shows it. It never invents a framing of its own, such as a frame with a piece hidden, a zoom into a detail to read it, an off-centre push, or half a layout. Two frames of the same screen are joined by moving from one composition to the other. *(eComm review)*
12. **Glass stays glass.** A translucent or frosted panel shows the background behind it as Figma's glass does, wherever it moves. Its transparency is exported from Figma exactly, over flat black and white, never baked against one background. An edge the designer left past the frame never shows unless it is drawn. *(eComm review)*
13. **The video has square corners.** The rounded corners around the whole Figma frame stay in Figma. The video is square, so the page or the player can round it, or not, as each place needs. *(eComm review)*

## How a video is made
1. Storyboard frames come from Figma. Layout and content follow Figma exactly. Motion may add the states the design implies (hover, press, focus, progress steps), never new content.
   - **Canvas:** a project sets its own `canvas: {design, output}` in `beats.yaml` (video 2: 1920×1080 design = output). Token px values (measured on video 1's 680-wide frame) are converted so they keep their size on screen.
   - **Poses:** `poses:` in `beats.yaml` lists every Figma frame as overrides of the scene's first frame; `tools/pose_check.py` builds, captures and overlays them all.
2. The agent writes `beats.yaml`: what moves, when, and which token. It writes no raw keyframes.
   - **ops:**
     - camera: `match_cut`, `drift`, `push` (in-scene zoom);
     - cursor: `cursor_visit`, whose points can `click`, `pause` to creep, be `{aside: true}` (the typing pattern), or set their own `bow`, `tangent` or `ease`;
     - interaction: `press`;
     - text: `type` (with `cps` or `until`), `words` (the closing line, word by word);
     - elements: `enter`, `pop`, `fade`, `move`;
     - AI and progress: `sweep`, `spin`, `resolve`, `rewrite`;
     - housekeeping: `reset`.
3. `tools/choreo.py` turns beats and tokens into keyframes. The rules above hold by construction:
   - entry speed sized from the exit;
   - cursor timing from path length and the cap;
   - scenes reset while hidden.
4. The build lints the keyframes in screen space:
   - speed caps;
   - parked cursors;
   - cursor appearing on screen, or vanishing with a cut;
   - zoom cuts whose pivots aren't the frame's centre;
   - clicks with no reaction;
   - kinks in the cursor's value graph;
   - loader and check on screen together;
   - match-cut direction and speed ratio;
   - overlapping scenes;
   - never-static;
   - loop.

   `tools/lint_video.py` then checks the rendered MP4: pops outside planned cuts, frozen stretches, and direction across each cut.
5. Review the stills against Figma, then a preview, then the final render.

## Review checklist (lessons from video 1, "Claude → Duda MCP → Vibe")
Before sending a video, check each of these. Every one was a real note from the review.

- [ ] **Transitions** are match cuts: the same motion and direction across a hard cut. No morphs between elements, no iris, no crossfades.
- [ ] **The camera** drifts in every scene. No frame is fully still.
- [ ] **The cursor** enters and leaves off-frame, rides curved paths, and never sits parked.
- [ ] **The cursor never vanishes with a cut.** After its last click it flies off the frame before the cut, or, when the click opens the next screen, the cut starts on the press and the cursor crosses it (`screen: true`) and leaves from the next scene. *(eComm review)*
- [ ] **No zoom into part of a scene.** No push-in to read or to point. Every rest is a storyboard frame's own composition. *(eComm review)*
- [ ] **Zoom cuts** scale about the frame's centre on both sides: only the scale moves. *(eComm review)*
- [ ] **Clicks** start a moment before the cursor stops.
- [ ] **Hovering** something that opens a submenu gets a soft "thought": a long slowdown (≈ cubic .61, 0, .11, ~.91) into a creep, then a gentle departure. No braking.
- [ ] **The cursor's value graph** has no kinks: only smooth curves and straight lines.
- [ ] **The closing line** comes in word by word, ~0.1 s after its cut, each word rising and sharpening from a light blur (`words`). *(eComm review)*
- [ ] **Typing** uses the Duda typing pattern: click the field, then one simple arc to the next control with the reference eases, landing as the text ends. No hook unless the next control is behind the field. *(video 2)*
- [ ] **One cursor per task:** the same cursor goes on to the next action in the scene; it doesn't exit and re-enter. *(video 2)*
- [ ] **Every clicked control** has a hover and a press, using colours from the design. List rows don't squeeze. *(eComm review)*
- [ ] **Labels and chips** appear after the content they describe.
- [ ] **Loaders** resolve into checks on their last visible frame, never both at once.
- [ ] **Agent progress** keeps moving to the end of the scene, and the loop may cut mid-step.
- [ ] **AI moments** (connecting, AI buttons, thinking or updating) get the animated gradient.
- [ ] **Readable text** holds still for ≥1 s, apart from the camera drift.
- [ ] **The same screen at two scales**, when the storyboard draws both, is a push-in (one continuous camera move, log-scale), not a cut. *(video 2)*
- [ ] **Long scrolls** use `ease.scroll` and keep the text under 30 px/frame. *(video 2)*
- [ ] **AI rewriting text** uses the sweep-and-swap pattern: highlight sweep, the edge is the swap, source before preview, then a slow shine. *(video 2)*
- [ ] **Stills** match Figma: mean diff ≤ ~12/255 in `tools/overlay.py` (`tools/pose_check.py` does every frame).
- [ ] **Build lints and video lint** are clean.
