# Motion learnings

What reviewed Rive motion pieces at Duda taught us (October–November 2026): the cursor, hover and click, typing, the
Copilot and the AI's answers, the generation effect, cuts, camera, timing and loops, what the reviewer rejects, edges,
delivery, interactive pieces, Rive pitfalls, and measured recipes for whole actions. **Every rule here is approved** by
the motion designer who reviews the pieces and fine-tunes them in the Rive editor.

**Read it all before scripting a piece**, and go through section 12 (what the reviewer rejects) before every delivery.
It holds for any interface motion in Rive: a scene built by a script with the Rive CLI, then adjusted by hand in the
editor.

- Numbers are at 60 fps; **f** = frames (38 f ≈ 0.63 s; f207 = frame 207). Curves are normalised cubic-bezier
  (x1, y1, x2, y2); `duda`, `settle` and the other curve names are the tokens in `tokens.json`.
- **Overrides MOTION.md** marks a learning that contradicts `MOTION.md` or `tokens.json`. The learning wins: it is
  newer and approved.
- "Rejected" or "wrong" describes what the reviewer turned down, so you don't repeat it.
- Where the library doesn't follow a rule yet, section 18 says so. Then say it in the plan and note it in the piece's
  `NOTES.md` as a library suggestion.

## 1. Working with the motion designer (every piece)
- Write the plan in words (timing, cursor, AI moments, the loop seam) and wait for the OK before animating. If
  something isn't clear, ask. A note like "remove it from some elements": ask which ones before removing it from all.
- **Change only what was asked.** Camera, cuts, timing and curves the motion designer set by hand are not
  "consequences" to fix. If a request shifts something of theirs (a new duration moves the camera), say so in one line
  and ask.
- Once the motion designer edits the file in the Rive editor, that file is the source of truth: they move beats
  earlier, remove blank frames, retouch hovers, and none of it is in the build. Always start from their version and
  compare first; never rebuild over it.
- To find what they changed: convert both `.rev` files (`rive create --from-rev`) and compare **every** property by
  name and **every** timeline, not only the cursor (they once edited the wrong timeline without knowing).
- "Keep the cursor exactly as I left it": their cursor goes in with their exact numbers, and the scene is refitted to
  it: hovers, presses, cuts and what follows move to their frames.
- "Do it as I did" / "copy the reference": copy their curves and timings whole, measured in the `.rev`, instead of
  reinterpreting them.
- Alternatives are separate versions (v06 and v07 side by side); the previous one stays intact until the motion
  designer picks. Before changing a version they have seen, keep its sources (done automatically; §6 of `new-motion.md`).
- The design lead's notes come with a timecode ("00:00:04:39"). Bring the options to the motion designer; they decide.
- Times dictated as "00:03:27" are the editor's clock, seconds:frames (= f207). "80 80" is After Effects' 80 %
  influence on both keys = (0.8, 0, 0.2, 1).
- They like to try timings in the editor: make each event (a cut, a swap) depend on 1–2 keys they can drag, and say in
  the delivery which object and property to drag.
- A curve they send (a screenshot of the graph) goes in as a real cubic key, never baked into one key per frame.
- In `MAIN`, one timeline ("Timeline", the piece's length) and one layer ("Main") in the state machine. A scene in
  several parallel layers is "very hard to work with".
- When they ask for "like in After Effects", or for a piece they will edit by hand in the editor:
  - one artboard per scene (a precomp), nested in `MAIN` inside a Solo that keys which scene is showing;
  - each scene, and each component that needs its own timing (a card, a block), plays on a two-key "time" they can
    drag;
  - the cursor lives in its scene, or on `MAIN` when it crosses from one scene to another;
  - opacity only where two scenes draw at once (a crossfade), and the delivery says where;
  - with the library: `p.build(remap=...)`.

## 2. Product fidelity and poetic licence
- By default, true to the product: layout, colours, type, icons, which screens and states exist and their order. Poetic
  licence is allowed when it makes the video more beautiful or clearer, as the Copilot already does.
- Polish is always allowed: Duda curves and durations instead of raw CSS transitions, arrive and settle, staggers,
  softer hover and press. "Otherwise it would just be a screen recording."
- Content, structure and behaviour come from the product; spacing, font size and border colour come from Figma when the
  same UI exists in both. If separating them gets too complicated, follow the product.
- Keep a "Product vs polish" table in the brief or `NOTES.md`, one row per deviation.
- Storyboards idealise (code typing itself, "Generating…" blobs): point out where they differ from the product and let
  the motion designer decide. Never change Figma.
- A storyboard frame is a still: it shows the state at that moment, often the final one. Animate the states that lead
  to it as the product does (e.g. a Copilot frame showing "Show steps ⌄" is the folded end, not the loading).
- When in doubt about a behaviour, look at the live product (a signed-in browser, looking only) and measure: states,
  order, transitions, whether a hover is instant.
- The design can beat real life when asked: an autofilled field without the browser's blue, "even if it isn't how it
  would be in real life".
- If the storyboard leaves out something the product has (the action bar under the AI's answer), it may be on purpose,
  for a cleaner video: don't add it on your own; at most, ask.
- In a piece with its own Figma, the cursor (colour, size) and the details come from that Figma, not from the house
  default.

## 3. Cursor (the current recipe)
- One path (Follow Path) per task, with few keys: only where it stops (a press) or where one curve hands over to
  another at the same speed. Never a landing at a turning point, in a creep or in a "breath".
- **Never the entry curve on every leg:** it lands every ~0.5 s and reads "stuttering, super buggy".
- **It appears and vanishes in place:** a 3 f fade, already moving, below the first target (~200–250 px), on the side
  towards the centre of the frame, never crossing the edge; it fades out in 3 f, 5–9 f after the last press, still
  landing. **Overrides MOTION.md:** the cursor enters and leaves through the edge and never appears or vanishes inside
  the frame.
- Entry (from appearing to the first target): ONE curve (0, 0, 0.2514, 1) over ~38 f: it leaves at ~19 px/f and lands
  long.
- From press to press (the wait while text types included): ONE curve (0.6, 0, 0.25, 1), 50–85 f, with no key at the
  arc's turn. A move from rest takes about 0.85 s + 1 ms per px. **Overrides MOTION.md:** `cursor.move_ms` =
  clamp(450 + 1.4·d, 550, 900) and the symmetric (0.6, 0, 0.4, 1) "look mechanical".
- The press starts 5 f before it stops (7 f on a field); the next move leaves 2 f after it stops. The cursor presses to
  0.85 in 3 + 3 f, linear (4 + 4 f on the motion designer's newer cursors).
- The path starts at 0.1 % and ends at 99.9 %, never at the exact ends, and the last key is hold. At the exact ends
  Follow Path draws the cursor at the other end of the path for a frame; a linear last key makes it slide back at the
  loop.
- Check the tip's speed frame by frame: one peak between two presses. The ceiling is 2.4 % of the frame's width per
  frame (~31 px/f in a ~1300 px frame; in a camera zoom, against the zoomed interface); approved peaks sit at
  18–26 px/f. It holds for every cursor, one drawn by hand too: the library's build checks them all.
- A long wait: it doesn't park, and doesn't leave the frame to come back; it glides slowly to the next target
  (~12 px/s), or it vanishes at a cut and another cursor fades in (3 f). **Overrides MOTION.md:** "for longer waits, it
  leaves the frame".
- It doesn't leave the screen between consecutive actions of one scene; the tip stays ≥ ~65 px from the bottom edge.
- Path shape: a light arc (~8 %) that already rises towards the target. Rejected: a C-shaped hook leaving a list that
  just opened, an arc that dips before rising, a scroll that stops and comes back 20 px.
- Picking an option in a list: a pause (a creep on the field, never still), then a short, direct drop to the option.
- On its way, it doesn't pass over other fields or targets; if it does, the target lights up (as the product does)
  while the tip is inside.
- The detour while text types goes to the empty side: with chips or controls under the text, it goes up.
  **Overrides MOTION.md:** the typing arc always bulges below the text.
- Size and colour follow the piece's Figma. Without one, the default: a blue arrow with a ~22 × 25 px fill in a
  1260 px frame (as in Duda's "Get Found" video); 155 % of that was too big. On the press, keep ~80–85 %.
- In a camera zoom, the cursor grows with it, in proportion to the interface (keeping its screen size was rejected).
- A cursor that drags (a file, a block, a widget) turns into the closed grabbing hand on the frame it picks the item
  up: a hard swap, no scale (the closed hand is the press). It disappears in place on the drop. Full recipe: 19.1.
- When the motion designer moves the path's points in the editor, the Follow Path percentages break (it only knows
  distance as a % of the whole path): measure in px, refit the values and handles, and keep their points so the build
  reapplies them.
- Before delivering, check that no Motion path was left visible (a red stroke on screen).

## 4. Hover, click and reactions
- A hover lights on the frame the cursor's tip or middle enters the target and goes off when the cursor leaves,
  measured on the render (the tip = the blue pixel with the smallest x + y). **Overrides MOTION.md:**
  `cursor.hover_lead_ms`, 150 ms before the press, "reads as a bug".
- No hover during the cursor's 3 f fade; if it is born inside a field and leaves within 2 f, no hover at all, so the
  edge doesn't flash.
- The product's dropdown: the option under the pointer gets its fill (#F6F6F8) at once, with no transition; every
  option the tip crosses lights up, not only the clicked one.
- The control's press: 0.9 on an icon button, 0.96 on a wide button, 50 ms in and ~333 ms to release (`duda`), about
  the control's own centre (an icon in a frame-sized box "jumped" when it shrank from the corner). List rows don't
  squeeze: the highlight is the reaction.
- A popup, modal or menu that the click opens starts on the release (~8 f after the press), not on the press: on the
  press it reads as "arriving before the click". **Overrides MOTION.md:** "the result appears on the press frame".
  Decided 2026-11-23: the same for a colour picker or any selector, even where an approved piece (design-with-context)
  opened one on the press.
- A button that changes colour keeps its shape.
- When the motion designer retimes the cursor, move the interface's state keys with it: each state at the start of
  their press, the hover where the tip enters, the hover off when the cursor vanishes.
- A background that appears with a list (a band behind the rows) comes in solid and still; only what is born on it
  fades in (a fading band showed lines through the checkboxes).
- Approved polish on the controls: a toggle in 250 ms, its knob stretching midway and the ✓ drawing itself; a checkbox
  with the box at 88 % and the ✓ drawn; a modal from 0.96 to 1, rising 8 px, in 767 ms `settle`; a menu dropping 4 px
  in 100 ms, its options 17 ms apart; a chevron turning 180° in 250 ms.

## 5. Typing in fields and prompts
- No blinking caret while typing.
- The Copilot's prompt: the placeholder goes on the click, the field stays empty until the typing, and the placeholder
  doesn't come back after sending.
- A prompt: the cursor clicks the field and vanishes; the text types in over 84 f on the curve
  (0.1804, 0.0442, 0.2292, 0.676), 9 f after the click; the send button presses on its own. **Overrides MOTION.md:**
  the Duda typing pattern (drift aside, swoop to the next control) for a prompt.
- Sending: the typed text rises 10.3 px in 45 f (0.8, 0, 0.2, 1) and fades out between +16 and +26 f; the message comes
  in at +23 f. **The sent message, always:** it rises 20 px in 30 f (0, 0, 0, 1) and appears over 5 f (linear), both
  starting on the same frame, and "Thinking..." comes with it. When the piece opens on the message already sent, that
  frame is f0.
- Typing is one cubic key on the number of letters shown (it takes fractions), not one key per frame. Text that is on
  screen too briefly doesn't read: the motion designer asked for +20–30 f "to make the text readable".
- The letter at the edge of a fractional count fades in over that one letter (a hair of it at .25, half at .5): never
  a half-drawn caret, never a letter flashing in and out. Check the typing at 5× on a frame in the middle.
- A prompt's send presses on its own ~45 f after the last letter (the approved Marketing Automation hero).
- Forms: the cursor clicks EACH field ("the cursor should be on the relevant fields while typing"), the text types in
  and the cursor arcs to the next control, arriving as the last letter lands.
- Never squeeze the cursor to fit a time: 3 fields in 3 s looked "stuck, not natural at all"; ~1.45 s per field is the
  minimum that reads human.
- All fields at the speed of the longest one (~14 letters/s, starting 0.15 s after the click); a short name spread over
  the whole window is too slow. A name that has to read as "typed": ~2.5 f per letter.
- A placeholder in a website form stays on focus and goes on the frame of the first letter, as in a browser.
- A form with many fields: clicking each one is "repetitive". The cursor types only the start of the first (3 letters),
  accepts the browser's autofill suggestion, and the other fields fill in a cascade (3 f apart, 4 f fade). With few
  fields, click each one.
- Code written by the AI: three copies of the text with a per-character modifier, magenta #F100FF underneath, purple
  #B36DFF at the tip and the syntax colours coming in behind on a ramp; no caret; remove the purple and magenta at the
  end.

## 6. The Copilot and the AI's answers
- **The panel fits the frame:** the "Reply to Copilot" field stays whole inside it, pinned to the panel's foot with the
  Figma margin (~12 px), its "+" and send button visible. If the artboard is shorter than the Figma panel, the
  conversation area shrinks; the field never goes past the edge.
- **The send button:** grey #C9CACD while the field is empty, orange from the first letter (a hold key), the orange
  stop while the Copilot works; at the answer, with the status swap, the stop fades out (0.1 s) and the grey send fades
  in after it (0.1 s), the field's edge back to rest. The field is the product's: only "+" and send at its foot.
- Status: "✦ Thinking..." comes in with the message and stays still under it, for the whole loading, even when the
  Figma frame shows "Show steps ⌄". When the answer starts, it swaps in place for "Thought for Xs ⌃", without the star.
- The status's timing: the star 5 f after the message, turning 60° and rising 8 px in 35 f (0, 0, 0, 1), appearing in
  7 f; the text wipes in 15 f later; a shimmer with a 37 % band every 1.6 s; the swap starts 9 f before the answer and
  the chevron comes 24 f after.
- **Steps (the storyboard's ✓ rows):** each row opens its space (0.25 s, `duda`) and comes in rising 4 px (opacity in
  9 f, y in 20 f), its text dark from the start, with no shimmer. The loader is **the classic turning spinner, never
  the sparkle, even when Figma draws the sparkle**: an open arc of 270° (~10 px in a 13 px icon), a ~1.2 px stroke with
  round caps, one colour as a trail (#272B35 from 100 % to 12 %, the full end leading), turning linear and clockwise,
  one turn every 0.8 s. End of a step: the loader fades out in 3 f, still turning; the ✓ comes in over the next 3 f;
  the next row comes in when the ✓ is done. **Never the loader and the ✓ on the same frame**: check it zoomed in,
  frame by frame. The "✦ Thinking..." above keeps its star. Wrong: a coloured sparkle standing still + grey text with a
  shimmer. **Overrides MOTION.md:** the loader fades out in 100 ms and the check draws over 300 ms; the active step's
  text shimmers.
- **The generation happens during the loading:** the big wash starts right after the message is sent, with
  "✦ Thinking...", not at the step that "talks" about design (e.g. "Designing the layout"). The steps follow the
  generation's pace: the last ✓ comes in as the last detail settles, and only then the answer. No loader spins alone
  for seconds waiting for the generation. Steps take different times (in the product, 0.2–4 s). Recipe: 19.2.
- The real product, for reference: Thinking → each step comes in with a spinner and turns into a ✓ (✗ when it fails) →
  "✦ Working..." under the rows → it all folds into "Show steps ⌄". The star is never on a step's row.
- The action bar under the answer (copy + "⋯"): 24 px buttons, 16 px icons in the secondary colour, 6 px apart, 12 px
  under the text; it comes in over 0.15 s, 0.3 s after the answer starts.
- **After a generation, the answer always comes**, even on a small card: never end on "Thought for Xs" alone. ~25 f
  after the last ✓ the status swaps and the steps fold away (0.1 s out, their rooms closing over 0.25 s, `duda`); 21 f
  after the swap the answer comes in their place as a plain typewriter: each letter whole, ~120 letters/s and never
  longer than ~1 s in all (a long answer types faster), no soft front, no feather, no colour pass (it is the chat, not
  the generated design); its action bar 0.08 s after the last letter. (On the small card of 19.2 the steps folded 21 f
  after the swap and the answer came 8 f later: both read well.) Wrong: a soft front at 75 letters/s ("type it faster,
  no feather, a normal typewriter").
- A Copilot (or any panel) that stays while the rest changes screen: no match cut with the rest sliding and the panel
  still ("looks buggy"); go through white in place (section 8).

## 7. The generation effect (AI)
- **The mother rule:** where the interface has blocks (cards, buttons, bars), each block is born from a gradient
  block; loose elements appear with colour + feather; inside the blocks, the elements also come in with colour +
  feather; numbers count up and end slowly.
  - **When:** it starts with the Copilot's loading (right after the message is sent), never after it (section 6).
  - **Top to bottom, big to small:** first the gradient wash over the whole screen; then the blocks in reading order,
    top to bottom (left to right in a row), one after another with a gap; each block's texts and icons come in as it
    shows, not after the whole screen (they may overlap the next block's start). Never all at once, and never the
    biggest block first when it sits lower ("first the elements on top, then the ones below them"; recipe: 19.2).
  - **A block that sits on another block** (a badge on the hero photo) is generated with it, as one of its rows
    (rising 4 px as the parent shows), never with a ~1 s slot of its own: in a blind test that slot pushed the lower
    block, the steps and "Thought for Xs" 53 frames late.
  - **Colours:** the classic gradient (below) by default; the design's own gradient when it has a visible one.
- **The default (classic) gradient** (measured in a Duda hero, the homepage's): 7 stops, #DDF1F9 transparent (0) →
  #DDF1F9 (.162) → #E6D7F1 (.336) → #F4BBD2 (.503) → #F9A84A (.681) → #F0CE72 (.848) → #F0CE72 transparent (1); the
  band at ~70°, from top left to bottom right, yellow leading; every pass on the curve (0.588, 0, 0.377, 1).
- **The design's colours:** if the screen has a gradient with its own colours (a background, a card, a button; any
  gradient counts, not only an "AI" one), the generation copies it and uses its colours everywhere: the wash, the blocks
  and the text's colour pass (in place of the orange and pink). Slightly stronger than in the design, so they show over
  it, with a middle tone between its two ends. On the welcome email (background #FFFBD6 → #DCEBFF): wash #FFF3B0 → #FFE8A3 →
  #E3E0F4 → #B9D2F6 → #D6E4FB; the photo's block #B9D2F6 → #C8DBF8 → #D6E4FB → #DDDFF7 → #E3E0F4; the lower block
  #FFE8A3 → #FBECB6 → #F6EFC8 → #E9EADF → #DCE6F6; texts #907EF1 → their own, and on the details #F8CD4F → #907EF1 →
  their own. Wrong: the default colours over that email. No gradient but a client palette: the design's colours in
  place of the defaults, at the same strength. **What counts is a gradient you see in the design.** A flat colour band
  (an email's yellow strip), a gradient hidden under the frame or the storyboard's "Generating" blobs don't count: use
  the classic one ("use the classic gradient colours, the homepage's"). In doubt, the classic.
- **The wash** (the anticipation over the whole area): at 50 % over white, scale 110 %, sweeping in 217 f (3.6 s) on
  (0.588, 0, 0.377, 1), feather 20 → 3. Over a cream background: a cool front and 75 % (at 50 % the blue turns grey).
  **Overrides MOTION.md:** the `gradient` sweep, (0.6, 0, 0.4, 1) over 1.5–2.7 s.
- **A block always covers its component with room to spare:** 5 px more on every side and the component's radius + 5
  (a square corner gets radius 5). At the exact size, the block's soft edge and the edge's anti-aliasing let the
  component show through: dark dashes around the block, on a photo's edge ("strange edges around the gradient"). Check
  the frames where the component lights up under the block at 5×.
- **A block:** a rounded rectangle over the component, with that room; scale 1.08 → 1 on cards (31 f) and
  1.02 → 1 on panels (45 f), linear; feather 11 → 2 on cards and 10 → 1.5 on panels (lighter than hero_1's 18 → 3: in
  every hand edit the reviewer lowered it, to ~0.6×; settled on 2026-11-23 for every piece), each block's first feather
  a little different from its neighbours'; a panel's block fades in over 12–20 f (it shouldn't appear whole); the pass
  84 f on cards, ~131 f on panels. The component under it doesn't move position (what's inside it
  can); its content comes in while the block settles, starting ~0.4 s after the block shows (sooner, it lights up
  hidden under the block). Vary the rhythm between blocks, so it doesn't look robotic. This base stays: add detail,
  never replace it ("you ruined the piece... it was much better before").
- **Feathers follow the size the piece is shown at.** The feathers in this section are for the 1340 px heroes; on a
  small card they blur too much ("the artboard is small: make every feather smaller, mainly the gradient squares'").
  On a 432×264 card: the blocks' at ~65 % of the above (a card's 11 → 2 becomes 7.2 → 1.3, a panel's 10 → 1.5 becomes
  6.5 → 1), the wash's at half (10 → 1.5), texts and icons 2 → 0. In between, scale by the width the piece is shown at.
  Decided 2026-11-23: this holds for every piece of that size, the new ones and those made again: at 772 px the wash
  goes 13.7 → 2.1 (an approved piece of that size had 20 → 3).
- **Texts and icons the AI generates** (loose or inside a block) change colour as a whole: in the classic gradient's
  orange #F9A84A from the start, its pink #F4BBD2 over 10 f after max(0.35 s, 60 % of the text's entrance), held 8 f,
  then their own colour over 20 f, linear; feather 4 → 0 over 40 f (2 → 0 on a small card). With the design's
  gradient, its tones (above). Wrong: purple texts on a classic generation ("use the classic generation colour on the
  texts too, not the purple"); a coloured band or gradient running ahead of the letters, from two copies of the text
  ("not that running gradient, but a colour change on the whole text, as in the hero").
- **How a text comes in:** copy on a generated page or email (headings, paragraphs, a tagline, a banner's letters)
  comes in letter by letter ("a gradual appearance: text modifiers, opacity"): opacity per character with a soft front
  ~6 letters wide, ~45 letters/s, 0.4–0.9 s a text; a two-line heading line by line. Short labels on interface blocks
  (a node on an automation map) come in whole: opacity over 8–20 f, blur 6 → 0 over 54 f. Icons and logos: opacity
  over 20 f, with the texts' colour and feather.
- **Loose elements** (logo, menu, avatar, a name that gets edited later) have no block: they come in as above, at
  their place in the top-to-bottom order. **Overrides MOTION.md:** fades ≤ 167 ms.
- **Inside the blocks:** texts as above (small captions may wipe in from the left); numbers #AE68FA → their own, with
  feather 4 → 0, in 26–41 f; bars #AE68FA → their colour. **Photos** settle inside their frame: 112 % → 100 % over
  1.5 s on (0.16, 1, 0.3, 1), from just before they show under their block (~50 f after it starts); the frame doesn't
  move. No small item pops in from one frame to the next: texts, icons, numbers and photos come in with at least an
  8 f fade, in that colour and feather.
- **Order and gaps:** the wash → the blocks top to bottom (cards left to right), each block's texts and icons as it
  shows; irregular gaps (7–16 f between cards, 2–4 f between loose items). On a screen the Copilot generates, with a
  few big blocks, the gaps are longer (~1 s between blocks; ~0.5 s on a small card, 19.2).
- **Numbers:** count up to the value on (0, 0, 0, 1) or (0.045, 0.122, 0.377, 1), over 1.5–3 s, starting fast and
  ending slowly, with a glow (blur + purple) while they count; keep the count visible (in the reference, the KPIs are
  already ~90 % counted when their card shows). **Never count from far** (e.g. 0 to 3,023 in 1 s): with a big gap the
  count looks un-eased, however soft its end. Start at the final value minus a random ~10–35; if the value is small,
  shrink the gap so it never goes below 0. The library's `a.count` does it by default.
- Charts: the line by a trim path + blur 5 → 0 in 40 f; the body (0, 0, 0, 1) under a lavender layer at 50 %, no fade;
  the donut on the `duda` curve; the donut's and the line's peaks together.
- Don't stack the storyboard's own effect (blobs, breathing placeholders) with the blocks: keep only the blocks.

## 8. Cuts and transitions between screens
- Pick the cut by what happens: a page that changes sideways = a match cut by position; a click that "goes into" a
  block = zoom in + white; a panel that stays = white in place. Zoom only where the click goes into the thing clicked.
- A match cut by position: it starts 7 f after the click; the exit travels 215 px in ~23 f (1, 0, 1, 1); the entry
  comes 60 px, settling in 54 f (0, 0, 0, 1). 40 px looked like a jump, 20 px was "really harsh". **Overrides
  MOTION.md:** the exit starts on the press frame.
  Decided 2026-11-23: 215 / 60 px is the default for every sliding cut (the motion designer's other cuts measure
  ~57 / 35 px; that doesn't change the default).
- A discreet swap (a hero's tabs): the old screen leaves towards the opposite side in 20 f / 26 px (exit), the new one
  comes in from the tab's side in 26 f / 34 px (settle), the entry larger than the exit. **Overrides MOTION.md:** exit
  400–600 ms, entry 700–1000 ms.
- A zoom cut with white: the screen goes to 120 % around the click point in 23 f (1, 0, 1, 1), starting 14 f after the
  click (135 % before 2026-11-23, when the motion designer settled on 120 %, the rest unchanged); white comes in over
  9 f, full from the cut −1 to +3 f, and leaves over 15 f; the new screen comes in from 95 % and settles in 54 f.
  **Overrides MOTION.md:** the pivot at the centre, 110 % / 93 %, no white.
- In a zoom cut, put the landing pivot where a gap would show least, and extend the edges on every side the 95 %
  landing uncovers; a fixed header the zoom covers goes back to its place hidden in the white.
- White in place (a panel that stays): 7 f after the click, the screen leaves in 0.15 s, 0.1 s of white, the next comes
  in over 0.25 s; never both at once. **Overrides MOTION.md:** a hard cut with no fade.
- What shows past the frame in a cut has to continue the screen as the piece draws it: copy from 5 px inside, start 2 px
  before the edge and cover the whole exit (~230 px). A band of another colour was rejected.
- A jump cut (so a hard cut isn't "totally hard": the loop's seam, the cut into a close shot): the whole picture
  slides ~23 px in 27 f (1, 0, 1, 0.9554) and the next comes in ~30 px on with the slide, settling in 34 f (60 px from
  the other side in marketing-automation v15.12; 30 px on with it in ma-novo v18.5-v18.7); "the goal is not even
  noticing it moved". At a seam he also cut on the peak of an 84 f 80/80 (ma-novo v18.9). Px on screen.
- Parts that exist on both sides of the cut (a header, bars) must be identical, or "something jumps on the swap"; use a
  single frame on top.
- The cursor at a cut walks across it when its next move comes within ~2 s of the cut: he kept it walking at 1.37 s
  (marketing-automation v15.12, cut 1), 1.38 s (design-with-context v04, the zoom) and 1.55 s (manage-hero2).
  Otherwise it vanishes in place before the exit starts: a 3 f fade from 8 f after the press (never before 5 f, the
  press's release), as when nothing came for 3.6 s (marketing-automation v15.12, cut 2) or nothing came at all
  (build-your-audience v03); the next cursor comes in after the cut, never across the old screen. Following "always
  vanish" left 100 f with no cursor (the design-with-context blind test). `a.cut` decides it and the build says
  which. **Overrides MOTION.md:** the cursor flies off the frame before the cut.

## 9. Camera and zoom
- No constant slow zoom or drift on the product's interface. Only the background (a photo) breathes, there and back
  over the whole loop (1 → 1.04 → 1), so the loop closes; with no photo, the background stays still. **Overrides
  MOTION.md:** "the camera never stops".
- A zoom into part of the scene only when the motion designer or the design lead asks. Then: a hard cut to the close
  shot (2–2.5×) in the middle of the cursor's run, ~31 f before the click, and the camera follows the cursor with the
  cursor's own easing until it meets the UI's limit (`a.camera_close` / `a.camera_open`). **Overrides MOTION.md:** "never zoom into part of
  the scene".
- In the close shot, only interface: lock the framing to a corner of the window so it never shows what's outside the UI
  (sky, the card's edge).
- Back out: a slow, gentle zoom out in the close shot (2.5 → 2.4, curve (0.65, 0, 0.8, 0.7)), then the strong 80/80
  zoom out; the strong one starts at the speed the slow one ends, so the two read as one.
- An editable camera: the card inside a `CAMERA` node with a Transform constraint named `CUT` aimed at a rig (where the
  cursor is > zoom > track); the `CUT` strength (hold 0 → 1 → 0) is the cut, and its two keys can be dragged (`a.camera_close` builds it).
- The camera's track in ~12 cubic keys fitted to the movement (error < 1 px), never one key per frame.
- Rounded corners only in the close shot; when the way back is a zoom out, the radius gets keys along with `CUT`, or the
  corner turns square all of a sudden.
- A zoom out shows what was outside the frame (a cursor parked outside the card): hide what has already left.

## 10. Entrances, lists, scrolling and swaps
- A new screen's content comes in as a cascade after the cut: each row rises 8 px and appears over 0.6 s `settle`,
  67 ms apart, top to bottom (`a.cut` does it). The movement may start 0.1 s before the fade.
- The cascade goes on what the click opened (the template's email, row by row, with what sits over it in its row: a
  selection, its label, its toolbar); the frame around it (bars, panels, the canvas) comes in whole (design-with-context
  v04; a blind test cascaded the panel's rows instead).
- A new row in a list opens its own space first (0.25 s, `duda`) and only then appears; nothing pushes text in a single
  frame.
- The DS toast: it comes in dropping 8 px over 0.5 s `settle`, stays, and leaves rising and fading over 0.25 s `duda`;
  top right, 24 px from the top bar and from the right.
- Scrolling: one move, never coming back (a "weird jump" when it stopped and came back 20 px); the curve
  (0.857, 0, 0.242, 1); ~784 px in 124 f (2.1 s) peaked at ~23 px/f, ~0.9 s + 1.5 ms per px over his five scrolls
  (`a.scroll`). **Overrides MOTION.md:** `ease.scroll` (0.6, 0, 0.4, 1).
- The top of a screen that is going to scroll stays readable ~1 s first. The screen scrolls on its own and the cursor
  appears 6 f before it ends.
- An element that rises as it arrives is clipped to its own space (a photo once slid over the block next to it).
- Dragging inside a product map (the automation flow's blocks), as the product does: the block follows the pointer with
  a larger shadow, no scale or rotation, a copy at 40 % stays in place, the drop targets' "+" turn blue; dropped far
  away, it snaps back. Anything else dragged (a widget, a file, a card): recipe 19.1.
- Colour or position ramps don't sit still and then finish all at once, and no title drops before rising (a y key on
  f0).

## 11. Timing, rest and loops
- A motion that loops on a page (a hero, a loop): ~3 s still on the last frame before it starts again, so the page
  isn't "polluted with motion"; a 2–3 px breath in the background keeps it from looking frozen. **Overrides MOTION.md:** a seam hold of
  ≥ 8 frames.
- A piece that a carousel or a tab switch cuts: `MAIN` lasts exactly the tab's length (the current carousel switches
  every 12 s, 720 f). Change the length only by stretching the still last frame, without touching the story or the
  cursor.
- In the email carousel (12 s) the story ends around 5–5.5 s and the rest stays still: the approved ask-your-agent is
  still from 5.53 s, design-with-context's last action is at 5.2 s (6.8 s still); the 12 s came from adding the still
  end to 9 s pieces. The "~3 s still" above is for a hero or a loop, not a carousel tab: following it, a blind test
  filled 8.4 s with the story.
- In those pieces, no white at the start or the end: f0 is already the first screen; the carousel does the switch.
- A carousel piece with a Copilot opens on the send: the message comes in at frame 0 (in over 5 f, up 20 px in 30 f),
  as in the approved ask-your-agent; f0 is the editor with the message arriving, never a bubble already sitting still.
- A piece that opens in a website tab is already moving on f0 (the screen still arriving, say), so it doesn't look
  frozen. (Opening on a scroll was turned down; use another movement.)
- A rushed start gets rejected ("that start is way too fast"): stretch the start and take the time from the rest at the
  end.
- A message that has to be read stays whole on screen for ≥ ~1 s.
- Measure the loop's length in the `.riv` itself, not in the brief: find the L where frame L + 10 equals frame 10.

## 12. What the reviewer rejects (check before every delivery)
- "Jumps": a control that shrinks from its corner; a scroll that comes back; a title that drops before rising; parts
  that change place between two screens; a match cut that travels too far or too little (sections 4, 8, 10).
- "Stuttering" / "buggy": a cursor landing on every leg; a cursor squeezed into a time; a ramp that waits and finishes
  at once; a panel standing still while the rest slides (sections 3, 5, 6, 8).
- Edges: a light line on an image's edge, a band of another colour in a cut, a grey block at the end of the loop, a
  card's edge showing when the window is offset, a panel's field cut by the frame, dark dashes around a generation
  block the exact size of its component (sections 6, 7, 13).
- The cursor vanishing or flashing: Follow Path at 100 %, a fade in the middle of a hover, a cursor that vanishes right
  on the click (section 3).
- Two states together: the loader and the ✓ on the same frame; also check that the placeholder and the first letter
  swap on the same frame (sections 5, 6).
- Lack of sharpness: any interface as an image ("I'm missing sharpness in the UI... don't do that!").
- A change that moved what wasn't asked: run `scripts/keydiff.py` against the version they saw, with `--expect` naming
  what you changed; anything else it lists is a regression.
- An item appearing dry on one frame (no fade); the storyboard's effect stacked on the house one; a generation that
  waits for the loading to end or comes in all at once (section 7).
- A generation that doesn't read as the house one: the hero's feathers on a small card; purple texts, or a band
  running ahead of the letters, on a classic generation; the lower block first; a design's flat colour taken as its
  gradient; a generation that ends with no answer, or an answer with a soft front (sections 6, 7).
- No hover with the cursor already over the target ("isn't there a hover here in the product?").
- Before saying an edge or line fix is done: `scripts/edges.py` renders the key frames at ~5× and lists the lines on
  image edges, clips and seams (sheets in `build/edges/`); for the area the reviewer marked, add `--region` and, with
  their screenshot, find their zoom. They once had to ask 3 times for the same line.
- The editor's preview draws between frames: check scene swaps in quarter frames; a linear 0 → 1 opacity between f0 and
  f1 showed half a frame of photo.

## 13. Edges, seams and images
- An image's edge is never sharp in the editor's zoom: cover it with a vector band in the background colour that goes
  ≥ 1 px into the image (say 4 px), never a 1 px seam exactly on the edge. `scripts/edges.py` finds these lines (and
  seams between blocks that meet at a fraction of a pixel); run it again after the band.
- Figma exports carry lightened edge columns and lines the piece doesn't draw; don't copy the last column to extend the
  screen.
- A divider under 1 px comes out lighter in Rive: use 1 px.
- Figma's SVG leaves out one-sided borders and draws text letter by letter; grain (Noise) doesn't turn into vector: say
  so and propose a tile or a still grain.
- The code in Figma's design context can get a text size wrong (36 px in the code, ~50 px in the frame) and carries
  hidden layers: measure on the frame's PNG before trusting it. `scripts/compare.py` measures every text of 20 px or
  more against the frame (ink width, `TEXT` over 3 %).
- A short line height (= the font size) shifts text in Rive by 1.7 to 5.7 px from Figma: measure the ink on the frames
  and compensate.
- Duda Sans has no tabular figures: changing a digit pushes what follows by ~0.5 px.
- Pose check (`scripts/compare.py`, all poses in one call): a mean difference ≤ ~12/255 per frame and no area with
  more than ~4 % of its pixels off by > 40 (the mean hides a missing icon), the big texts within 3 % of Figma; then look
  at the overlays. A high difference only from a Figma P3 photo vs sRGB, or from grain, is acceptable when explained.

## 14. Delivery
- Interface in vector; only real photos stay images. On the site, a `.riv` is used instead of a video because it is
  sharp at any zoom and light.
- An approved exception: a part that only moves or goes as a whole, and weighs on the editor, becomes a 2× image drawn
  by Rive itself, in a nested artboard (a "plate"); what animates inside it stays vector. Warn that above 200 % in the
  editor the image shows.
- A `.riv` (and its `.rev`) as light as it can be at good quality: only the library components the piece uses, images
  in WebP by kind, done by `slim` (photos lossy Q 90; avatars, UI captures, transparency and flat images lossless;
  `p.image(quality=)` for one image), fonts subset to ASCII + the scene's letters keeping the default features
  (ligatures), no unused font, unreachable artboards and view models pruned, the part of a photo that is always covered
  flattened. A piece carrying the whole library and PNG photos weighed 2.7 MB; pruned, ~0.2–0.3 MB.
- The editor's export re-encodes each image by its ImageAsset's `format`: `slim` writes it (webp 0.9 for a lossy
  image, png for a lossless one), or the WebP doesn't reach the final `.riv` (1.7 → 2.4 MB). Don't patch it by hand.
- A subset font: warn that text edited in the editor with a new letter comes out without that letter.
- A production MP4: `scripts/render_mp4.py` (every frame at 2× with `--fit=contain`, 1 ms past its time, 60 fps,
  x264 slow, CRF 12, yuv420p, BT.709, faststart), from a project whose `.riv` is identical (`cmp`) to the site's; look
  at the sheet of frames it reads back from the MP4.
- Performance on the site: the weak point is the graphics card (~500 draws a frame), and what weighs most is blur
  (feather) and text as outlines. Measure before and after; nothing changes without the motion designer's OK.

## 15. Interactive pieces (state machine listeners)
- An interactive website card (a section driven by the mouse): it plays once when it appears and stops on the Figma
  frame; no loop and no fake cursor; the visitor's mouse does the interactions.
- A hit area: a rectangle with a 0 % fill in a node on top of everything; a transparent fill still gets the mouse.
- One state machine layer per item, states off / on as 1-frame poses and a 150 ms transition; enter / exit listeners
  write a boolean in the view model; a click = a "click" listener.
- The hover's layer animates another node, never the property the entrance animates; otherwise the two fight and the
  later one wins.
- What the mouse triggers and moves in the entrance's drawing only runs after the entrance (locked by an "introDone"
  boolean).
- The hand cursor: a "cursor" text property in the view model ("pointer" / ""), bound to the CSS by the page. Two areas
  the mouse crosses in one move: copies with only the exit on top, because the runtime processes front to back.
- A loop's speed driven by the mouse with no script: `speed` bound to a view model number through a
  DataConverterInterpolator (0.5 s cubic), to stop and resume with no jump.
- On a phone there's no mouse: the entrance alone tells the story, or the section uses an image.

## 16. Rive pitfalls (editor and runtime)
- A group's or nested artboard's opacity applies layer by layer: fading a scene out shows what it hides underneath. On
  a flat background, make it go under a veil in the background colour, on top. The build notes a box held
  half-faded ([layoutfade]).
- Content over white that leaves: first the content fades into the white (0.08 s), then the white alone (0.12 s).
- To change only part of a text (the number in "All contacts (1,283)"): split it into runs and fade only that run with a
  TextModifierGroup with `invertOpacity`; without `invertOpacity`, only that part shows.
- Time remap: `time` is a 0–1 fraction and the timeline oneShot; a remap whose `time` never changes doesn't apply (use
  0.0001); never shift keys by an epsilon.
- Scenes in precomps: each scene starts 1 f before the cut, hidden, and the swap goes 1 f after the cut (on the cut
  itself it gave a blank frame); each scene's entry key is born hold.
- `MAIN` with a remap: `MAIN`'s length = the remap's end = the piece's length. Shortening a remap's end in the editor
  compresses the whole artboard (the fields drift away from their click).
- Sections switched by the state machine (tabs in one `.riv`): a click while the section is still swaps with no mix; a
  133 ms mix blended the frame and the cutout, and the window flashed transparent. Mix only in the middle of a pass,
  with early exit on.
- An artboard played directly in the editor is slow; the same one nested in a `MAIN` plays smoothly. A heavy piece that
  stutters: nest it before hunting masks.
- The editor freezing: screens from Figma's SVG become tens of thousands of objects (text as outlines). Use native text,
  one per line; remove masks that don't cut anything off; set off-scene screens to display none. ~25 thousand points
  opens fine. The build notes it: [weight] (objects per artboard), [outlines] (letters as paths), [offscene] (a screen
  hidden by opacity but still on).
- A Feather on a fill (text, a layout box) only draws with `fillRule="clockwise"`.
- An Image inside a LayoutComponent only sizes with a LayoutParticipant; better to place it by its centre with a scale.
  A ClippingShape inside a node once cut a sibling.
- Draw order: in RML and in a layout box, the first child is in front.
- An enum starts at its first value and the layers bound to it fire on f0: avoid enums, or add an empty escape state.
- An icon colour written by a state machine layer shows right on the site and in the CLI but not in the editor: write
  the starting colour on each instance.
- With autoBind (the site), a nested component's triggers come from the state machine bound to the view model, not from
  fire keys on the timeline; the CLI doesn't show the problem, only the web check does.
- The Finder's QuickLook doesn't bind the view model: a component "without bindings" there is right on the site, in the
  CLI and in the editor.
- Test on the runtime version the site really uses: an embed on 2.39.x broke scenes that were right on 2.45.0.
- The runtime respects the work area set in the editor; over `file://` the `.riv` doesn't load (serve it over http);
  images decode after onLoad, so wait ~2 s.
- Headless Chrome chokes requestAnimationFrame: to check timing, replace the clock with a fixed 1/60 s step.
- The editor keeps numbers with every decimal; when copying its keys, write ≥ 8 digits (4 decimals misalign handles and
  paths). Edit the motion designer's RML as text, never rewrite it through an XML parser.

## 17. Rive CLI pitfalls
- CLI 1.9.2 (the server refuses older ones): frame N is `--advance=N`; `--once` is gone; `--verify` checks,
  `--rev=<file>` exports the `.rev`; `--commands` takes hundreds of captures in one build.
- A CLI capture taken on a whole frame shows a hold key one frame late, and `advance 0` (or none) is the setup pose,
  not frame 0: take each frame 1 ms past its time (`advance 1ms` first). `render_mp4`, `compare`, `edges` and the
  build's `--stills` do. In the editor it falls on the right frame: don't move the keys.
- A `.riv` from the CLI only comes out of `--publish`, and on the free plan it is watermarked and spends one of the
  month's publishes. A clean `.riv`: the editor's Export for Runtime.
- Never run `rive push` or `--publish`: both upload to the user's Rive account.
- To read someone's file: `rive create <folder> --from-rev=<file>` or `--from-remote-file=<id>` (read only; take
  `push:` out of the copy's `rive.yaml`) and compare by id, with a tolerance on the numbers.
- Don't build during an MP4 render: the render reads the scene frame by frame and mixes versions. `render_mp4` stops
  if scene.rml changes while it renders.
- An extra `.rml` in the project folder goes into the build and breaks it silently: keep a copy of a scene as
  `.rml.txt` or `.xml`. The build now fails on one ([rml]).
- If a file changes on its own while you work, someone is editing it: stop writing and ask.

## 18. Where the library still differs from these rules
- The generation (`a.generate_screen`, v14) follows section 7. Not automatic yet: small captions wiping in from the
  left, and bars inside a block tinted #AE68FA (section 7, "Inside the blocks"): build those by hand. The small card's
  later fold (19.2: the steps fold 21 f after the swap) is not the default: `a.reply` folds with the swap.
- Cuts and camera (`a.cut`, `a.camera_close`, v14) follow sections 8 and 9. Not automatic yet: the rounded corners
  of the close shot keyed with `CUT` (section 9); hiding what has already left before a zoom out shows it (section 9);
  a fixed header the zoom covers going back to its place in the white, and one frame on top for parts that exist on
  both sides of a cut (section 8: build those by hand); the zoom's landing pivot is the click point (`at=` moves it
  where a gap would show least). Edges are copied only where a screen reaches its clipping box, and not for a screen
  inside a scaled box.

## 19. Action recipes (reference files + measured numbers)
Each recipe gives the default, the variants and when to use each. Numbers come from the reference file at 60 fps; px
are at the scale of the reference's card (scale them by the card size in your piece). Key frames:
`motion-spec/refs/<recipe>-ref*-key-frames.png`. Compare your render with them before delivering.

### 19.1 Drag a widget from the side panel onto the site
Two references:
- REF 1 picks and drops, with the grabbing hand (`refs/drag-widget-ref1-key-frames.png`).
- REF 2 starts with the panel closed, opens it and picks. It doesn't have the hand yet, and it has the close-up
  variant (`refs/drag-widget-ref2-key-frames.png`).

**Default:** REF 2's path and curves up to the pick, then everything as in REF 1. Use it as the principle for any
pick-and-drop action.
- **Cursor:**
  - Duda's classic arrow turns into the closed (grabbing) hand on the frame it reaches the widget: a hard swap, no
    fade, no scale.
  - The hand is ~1.15× the arrow, its top level with the tip, its centre ~5 px right and ~16 px below.
  - With the hand there is no press scale; the closed hand is the press.
  - It never turns back into the arrow: it fades out in place over 2 f on the drop frame, all the way to 0.
  - Draw the hand as vector.
- **Panel closed (REF 2):**
  - The cursor goes to the "+" in 37 f, along a ~172 px arc, (0.379, 0, 0.246, 1), already moving when it appears.
  - The "+" hover (#B1E8FF at 50%) lights 9 f before the click. The click uses the normal press (0.85, 3 + 3 f).
  - The panel slides in from behind the left bar in 42 f (0.7 s), (0.8, 0, 0.2, 1), with no fade.
- **To the widget (REF 2):**
  - 93 f (1.55 s), ~408 px, in two legs with continuous speed: (0.478, 0, 0.346, 0.817) + (0.777, 0.347, 0.299, 1).
  - It slows mid-way (~1.5 px/f), which reads as "looking at the panel".
  - The widget hover (#ECECED) lights on arrival.
  - With the panel already open (REF 1): 28 f, ~195 px, (0, 0, 0.175, 1), a light rising arc.
- **Pick:**
  - The cursor holds for 3 f.
  - The card itself follows the cursor, and its slot in the panel stays empty.
  - The card lifts ~6.5 px up-left in 8 f (0, 0, 0, 1).
  - A soft shadow comes in over 10 f: black 10%, feather 20, offset 4/4.
  - No scale, no tilt, full opacity.
- **Drag (REF 1):**
  - 88 f (1.47 s), ~392 px, (0.596, 0, 0.152, 1).
  - The path leaves horizontally to the right, arcs down and lands vertically on the drop point.
  - When the card crosses from the panel onto the site, a blue "+" badge (21 px, #2A84EE) pops on its top-right corner:
    elastic, 0.7 → 1 in 10 f.
- **The site makes room:**
  - When the card enters the site, the panel closes. The site shifts left by the panel's width and scrolls ~124 px,
    in 58 f (0.551, 0, 0.151, 1).
  - The section below moves down ~33 px in 50 f (0.637, 0, 0.338, 1), starting with the badge.
  - The blue line (#2A84EE, ~3.7 px, the content's width) fades in over 4 f, ~24 f before the drop, where the widget
    will land.
- **Drop:**
  - The shadow goes out in 7 f. The card shrinks 100 → 90% in 10 f (0.736, 0, 1, 1) and fades in the last 5 f.
  - On the same frame, the new section opens from inside the blue line, in 60 f (1 s), (0.8, 0, 0.2, 1):
    - the line grows from its centre to the section's height (0 → ~545 px) and a little sideways (~54 px each side);
    - it clips the new content as it opens;
    - the section above moves up and the one below moves down to make room, on the same curve;
    - the blue outline fades in 4 f, half-way through the opening.
- **Intro of the new section:**
  - Each element rises 40 px in ~50 f (0, 0, 0.205, 1), with a 5 f fade, in reading order.
  - 3–4 f between the parts of one item, 12 f between items.
  - Images fade in over 12 f, then drift slowly.
  - The intro starts ~27 f after the drop.
- **Rare variant** (only when asked, or explicit in the design): a cut to a close-up of the action.
  - The cut lands at the drag's peak speed. The scene is at 2.1× for ~70 f.
  - The cursor eases out (0, 0, 0, 0.92). The line rises 30 px while fading in over 7 f. The drop is as in the default.
  - A hard cut back to the wide shot at 107%, settling to 100% in 58 f (0, 0, 0, 1).
- **Default timeline** (T0 = the cursor starts):

  | frames | what happens |
  |---|---|
  | 0–37 | to the "+" |
  | 38–80 | the panel slides in |
  | 38–131 | to the widget |
  | 131 | pick (the hand) |
  | 134–222 | drag |
  | 153–211 | the panel closes and the site scrolls |
  | 156 | badge |
  | 158–208 | the section below makes room |
  | 197–201 | blue line |
  | 221 | drop; the cursor fades out over 221–223 |
  | 221–281 | the section opens |
  | 248–330 | intro |
- **In the library (v12):** `a.drop_widget` does all of this, with `p.drop_slot` where the section opens
  (`library/QUICKSTART.md` §4 and §5); `a.drag` is the gesture alone, for any other pick and drop.

### 19.2 The Copilot generates a screen
Reference: the reviewer's hand-finished version of a welcome email the Copilot creates. Key frames, right (top row)
and wrong (bottom row, made before these rules): `refs/generate-screen-ref1-key-frames.png`.

**This applies to any screen the AI generates** (email, site, page, dashboard). Fit the timing to the number of
blocks, but keep the wash starting with the send, the blocks top to bottom with a gap, each block's texts as it
shows, and the last ✓ at the end of the generation.
- **What the hand-finished version fixed:**
  - the generation starts with the loading (0.1 s), not at 4.5 s, after three steps;
  - big → medium → small, with gaps, instead of the blocks, texts and details coming in almost together;
  - the colours come from the email's gradient (section 7, "The design's colours"), not the defaults;
  - the answer is done at 5.0 s, not 8.0 s, and no loader spins alone (the wrong one spun 3 s);
  - while loading, the top shows "✦ Thinking...", not the Figma frame's "Show steps ⌄";
  - the Copilot's field sits whole in the frame (section 6).
- **The default timeline** (60 fps; 0 = the send):
  - 0–30 f: the message rises 20 px (0, 0, 0, 1) and appears over 5 f, both from f0; 33 f: the summary;
  - 6 f: the wash starts over the whole area that will be generated and sweeps until 223 f (0.588, 0, 0.377, 1);
    feather 20 → 3 from 41 to 114 f;
  - steps at 54, 93, 126 and 180 f; ✓ at 90, 123, 177 and 252 f (the last ✓ when the generation ends);
  - 108 f: the first block (the top one: the photo, also the biggest); its pass runs until 239 f (0.42, 0, 0.58, 1),
    with scale 1.03 → 1 and feather 16 → 0 from 131 to 176 f; its content comes in over 8 f near the end (164–172 f);
  - 111 f: a loose text (the name), with opacity over 20 f, feather 6 → 0 over 53 f and colour #907EF1 → its own
    (119–164 f); the next text 57 f later (168 f);
  - 171 f: the second block, 63 f after the first; its pass runs until 255 f, with scale 1.11 → 1 and feather 18 → 3
    from 184 to 215 f; its image appears from 207 to 215 f;
  - 189–243 f, the details last (the "Welcome." and "You're in the right place." over the photo):
    - colour #F8CD4F from 189 to 197 f, held until 207 f;
    - #907EF1 at 216 f, their own at 243 f;
    - feather 6 → 0 from 189 to 237 f (0.75, 0, 0.25, 1);
  - 280 f: the status turns into "Thought for Xs"; 301 f: the answer; then the rest until the end of the loop.
- **In the library (v14):** `a.generate_screen` does all of this, the small card's too (`gradient=` for the design's
  colours; `p.shown_at(432)` when a bigger artboard is shown in a card), with `a.steps(reply, t, until=end)` for the
  steps and `a.reply(reply, t=end + 25 / 60)` for the typed answer (`library/QUICKSTART.md` §4 and §5). Nothing to
  build by hand.

**A small card** (a 432×264 homepage thumbnail: the Copilot builds a win-back campaign and its email generates beside
it, the classic gradient). Approved after five rounds of review; key frames, approved (top row) and first try (bottom
row): `refs/generate-screen-ref2-key-frames.png`.
- **What the reviews changed, first try → approved:**
  - colours: the design's tones (its yellow strip and a gradient hidden under the frame) → the classic gradient, the
    wash at 50 %;
  - order: the photo first (the biggest block, under the banner) → top to bottom: the banner, the logo, the photo, the
    heading, the line under it;
  - feathers: the hero's → ~40 % on the blocks, half on the wash, 2 on texts and icons;
  - texts: whole, blurred, purple → letter by letter, the whole text orange → pink → its own; on the way, a purple
    front and then a gradient running ahead of the letters (two copies of each text) were both rejected;
  - the logo's icon: sharp → the texts' feather and colour;
  - the photo: still → 112 % → 100 % inside its frame;
  - the end: "Thought for 4s" alone → the answer as a plain typewriter, with its action bar;
  - the blocks: the component's exact size (dark dashes on the photo's edge) → 5 px of room and radius + 5.
- **The timeline** (60 fps; 0 = the send):
  - 6 f: the wash, feather 10 → 1.5;
  - 96 f: the banner's block (a card: 1.11 → 1, feather 7.2 → 1.2); 132 f: its letters, as it shows;
  - 112 f: the logo: the icon fades in over 20 f, its two texts 2 f and 6 f later;
  - 124 f: the photo's block (a panel: 1.03 → 1, feather 6.4 → 0); 174 f: the photo starts settling, 112 % → 100 %
    over 1.5 s (0.16, 1, 0.3, 1);
  - 184 f: the heading, as the photo shows; its second line when the first ends; 222 f: the line under it (≤ 0.75 s);
  - 287 f (4.8 s): the generation ends with the last ✓; 312 f: "Thought for 5s"; 333 f: the steps fold away (8 f);
    341–388 f: the answer types; 393 f: its action bar; 402 f (6.7 s): all done, still until the loop's seam.
- **Letter by letter in Rive:** on the text, a TextModifierGroup with `modifyOpacity` and one TextModifierRange
  (`modifyFrom` = `falloffFrom` = −10, `falloffTo` = 0, `modifyTo` = w, where w = min(0.5, 6 / letters) is the soft
  front, or 0 for a typewriter); animate its `offset` from −w (all hidden) to 1 (all shown), linear, over the text's
  entrance. The colour is the text fill's own `colorValue`, keyed as in section 7; the feather is a Feather on that fill
  (`fillRule="clockwise"`).
