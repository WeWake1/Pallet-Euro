# Prototype history

Every design round, what it tried, and the owner's verdict. Screenshots are 1440 px desktop and 390 px phone.

## Round 1 · dark (7 Nov 2026) · rejected entirely

Folder: `round-1-dark/`. Code deleted.

| | Direction | Idea |
|---|---|---|
| A | The Register | Passport-style record card, guilloche linework, rubber stamps, certificate ledger |
| B | The Object | Huge "1200 × 800 × 144" numerals, pallet on black with callouts, technical drawing |
| C | The Port | Split-flap "how many fit" board, stencil type, "cleared for Europe" board |

Verdict: "I hate everything." The owner wanted a **light** background (the brief was misread as dark), and disliked every UI element.

## Round 2 · light (7 Nov 2026)

Folder: `round-2-light/`. Still viewable at `/prototype/round-2/` (code in `src/components/proto/archive/r2/`).

| | Direction | Idea |
|---|---|---|
| A | Studio | "Europe’s standard pallet, made in India." EPAL 1 render on white, cross-fading through five studio angles |
| B | Assembly | "Built to the EPAL standard." Live 3D EPAL 1 that builds itself, gets its marks, shows dimensions, can be pulled apart |
| C | Certified | "Licensed by EPAL. Check it yourself." Deep-blue block, cycling stack of certificate documents |

Verdict:
- **Keep:** the headline "Europe’s standard pallet, made in India." (A); the product cards after the hero (A); "Certified at every step" (B); "Your next container, on EPAL pallets" as the quote band (C).
- **Reject:** all three hero concepts. The five-angle turntable is "good but generic".

## Round 3 · hero concepts (7 Nov 2026)

Folder: `round-3-heroes/`. Still viewable at `/prototype/round-3/` (code in `src/components/proto/archive/r3/`). Every variant keeps the chosen headline and is followed by the kept sections (product cards, "Certified at every step", "Your next container" band). One typeface (Urbanist) except the band, which keeps its condensed caps.

| | Hero | Idea | Motion |
|---|---|---|---|
| A | The Line | All 28 pallets roll along a conveyor through a quality-check gate; a readout names each one as it passes | Continuous; hover stops it |
| B | The Stack | Tall stacks of EPAL 1 pallets drop into place one by one, with spec tags (scale) | 2.5 s build, then a slow sway |
| C | The Mark | Opens on a close-up of the corner block; the EPAL mark brands in hot orange and cools; the camera pulls back to the pallet | 4 s film, then a slow drift |
| D | The Container | A deep-blue 20' container opens its doors on a load of EPAL pallets (real floor-fit layout) | 3.5 s, doors and camera |

B, C and D are live 3D built from `pallet-geometry.json`; A uses the studio renders.

Verdict:
- **Not heroes, but keep the ideas:** C (The Mark) as an Apple-style scroll section after the hero; A (The Line) on a products or certifications page.
- **Disliked:** B (The Stack) and D (The Container). The container idea may move into the "Your next container" band.
- **Quality:** the live 3D (wood, container) looked "low quality, fake, non-realistic". Hence round 4: photoreal Blender renders only.

## Round 4 · photoreal heroes (7 Nov 2026)

Folder: `round-4-heroes/`. Still viewable at `/prototype/round-4/` (code in `src/components/proto/archive/r4/`). No live 3D: every picture is path-traced in Blender (Cycles) from the exact pallet geometry and the approved wood look, then played back as image frames. Scenes: `tools/render/hero/` (`jaali.py`, `resting.py`, `rann.py`), shared builder `tools/render/palletkit.py`. Frames in `public/dev/r4/` (dev only: EPAL oval and the `IN-XXX` placeholder).

| | Hero | Idea | Motion |
|---|---|---|---|
| A | Indian light | An EPAL 1 in a pale stone room; morning sun through a jaali (Indian stone lattice) throws its star pattern over the wall, floor and pallet. Europe's standard pallet, Indian light | Desktop: the cursor moves the sun (48 frames, 1.3 MB). Touch: slow drift |
| B | On the headline | The headline very large on white; the pallet is set down on the word "pallet," with its real contact shadow; the word gives a little under the weight | 1.7 s set-down, hover lifts it; "Set it down again" |
| C | White desert | One EPAL 1 alone on a white salt desert (after the Great Rann of Kutch) under a physical sky; headline in the sky | Seamless 9.5 s camera sway (72 frames, 3.2 MB); Pause button |

Phones: the picture comes first (5:4), then the headline. Header floats transparent over A and C on computers.

Verdict:
- **A (Indian light) is "still good enough"**: the fallback hero if no later concept wins.
- **Disliked:** B (On the headline) and C (White desert).
- Everything else asked after round 4 was answered yes (decisions #22–#27), and the owner asked to see the Mark and the container as Apple-style scroll stories.

## Round 5 · hero concepts and two scroll stories (8 Nov 2026)

Folder: `round-5-heroes/`. Archived at `/prototype/round-5/` (`?variant=A|B|C`). All photoreal Blender renders (`tools/render/hero/`), frames in `public/dev/r5/` (dev only: EPAL oval and the `IN-XXX` placeholder).

| | Hero | Idea | Motion |
|---|---|---|---|
| A | Two worlds | The same EPAL 1 from the same camera in two rooms: a north-European warehouse (white brick, cool light through a steel factory window, `europe.py`) and the Indian jaali room from round 4 (`jaali.py`). The seam between them follows the cursor: Europe's standard, made in India | Cursor moves the seam; phones: it sweeps by itself, drag to move |
| B | In its place | An anamorphic installation in a white gallery: the pallet's 20 wooden parts hang on fine wires at very different depths and line up into the exact pallet from one spot only (`anamorph.py`) | 61 orbit frames; on load it parts and settles; cursor movement fans the layers out, they settle when it rests; phones: every 7 s |
| C | Look inside | An EPAL 1 in low morning sun; a lens follows the cursor and shows it as an X-ray in the brand blue, with all 78 nails, and names the part under it (`xray.py`: photo, X-ray and an ID map) | Lens follows the cursor; phones: it wanders, touch to move |

Scroll stories under every hero (owner's request after round 4), pinned and scrubbed on computers, played once by themselves on phones (rule 7):
- **The Mark** (right after the hero, `mark.py`, 168 frames): a steel head brands "EPAL in oval" into the corner block (glow, smoke, cooling), the camera tracks to the IPPC HT mark, flies through the fork opening under the deck, and pulls back to the whole pallet. Captions use only facts checked on EPAL's page (decisions, after round 4).
- **Your next container** (the closing band, `container.py`, 150 frames): a weathered deep-blue 20' box opens its doors (right-hand door first, as on a real box) on 11 EPAL pallets of cartons; the camera rises, the roof lifts away and shows the standard 7 + 4 floor layout; it ends on the deep-blue quote card.

Verdict (23 Nov 2026, decisions #39–#42):
- **B (In its place) disliked.** No hero chosen. The owner likes the **simplicity of round 2's A and round 4's A**; wants two new simple heroes and one "crazy cool" one.
- **The Mark: loved**, with more frames for a smoother scroll (now 335 frames, phones 168). **The container: loved.**

## Round 6 · two simple heroes and one crazy one (23 Nov 2026)

Archived at `/prototype/round-6/` (`?variant=A|B|C`), followed by the Mark and container stories. Rendered on the Windows PC (RX 9060 XT): scenes `tools/render/hero/daybreak.py`, `neem.py`, `bullettime.py` (`python tools/render/run.py r6`), frames in `public/dev/r6/` with `-sm` phone versions (dev only: EPAL oval and `IN-XXX`). One component plays all three: `src/components/proto/r6/HeroFrames.astro`.

| | Hero | Idea | Motion |
|---|---|---|---|
| A | Daybreak | Round 2's white studio with a real sun: one EPAL 1, the light travels a whole day. Sunrise low on the left (warm, the low sun shines under the deck through the fork openings), noon high behind, sunset low on the right (the shadow reaches toward the headline) | 48 frames; the cursor carries the sun across; phones: it drifts back and forth |
| B | Neem shade | Round 4's calm in a new place: an EPAL 1 in a sunlit lime-plaster courtyard under a neem tree the camera never sees. Its dappled shade (procedural neem leaves on two canopy layers) moves gently over wall, floor and pallet; the top left, behind the headline, stays in calm shade | 48-frame seamless loop; moving the cursor stirs the breeze |
| C | Bullet time | The crazy one: a dropped EPAL 1 frozen at the instant its corner meets the studio floor, tilted hard, with a puff and a spray of sawdust hanging in the air (22,000 grains placed by formula plus a volume puff) | 61 orbit frames; the cursor circles the camera around the frozen moment; phones: it orbits by itself |

Tried and dropped before showing: a long striped shadow from a low sun (a 14 cm pallet's blocks and boards block every gap, so the shadow is a flat blob) and a granite block landing on the pallet (the dust cloud hid the product).

Verdict (23 Nov 2026, decision #51): **"good, but still not up to what we want."** No hero chosen; another round, keeping every round saved.

## Round 7 · the same brief, moving something other than the light (23 Nov 2026)

Archived at `/prototype/round-7/` (`?variant=A|B|C`), followed by the Mark and container stories. Rounds 4 and 6 all moved the sun or the shade; round 7 moves the drawing, the viewpoint and the wood itself. Scenes `tools/render/hero/blueprint.py`, `frieze.py`, `carved.py` (`python tools/render/run.py r7`), frames in `public/dev/r7/` with `-sm` phone versions (dev only: EPAL oval and `IN-XXX`). One component plays all three: `src/components/proto/r7/HeroFrames.astro`.

| | Hero | Idea | Motion |
|---|---|---|---|
| A | From the drawing | Round 2's white studio: the EPAL 1 as a deep-blue technical drawing (Freestyle ink, hidden edges dashed) turning into the real pallet part by part, in assembly order (bottom boards, blocks, stringer boards, deck boards, then nails and marks), with its dimension lines (1200, 800, 144 mm). The brand blue is in the picture itself | 22 frames; the cursor goes from the drawing (left) to the pallet (right); phones: it drifts |
| B | Eye level | The camera on the floor of a sunlit sandstone courtyard, a hand's height up, close to the long side: the pallet becomes a low frieze with its three branded blocks, the fork openings like doorways; behind, out of focus, an arcade of pointed arches against a bright sky | 41 frames; the cursor moves the camera along the pallet (parallax through the openings); phones: it drifts |
| C | Carved | The crazy one: a solid slab of spruce, exactly the size of an EPAL 1, turns to sawdust along a rough front and reveals the finished pallet inside; the dust bursts up and fades, heavier grains settle on the floor | 48 frames; the cursor carves (right = more pallet); phones: it drifts |

Verdict (23 Nov 2026, decision #58): "good", but not the final hero; **every hero moving with the cursor "is getting boring: try something new."**

## Inner pages · Inspect and Before/after (23 Nov 2026)

Live at `/prototype/inner/` (`?variant=A|B`). The owner's refinements of round 5's unused heroes (decision #52). Renders: `tools/render/hero/inspect.py` (`python tools/render/run.py inner`), in `public/dev/inner/`.

| | Demo | Idea |
|---|---|---|
| A | Inspect (product page) | The real studio photo of the EPAL 1; the part under the cursor gets a thin blue outline and a label with its name and size (from a one-colour-per-part ID map); the parts table beside it (names, sizes, quantities from EPAL's drawing; plain HTML) lights up with it, and hovering a row outlines every part of that kind |
| B | Before and after (About) | Same studio, camera and light: a generic unmarked worn pallet (grey timber, grime and mould, one deck board missing and one broken, a split-off corner, a twisted block, rusty nails standing proud) against the EPAL 1; a drag handle (computers: it follows the cursor) and three short facts on each side |

Verdict (decisions #60–#61): Before and after **approved** for the About page. Inspect: not needed on every product page; it moves to **one guide page** and needs a polished highlight, more than one view, layer by layer, and an exploded view to play or turn. Rebuilt as "Anatomy" (below).

## Round 8 · four kinds of motion, none of them the cursor (23 Nov 2026)

Archived at `/prototype/round-8/` (`?variant=A|B|C|D`), followed by the Mark and container stories. The owner picked all four kinds of motion offered (decision #59). Scenes: `tools/render/hero/layers.py` (one pallet in its layers: explode, assemble, film, orbit, orbit-ids), `container.py --still`, `jaali.py --glide`; frames in `public/dev/r8/`.

| | Hero | Motion |
|---|---|---|
| A | Built in layers | A scroll story: the hero stays pinned on computers while scrolling takes the EPAL 1 apart into its layers (top deck first), each layer named at its end, then the page carries on. Phones: plays once by itself |
| B | The journey | Scenes that advance by themselves, each with a slow push-in and a progress bar: 01 Made in India (round 7's sandstone courtyard), 02 Loaded for export (the deep-blue container, doors open), 03 To Europe’s standard (round 5's European warehouse). Tap a bar to jump |
| C | The family | Tap to transform: EPAL 1, EPAL 2, EPAL 3 and CP1 under the picture; a tap sends the pallet's parts flying up and drops the new one in, layer by layer. Until the first tap it changes by itself every few seconds |
| D | Living photograph | Plays by itself: round 4's Indian light (the owner's favourite so far) as a slow camera glide into the jaali-lit room and back, on a sine, with no seam and nothing to do |

## Inner pages · Anatomy (replaces Inspect) and Before/after (23 Nov 2026)

`/prototype/inner/?variant=A`: the guide page's anatomy viewer. "Take it apart" plays the exploded view (48 frames); taken apart, drag or the arrow buttons turn it all the way round (36 angles); "Layer by layer" steps through top deck boards, stringer boards, blocks, bottom deck boards and nails; any part can be picked on the pallet or in the list. The highlight is vector: outlines traced from a double-size ID map (`tools/render/trace_ids.py`), a white-and-blue line around the part, the rest softly veiled.

Round 8 verdict (decisions #65–#66): **"good, but they still ain't cutting it. Something more unique, cool yet simple."** Anatomy approved for the guide page after two fixes (no layer picked by itself; smoother turning), both done the same night (72 angles, eased turning).

## Round 9 · four bold pictures, motion later (23 Nov 2026)

Archived at `/prototype/round-9/` (`?variant=A|B|C|D`). After eight rounds built around motion, this round finds the picture first: four bold, simple stills (only a slow settle as the page opens); the chosen one gets its motion next. Scene: `tools/render/hero/r9.py --scene indigo|plan|upright|macro` (`python tools/render/run.py r9`), pictures in `public/dev/r9/` (2400×1350 with `-sm`).

| | Picture | Idea |
|---|---|---|
| A | Indigo | An EPAL 1 carrying rolls of indigo-dyed cloth on a white studio: India's own blue, close to the brand's deep blue, the one strong colour |
| B | Plan | Straight from above on warm stone in late sun: the boards and their long shadows as a graphic poster |
| C | Upright | The EPAL 1 standing on its end against a lime-washed wall, low sun from the front right, like a piece of design |
| D | Close-up | One corner, close and cinematic: deck board ends, the chamfer, the branded block, shallow focus |

Verdict (decision #68): **"very, very simple"**: simple meant unique, cool and simple, not plain.

## Round 10 · the owner's idea: one pallet, every industry (24–25 Nov 2026, awaiting the owner’s verdict)

Live at `/prototype/` (`?variant=A|B|C`), followed by the Mark and container stories. Built from the owner's own idea (decision #69): an EPAL pallet carrying a different industry's load, one detailed, unbranded product per industry. All three play by themselves (no cursor). The eleven loads (`tools/render/hero/loads.py`): FMCG (bottled drinks on slip sheets, stretch-wrapped), Automotive (tyres), Pharmaceuticals (cartons under a quilted thermal cover with a logger), Chemicals & Polymers (two 200-litre drums), Engineering & Heavy Industries (an electric motor on skids), Food & Agriculture (crates of mangoes), Manufacturing (copper wire on reels), Logistics & Warehousing (mixed cartons with tape and labels, wrapped), Textiles & Apparel (rolls of indigo cloth), Exporters & Importers (jute sacks), Building Materials (clay bricks, strapped). Forklift and racking: `tools/render/hero/warehouse.py`. Scenes: `tools/render/hero/r10.py --job industries|lift|delivery|still`.

| | Hero | Motion |
|---|---|---|
| A | The industries | The owner's idea: the camera circles one EPAL 1 in the white studio; every few seconds the load lifts away and the next industry's load comes down and settles (374 frames, a 38-second loop); the industry is named under the headline and marked in the list of industries under the hero (plain text, for search) |
| B | Lift | A forklift raises an EPAL 1 of bottled drinks to the second beam level of a racking stocked with every other industry's load, drives it in, sets it down and backs out; the camera rises with the load (132 frames, 5.5 s, plays once, then "Play again") |
| C | The delivery | The forklift combined with the industries: a forklift drives in carrying one industry's load, stops beside the headline while the industry is named, backs out, and the next one drives in. Photoreal sprites from an orthographic camera (every load × 4 wheel phases, transparent, with its own shadow), slid across the page, so it is smooth at any frame rate |
