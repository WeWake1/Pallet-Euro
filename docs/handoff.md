# Handoff: Pallet Euro Packaging website

Read this first in every Claude Code session, on either machine. It carries everything from the earlier sessions that is not obvious from the code: where the work stands, what the owner has decided, how they like to work, how to set up a new machine, and how the renders are made. Owner answers are logged in full in `docs/decisions.md`; every design round with screenshots is in `docs/prototypes/README.md`.

**At the end of every session:** update "Status" below and add a line to "Session log" at the bottom. The owner commits and pushes themselves (decided 2026-11-23); commit or push only when they ask.

---

## 1. Status (last updated 2026-11-23)

- **Stage:** two tracks.
  - **Hero:** rounds 5 to 7 turned down (round 7: "good", but every hero moving with the cursor "is getting boring", decision #58); the two scroll stories are approved (the Mark has 335 frames). Round 8 (four kinds of motion, none of them the cursor) turned down too: "something more unique, cool yet simple" (#65). **Round 9** (2026-11-23: four bold stills, Indigo, Plan, Upright, Close-up; the chosen picture gets its motion next) waits for the owner's verdict. Live at `/prototype/` (`?variant=A|B|C|D` or the arrow keys). The owner likes the **simplicity** of round 2's A and round 4's A.
  - **Inner pages:** before/after approved for About (#61). The part inspector moved to one guide page as "Anatomy" (exploded view to play and turn, layer by layer, vector highlight): **approved** (#66) after two fixes, done (nothing picked by itself; smooth turning on 72 angles). `/prototype/inner/?variant=A`.
  - **Product cards** on `/` and the prototype now use this repo's catalogue renders (dev marks); nothing live shows Ambica's `IN-083` any more (only the frozen round-2 archive).
  - **Production home page:** started on 2026-11-23 with the parts that do not depend on the hero (decision #33). `/` now runs on the production layout with the kept sections, SEO head, schema, the launch gate, `robots.txt`, sitemap and 404 (section 7). Mobile Lighthouse: 100 / 100 / 100 for performance, accessibility and best practices; SEO 69 only because of the `noindex` gate.
- **Waiting on the owner:** round-9 question #67 (`docs/decisions.md`), plus the company facts from round 2 (domain confirmed: palleteuro.com).
- **Fallback hero** if nothing in round 9 wins: round 4's A "Indian light" (`/prototype/round-4/?variant=A`).
- **Catalogue rendered on the PC (2026-11-23, decision #53):** 28 pallets × 5 studio views in `src/assets/products/<slug>/`, 28 GLB models in `public/models/` (dev marks; about 74 s per pallet with its GLB). Not used by any page yet.
- **Why the second machine:** the owner wants to do heavier Blender work on their Windows PC (AMD Radeon RX 9060 XT, 32 GB RAM). Section 3 explains the setup.
- **Windows PC: set up and verified (2026-11-23).** Every round-5 scene renders on the RX 9060 XT and matches the Mac's frames; the site builds; the review scripts run. Two Windows-only render bugs were fixed in `tools/render/hero/common.py` (section 3, step 7). cwebp is installed.
- **Nothing is public yet.** Every page is `noindex`. The EPAL licence is applied for, not granted (see CLAUDE.md hard rules 1 and 2).
- **Repo privacy (owner's decision, 2026-11-23):** the GitHub repo `WeWake1/Pallet-Euro` is **public** and stays public for now. Claude pointed out the cost: anyone can see the EPAL-oval renders, the older renders with Ambica's `IN-083 HT` mark, and the notes naming Ambica (this file included), which conflicts with hard rules 1 and 2. The owner chose to keep it public. Do not change the visibility unless they ask; mention it again only before anything goes live (domain, Search Console, directories).

## 2. Run it

```
npm ci                  # once per machine (Node 24, see .nvmrc)
npm run proto           # dev server on http://127.0.0.1:4322
```

Open `http://127.0.0.1:4322/prototype/` (round 9), `/prototype/inner/` (anatomy, before/after), `/prototype/round-8/` … `/round-2/`. `/` is the production home page in progress.
Astro 7 may start the dev server in the background and return at once: `npx astro dev status`, `npx astro dev logs`, `npx astro dev stop`. On the Mac, port 4321 belongs to another project; that is why this one uses 4322.
Astro 7 allows one dev server per project: if `npm run proto` says "Another astro dev server is already running", stop the old one (`npx astro dev stop`, or close its terminal) and start again.
`npm run check` type-checks (0 errors expected; one deprecation hint in the round-2 archive is known).
`vite.server.forwardConsole` is off in `astro.config.mjs` on purpose: with it on, Vite 7 crashed the dev server.

## 3. Set up a new machine (Windows PC with the Radeon)

All steps were done on the PC on 2026-11-23. The notes in italics are what that setup found.

1. **Git for Windows**, then `git clone https://github.com/WeWake1/Pallet-Euro.git`. Line endings are pinned by `.gitattributes`; leave them alone.
2. **Node.js 24**, then `npm ci` and `npm run proto` (section 2). *The PC has Node 22.23.5, which every package accepts (Astro 7.4.7 needs 22.23.4 or newer), so it was kept; move it to 24 when convenient.*
3. **Blender 5.1.x** (the Mac uses 5.1.2; keep both machines on the same version so renders match). Blender's Cycles supports the RX 9000 (RDNA 4) cards through **HIP** since Blender 4.4, with AMD's Adrenalin driver 24.6.1 or newer: install the latest Adrenalin driver. Check Edit > Preferences > System > Cycles Render Devices > HIP lists the RX 9060 XT. *The PC has 5.1.2. HIP lists two devices there: the RX 9060 XT and the CPU's built-in "AMD Radeon(TM) Graphics". `common.py` renders on the dedicated card only (the heaviest Mark frame took 26 s on the card alone, 34 s on both).*
4. **Python 3** on PATH (only for `tools/render/run.py`; the scenes run on Blender's own Python).
5. **cwebp** for the phone-size images: download libwebp from https://developers.google.com/speed/webp/download, unzip, add its `bin` folder to PATH (or set `CWEBP`). *On the PC: libwebp 1.6.0 (signature checked against the WebP release key) in `%LOCALAPPDATA%\Programs\libwebp-1.6.0-windows-x64\`, its `bin` folder on the user PATH (new terminals only).*
6. **Google Chrome** for the review scripts in `tools/shot/` (or set `CHROME` to `chrome.exe` / `msedge.exe`).
7. **First render test:** `python tools/render/run.py mark --test --frames 0`. It should print `DEVICE HIP: AMD Radeon RX 9060 XT` and write `.render-test/mark/000.webp`. A `WARNING no GPU found` line means Blender fell back to the CPU: fix the driver first. Force a backend with `--device HIP` or the env var `PE_RENDER_DEVICE`. *Passes on the PC. Before the fix, Blender on Windows wrote every frame under the drive root (`C:\.render-test\...`) while the log said WROTE, so the repo folder stayed empty; `common.py` now makes `--out` absolute. Blender's `CUEW initialization failed` line (no NVIDIA card) is harmless; `run.py` hides it.*
8. **Long renders:** stop the PC from sleeping while plugged in (Windows Settings > System > Power), or a queue pauses for hours. That happened twice on the Mac. *Already so on the PC: sleep and hibernate are off on AC power.*
9. **Claude Code:** open this folder. `CLAUDE.md` loads by itself and points here. The project skills in `.claude/skills/` (grilling, prototype, karpathy-guidelines) come with the repo. Claude's own memory from the Mac does not travel; its content is in section 5.
10. **Keyword research (optional, later):** OpenSEO is a separate project, not in this repo (section 10).

## 4. The project in one page

- **Company:** Pallet Euro Packaging ("Pallet Euro" large, "packaging" small), a new Indian company focused on EPAL pallets. Goal: be the name every Indian buyer thinks of for EPAL pallets. **SEO is the top priority** on every decision.
- **Range:** all 28 pallets, EPAL family first (EPAL 1/2/3, CP1–CP9), then pinewood, hardwood, GMA and the collar (plain names, no EPAL marks). Data: `src/data/range28.ts`, `src/data/products-ambica-source.json`, geometry `src/data/pallet-geometry.json`.
- **Site plan (decided):** multi-page. Home; Products (one page per pallet); Certifications (one page per certificate, each with a Verify link); About; Contact/Quote; Guides (articles answering buyers' searches). Home page first, then the inner pages.
- **Stack:** Astro 7 + TypeScript, React islands, Tailwind v4. Static build for Hostinger, one PHP file for the quote form. All text and links in the static HTML.
- **Hard rules:** in `CLAUDE.md` (no Ambica connection, no EPAL oval in public before the licence, certificate rules, never invent facts, EPAL product names, renders are dev-only, phone performance).
- **Look (decided):** light background (never dark), deep blue `#0B3A9E`, Urbanist everywhere, bold condensed capitals (Sofia Sans Condensed) only for big statement bands. Rich, premium motion; no video, ever.
- **Kept from earlier rounds:** headline "Europe’s standard pallet, made in India."; product cards (`home/Range.astro`); "Certified at every step" (`home/CertifiedSteps.astro`); the deep-blue "Your next container, on EPAL pallets" quote band (now the end of the container scroll story).
- **3D policy (decided):** everything visitors look at is a photoreal Blender render (stills or frame sequences). Live 3D only for "drag to rotate" on product pages, loaded on tap. "The Line" (all pallets on a conveyor) goes on the Products page. The Mark is a scroll story right after the hero; the container is a scroll story at the end.

## 5. Working with the owner (carried over from Claude's memory on the Mac)

- **Who:** the founder of Pallet Euro Packaging, with 20+ years in pallets. They also own Ambica Patterns India Pvt Ltd, a separate pallet company in Bengaluru (heat-treated pinewood pallets, ISPM-15 HT, not EPAL). Ambica must never be connected to Pallet Euro in public. Vision: India's largest EPAL manufacturer, the brand buyers think of first. They write long, emphatic briefs, want premium, unique output, and hate generic AI-looking sites. They rely on Claude Code for the web and Blender work.
- **Ask at every decision.** Use numbered questions, each with a recommended answer, worded so "yes" accepts it (the `grilling` skill). For visual or motion choices, build a working demo with variants on one route (the `prototype` skill). If the brief contradicts itself, ask before building: guessing "dark" from a contradictory first brief cost a full redo. Do the fact-finding yourself, then batch real decisions into one short round. When they say "idk", decide or show options as variants. When they delegate, decide, say so in one line, and log it. Log every answer in `docs/decisions.md` the same day.
- **Taste:** premium-corporate polish over clever metaphors. Reference sites they like most: Jay Wood, We Are Pallets, Golden Pallet (white, big confident headlines, one strong colour). They judge by polish and clarity, not novelty alone, but keep asking for "creative unique" heroes.
- **What has landed so far:** photoreal + a real-looking space + Indian character + interactive light (round 4's "Indian light"); scroll stories (the Mark, the container: "loved"). What failed: anything dark; live WebGL ("low quality, fake"); turntables ("good but generic"); playful type tricks; empty landscapes; short films that build up to the message (a hero should be one striking statement from its first frame; this reading is not confirmed by the owner); and, after rounds 4–7, **heroes that move with the cursor ("getting boring")**.
- **Never reuse** round 1's ideas: guilloche/passport/MRZ, rubber stamps, split-flap boards, stencil type, monospace "technical" styling, huge dimension numerals as the hero.
- **Phones:** no scroll-driven or pinned motion (play once by itself instead), no Lenis, no dot-grid backgrounds, 3D off the first load, Lighthouse mobile 99–100.
- **EPAL register (for checking the licence and competitors):** https://www.epal-pallets.org/eu-en/licensee-search. Results come from POSTing the page's main form (`module-map-main-form`, TYPO3 fields `tx_licenseesearch_pi1[...]` with the hidden `__referrer`/`__trustedProperties`) to `/eu-en/licensee-search/licenseesearch.json?...findByFilter...` with `tx_licenseesearch_pi1[search][countryCode]=IND`. Snapshot 2026-11-07: 23 active Indian licences (codes up to IND-039). Jay Wood Industry holds IND-007 and IND-016.

## 6. Design rounds so far (details and screenshots: `docs/prototypes/README.md`)

| Round | Date | What | Verdict |
|---|---|---|---|
| 1 | 7 Nov | Three dark directions | Rejected entirely; never reuse |
| 2 | 7 Nov | Light: Studio, Assembly (live 3D), Certified | Kept the headline and three sections; all heroes rejected |
| 3 | 7 Nov | The Line, Stack, Mark, Container (live three.js) | Mark → scroll story; Line → Products page; 3D looked fake |
| 4 | 7 Nov | Photoreal: Indian light, On the headline, White desert | Indian light = fallback hero; others disliked |
| 5 | 8 Nov | Two worlds, In its place, Look inside + Mark and container scroll stories | Heroes turned down (B disliked); both scroll stories loved |
| 6 | 23 Nov | Daybreak, Neem shade, Bullet time (two simple, one crazy) | "Good, but not up to what we want" |
| 7 | 23 Nov | From the drawing, Eye level, Carved (moving the drawing, the viewpoint, the wood; not the light) | "Good", not final; cursor motion "getting boring" |
| 8 | 23 Nov | Built in layers (scroll), The journey (scenes), The family (tap), Living photograph (plays by itself) | "Good", not cutting it: "more unique, cool yet simple" |
| 9 | 23 Nov | Four bold stills (Indigo, Plan, Upright, Close-up); motion after the pick | **Awaiting verdict** |

Round 5 in one line each:
- **A Two worlds** (`r5/HeroWorlds.astro`): the same EPAL 1 from the same camera in a European warehouse (cool light through a steel window) and the Indian jaali room. The cursor moves the seam; on phones it sweeps by itself.
- **B In its place** (`r5/HeroAnamorph.astro`): an anamorphic installation. The pallet's 20 parts hang on wires at different depths and line up only from one spot. Cursor movement fans the layers apart; they settle when the cursor rests. This was the recommended pick.
- **C Look inside** (`r5/HeroXray.astro`): a lens shows the pallet as a blue X-ray with all 78 nails and names the part under it (from an ID-map render).
- **The Mark** (`r5/MarkFilm.astro`, 335 frames since 23 Nov; phones 168): a steel head brands the EPAL oval (glow, smoke, cooling) → IPPC HT mark → fly under the deck → whole pallet. Captions use only facts checked on EPAL's page (`docs/decisions.md`, after round 4).
- **Container** (`r5/ContainerFilm.astro`, 150 frames): a deep-blue 20' container opens (right-hand door first), 11 EPAL pallets of cartons, the roof lifts for the 7 + 4 floor layout, ending on the blue quote card.

## 7. Code map

**Production (stays at launch):**
- `src/pages/index.astro`: the home page in progress (hero stand-in: a still of round 5's B). `404.astro`. `robots.txt.ts` (blocks all crawlers until launch).
- `src/layouts/Base.astro`: the production layout (SEO head, fonts, header, footer, reveal-on-view). `src/styles/site.css`: tokens and buttons (light only).
- `src/components/site/`: `Seo.astro`, `Header.astro` (Menu button below 1100 px; below 560 px the quote button moves into the menu), `Footer.astro`, `Hero.astro`, `Range.astro`, `Certified.astro`, `QuoteBand.astro`, `Logo.astro`, `Icon.astro`. Ported from the prototype's kept sections, with real links.
- `src/data/site.ts`: company facts (placeholders in `{{braces}}`), navigation, and **`LAUNCHED`, the launch gate** (false: `noindex` everywhere and `robots.txt` blocks crawling). `src/lib/schema.ts`: Organization and WebSite JSON-LD (no `sameAs`, no parent company).
- `astro.config.mjs`: `site` (domain not confirmed), `@astrojs/sitemap` (prototype and 404 left out), CSS inlined into every page.
- Product links use `/products/<slug>/` with the slugs in `src/data/range28.ts` (open question #36). Those pages do not exist yet.

**Prototype (deleted before launch):**
- `src/pages/prototype/index.astro`: round 5 (live). `round-2/3/4.astro`: frozen archives.
- `src/layouts/Proto.astro`: prototype layout (noindex, fonts, `?variant=` before first paint, `[data-reveal]` observer).
- `src/components/proto/home/`: the live home sections shared by the current round (Header, HeroCopy, Range, CertifiedSteps, ContainerBand, Footer, `home.css` scoped under `.pe`, `when-shown.ts` to start a hero only when its variant is visible).
- `src/components/proto/r9/HeroStill.astro`: the round-9 heroes (one still each, a slow settle). `src/components/proto/r8/`: the round-8 heroes (`HeroScroll`, `HeroScenes`, `HeroTransform`, `HeroLoop`), shown by `src/pages/prototype/round-8.astro`. `round-7.astro`: round 7 archive.
- `src/components/proto/r7/HeroFrames.astro`: the three round-7 heroes (frames scrubbed by the cursor; with `dims`, the dimension lines from the scene's `dims.json`, kept in register with the canvas crop). `src/pages/prototype/round-6.astro` (uses `r6/HeroFrames.astro`) and `round-5.astro`: archives (round 5's components stay in `r5/`, which the live page still uses for the films).
- `src/pages/prototype/inner.astro` + `src/components/proto/inner/`: `Anatomy.astro` (the guide page's exploded view, layer by layer; vector outlines from `outlines.json`) and `BeforeAfter.astro`. Parts data by layer: `src/data/epal1-parts.ts`.
- `src/components/proto/r5/`: round-5 heroes, `Film.astro` + `film.ts` (scroll film: pinned and scrubbed on screens over 900 px, play-once on phones, lazy frame loading, rests on whole frames), `seq.ts` (frame player: coarse-to-fine loading, cross-fade, cover crop around a focus point).
- `src/components/proto/r4/`: round-4 heroes (still used by nothing live; the archive has its own frozen copy).
- `src/components/proto/archive/r2|r3|r4/`: frozen copies of each round (do not edit).
- `src/components/proto/Switcher.astro`: the floating variant switcher (prototype only). `Icon.astro`: Phosphor icons inlined at build time. `Logo.astro`.
- `src/data/`: `certificates.ts` (placeholders in `{{braces}}` or with X; never publish), `range28.ts`, `pallet-geometry.json` (exact part coordinates in mm), `products-ambica-source.json` (catalogue data copied from the Ambica repo).
- `src/lib/containers.ts`: container sizes and `floorFit()` (11 Euro pallets in a 20', standard single-tier layouts). `pallet-drawing.ts`: technical drawing helper.
- `src/assets/dev-renders/`: catalogue renders copied from the Ambica repo (carry `IN-083 HT`, dev only).
- `public/dev/`: dev-only renders and textures (`r4/`, `r5/` with `*-sm` phone versions, `stamps/`, `textures/`). Delete before launch.
- `tools/render/`: `palletkit.py` (pallet builder for Blender: geometry, approved wood look, nails, marks from `brand.json`), `brand.json` (dev marks: EPAL oval + `IN-XXX HT` placeholder), `stamps/`, `textures/` (ambientCG Wood096 pine, Wood060 hardwood, CC0), `hero/` scenes, `run.py`, `make_small.py`.
- `tools/shot/`: `sheet.mjs` (contact sheet), `shots.mjs` (page screenshots with errors and overflow), `browser.mjs` (finds Chrome on Mac or Windows).
- `docs/`: `decisions.md`, `prototypes/` (history + screenshots per round), this file.

## 8. Render pipeline

**How it works:** each scene in `tools/render/hero/` imports `common.py`, which imports `palletkit.py`. That resets the Blender scene, builds the materials and gives helpers. Every scene builds the exact EPAL 1 with `C.build_pallet()` (deterministic: palletkit seeds its randomness from the recipe name, so the same pallet comes out in every scene), sets up its room, lights and camera, then renders frame by frame to WebP. Output paths are relative to the repo root.

**Render with saved settings:** `python tools/render/run.py --list` shows every scene. Examples:
- `python tools/render/run.py mark`: renders all frames, then makes the phone versions.
- `python tools/render/run.py xray worlds`
- `python tools/render/run.py mark --test --frames 0,26,72,114,167`: half size, 24 samples, written to `.render-test/` (ignored by git).
- Then review with `node tools/shot/sheet.mjs public/dev/r5/mark sheet.png 3 1800 "^(000|040|080|120|167)\."`.

| Scene | Script | Output | Settings |
|---|---|---|---|
| The Mark film | `mark.py` | `public/dev/r5/mark/000-334.webp` (every half story frame) | 1600×900, 48 spp; 72 min on the PC |
| Round 6 A Daybreak | `daybreak.py` | `public/dev/r6/daybreak/00-47.webp` | 1920×1080, 64 spp |
| Round 6 B Neem shade | `neem.py` | `public/dev/r6/neem/00-47.webp` (loop) | 1920×1080, 64 spp |
| Round 6 C Bullet time | `bullettime.py` | `public/dev/r6/bullettime/00-60.webp` | 1920×1080, 48 spp; all three about 45 min on the PC |
| Round 7 A From the drawing | `blueprint.py` | `public/dev/r7/blueprint/00-21.webp` + `dims.json` | 1920×1080, 64 spp; photo and ink rendered apart, `compose_lines.py` lays the ink over in brand blue (run.py does it) |
| Round 7 B Eye level | `frieze.py` | `public/dev/r7/frieze/00-40.webp` | 1920×1080, 64 spp |
| Round 7 C Carved | `carved.py` | `public/dev/r7/carved/00-47.webp` | 1920×1080, 64 spp |
| Inner pages | `inspect.py --pass photo/generic/ids` (`run.py inner`) | `public/dev/inner/` | 1920×1200, 128 spp; ids.png: red = 10 × id |
| Anatomy (guide) | `layers.py --job film/orbit/orbit-ids` (`run.py anatomy`), then `python tools/render/trace_ids.py tools/render/out/anatomy-ids public/dev/inner/anatomy/outlines.json` | `public/dev/inner/anatomy/film` (48), `orbit` (72, every 5°), `outlines.json` (36, every 10°) | 1600×1000, 64 spp; IDs at 3200×2000, traced with OpenCV (`pip install opencv-python-headless`) |
| Round 8 A, C | `layers.py --job explode` / `--job assemble --recipe X` (`run.py r8-layers`) | `public/dev/r8/explode` (60 + `layers.json`), `public/dev/r8/assemble/<epal1|epal2|epal3|cp1>` (36 each) | 1920×1080, 64 / 48 spp |
| Round 8 B, D | `container.py --still`, `jaali.py --glide` (`run.py r8-more`) | `public/dev/r8/scenes/still.webp`, `public/dev/r8/glide` (72) | 2400×1350 / 1920×1080 |
| Round 9 | `r9.py --scene indigo/plan/upright/macro` (`run.py r9`) | `public/dev/r9/<scene>.webp` (+ `-sm`) | 2400×1350, 128 spp; about 25 s each |
| Catalogue (28 pallets) | `render_pallet.py` via `render_all.py` | `src/assets/products/<slug>/1-5.webp`, `public/models/<slug>.glb` | 1600 px, 128 spp; about 74 s per pallet (5 views + GLB) on the PC, 35 min for all |
| Container film | `container.py` | `public/dev/r5/container/000-149.webp` | 1600×900, 32 spp |
| In its place (hero B) | `anamorph.py` | `public/dev/r5/anamorph/00-60.webp` (frame 30 = sweet spot) | 1920×1080, 40 spp |
| Two worlds, Europe | `europe.py` | `public/dev/r5/worlds/europe.webp` | 2400×1350, 128 spp |
| Two worlds, India | `jaali.py --frames 24` | `public/dev/r5/worlds/india.webp` | 2400×1350, 128 spp |
| Look inside (hero C) | `xray.py --pass photo/xray/ids` | `public/dev/r5/xray/` | 2400×1350, 128 spp; ids.png: red = 10 × part number |
| Round 4 (archive) | `jaali.py`, `rann.py`, `resting.py` | `public/dev/r4/` | commands in each script's docstring |

Phone versions (`make_small.py`): films every second frame at 800×450 (`mark-sm`, `container-sm`), hero frames at 960×540 (`anamorph-sm`), stills at 1200×675 (`*-sm.webp`). Pages pick them on screens up to 900 px wide.

**Timings on the Mac (M4, 10-core GPU), rough:** Mark about 1 h in total (smoke frames about 45 s each, the rest about 15 s); container about 40 min; anamorph about 30 min; each 2400×1350 still 1–3 min.

**Timings on the PC (RX 9060 XT, HIP),** one full-quality frame per scene on 2026-11-23, each including about 3 s of scene setup: Mark smoke frame 26 s, plain frame about 6 s; container 9 s; anamorph 13 s; 2400×1350 stills 12–27 s; X-ray IDs 3 s. Estimated from those (not yet measured end to end): Mark about 25 min, container about 15 min, anamorph about 10 min.

**Lessons:**
- Always render one test frame at half size first (`--test`), look at it, then run the sequence.
- One Blender process at a time: on the Mac, three in parallel were slower than two.
- Volume smoke is slow: keep it to the frames that show it (`mark.py` fades it out by frame 56).
- Exposure: AgX "Medium High Contrast". Pale wood turns pink if overexposed.
- Seamless backgrounds use a world shader that shows a flat colour to camera rays, and a floor that fades into that colour with camera distance (no horizon line).
- A generated image must be saved to a file and reloaded before Cycles sees it (the `_*.png` files in `hero/`, now ignored by git).
- An anamorphic part must keep the depth order of the real pallet (deck closest, then stringer boards, blocks, bottom boards), or hidden parts show through.
- The scroll player must rest on whole frames, or a half cross-fade leaves a double image when scrolling stops.
- Blender on Windows resolves a relative output path from the drive root (`C:\`), not the working folder: keep every path handed to Blender absolute (`common.py` does this for `--out`; the textures and stamps already are).
- Freestyle (ink lines) draws nothing over holdout surfaces: for a lines-only pass give every surface a fully transparent material instead (`blueprint.py`). AgX shifts any line colour, so render the lines white on transparent and colour them afterwards (`compose_lines.py`).
- Exact booleans fail silently (the object renders empty) on a cutter with duplicate points or flipped faces: build cutters with bmesh and run `recalc_face_normals` (`frieze.py`, `carved.py`, `inspect.py`).
- The seamless studio's backdrop must be as bright as the lit floor, or a grey band shows where the floor fades out: about `bg_strength=3` for a white studio under AgX.

**Render rules from the owner (do not break; copied from the earlier catalogue handoff on the Mac):**
- Chamfers only where the official drawing has them; no generic bevels. Corner chamfer through every layer at that corner: EPAL 1 = 17 mm, EPAL 2/3 = 24 mm, CP = 20 mm, all at 45°.
- Outer bottom boards of EPAL-type pallets: chamfered only between the blocks, on the outer top edge, about 11 mm deep with curved run-outs. The pinewood middle bottom board has no chamfer. GMA notches are rounded.
- Approved look (5 Nov 2026): pale straight-grain spruce, 3 mm eased edges, small bright nails, a few knots on one deck board per pallet, CC0 textures Wood096 (pine) and Wood060 (hardwood). Wood095 was rejected. Never open the `.blend` files inside texture zips. If the look changes, test one pallet and get the owner's OK before re-rendering all 28.
- **Where the marks go (EPAL's own sheets; EPAL-licensed pallets only):** EPAL 1/2/3: EPAL oval on the left and right corner blocks; IPPC mark (plus licence number, year and month) on the centre block. CP1–CP9: IPPC mark on the left-hand corner block, CP type and EPAL ID on the centre block, EPAL oval on the right-hand corner block. Pinewood, hardwood, GMA and collar are not EPAL: IPPC mark only. Never stamp the company name on the pallets.
- **Open data issue:** for CP8/CP9 board counts, EPAL's sheets say 28 and 24 but the drawings give 21 and 18 (the renders follow the drawings). Settle it with the licence documents. Pinewood/hardwood/GMA/collar layouts were measured from a reference range; the owner's production drawings win.
- **Content rules from that handoff:** specs may match Jay Wood's range, but all text must be original (never copy their text or images). Use real names (EPAL 1/2/3, CP1–CP9, "pallet collar"). Never reuse Ambica's page text or photos. EPAL load ratings only on licensed pallets.

**Launch re-render (blocker):** once the EPAL licence and Pallet Euro's own HT code exist, set `tools/render/brand.json` (`ippc.code`, marks) and re-render everything: the hero scenes and films via `run.py`, and the 28 catalogue products plus GLBs via `python tools/render/render_all.py` (set `"glb": true` in `brand.json`, or pass `--glb`). The catalogue renderer came from the Ambica repo on 2026-11-23 (`render_pallet.py`, `pallets.py`, `make_stamps.py`; Metal-only GPU code replaced, output paths made absolute). `make_stamps.py` redraws the IPPC stamp from `brand.json` once the real HT code exists. `brand.json` holds EPAL's mark layouts for EPAL 1–3 and CP1–CP9.

## 9. Open questions waiting on the owner

- Round 9 (asked 2026-11-23): #67 which picture becomes the hero (D "Close-up" recommended). Full text: `docs/decisions.md`.
- Round 2 (still open): domain, own factory address/phones/email, which EPAL products the licence covers, status of the other certificates (numbers, issuers, validity, scans), trademark ® or ™, what "SOP" and "IIP" mean, whether to mention 20+ years of experience, real figures (capacity, area, HT chamber, people), launch timing.

## 10. Not in this repo (on the Mac only)

- **Ambica site repo** `/Users/wewake/VSC/APIPL/apiplSite`: the original 28-product render pipeline and assets. What this project uses is already copied in: `palletkit.py` (lines 1–741 of its `render_pallet.py`), textures, stamps, geometry, catalogue data, dev renders (one cut-out per pallet plus some extra views, `src/assets/dev-renders/`). Since 2026-11-23 also the batch catalogue renderer (`render_pallet.py`, `pallets.py`, `make_stamps.py`, stamp artwork; fetched read-only from GitHub `WeWake1/apiplSite`, which this PC's git login can read). **Deliberately not copied:** Ambica's 28 GLB models and its 5-view catalogue renders (they carry `IN-083 HT`; `render_all.py` regenerates both with Pallet Euro's dev marks). Never edit that repo, and never let it show on this site.
- There are no `.blend` files to carry: every scene is built by a script, so the round-4/5 renders can be remade from this repo alone (proven on the PC on 2026-11-23).
- **Earlier Pallet Euro attempt** `github.com/WeWake1/PalletEuro`: EPAL stamp setup, product copy, guides. Reuse data and copy only, not its design.
- **OpenSEO** (`../open-seo` next to this folder on the Mac, cloned from `github.com/every-app/open-seo`) with the owner's DataForSEO key in `.env.local`. On the PC: clone it next to this repo, copy `.env.example` to `.env.local`, paste the key (never commit it), follow its README. DataForSEO gives $1 free credit; the minimum top-up is $50.
- **Claude's memory files** on the Mac: their content is now in section 5.
- **The chat transcripts** of the earlier sessions: not copied. This file, `docs/decisions.md` and `docs/prototypes/README.md` hold what matters from them.

## 11. Next steps (when the owner is ready)

1. Get the round-9 pick and design the motion for that picture; another round if nothing wins (keep what landed in mind, section 5: simplicity, one pallet, calm space; rounds 4 and 6 moved the light every possible way, and the owner is tired of heroes that move with the cursor).
2. Build the production home page around the chosen hero:
   - deferred frame loading and lighter (AVIF) frames on phones;
   - Lighthouse mobile 99–100;
   - SEO tags and schema without Ambica links;
   - the `noindex` launch gate kept on.
3. Keyword research with OpenSEO, then the inner pages (Products with the Line and the X-ray lens; Certifications; About; Contact/Quote with the PHP form; Guides).
4. Launch blockers (`docs/decisions.md`): EPAL licence certificate; re-render all renders and GLBs with Pallet Euro's marks; real company details; delete the prototype (`src/pages/prototype/`, `src/components/proto/`, `src/layouts/Proto.astro`, `src/assets/dev-renders/`, `public/dev/`).

## 12. Session log

- **2026-11-06/07:** Kickoff. Brief, EPAL register research, skills installed (`.claude/skills/`), stack chosen, Astro scaffold, OpenSEO cloned. Round 1 (dark) was rejected; rounds 2 and 3 were built and judged.
- **2026-11-07:** Round 4, the first photoreal Blender heroes (new `palletkit.py`, `tools/render/hero/`). Indian light became the fallback.
- **2026-11-07/08:** Round 4 archived. Round 5 built: three heroes plus the Mark and container scroll films. About 3 h of GPU renders; the Mac slept twice mid-queue. Docs and decisions updated.
- **2026-11-23:** Prepared the move to the Windows PC.
  - Added this handoff file and pointed CLAUDE.md at it.
  - `common.py` now picks the GPU automatically (Metal / OptiX / HIP / CUDA / oneAPI).
  - Added `tools/render/run.py` (saved render settings) and `make_small.py` (phone versions).
  - Moved the review scripts into `tools/shot/` (puppeteer-core as a dev dependency).
  - Git: ignore Python caches and generated textures; `.gitattributes` for line endings; `.nvmrc`; `npm run proto`.
  - Found the GitHub repo is public. The owner chose to keep it public, and to commit and push themselves (`docs/decisions.md` #29–#30).
- **2026-11-23 (on the Windows PC):** Set up and verified the PC (section 3).
  - Fixed two Windows-only render bugs in `common.py`: frames were written under `C:\` instead of the repo, and Cycles also used the CPU's built-in GPU (about 25% slower).
  - Every round-5 scene renders on the RX 9060 XT; frames match the Mac's. The PC's timings are in section 8.
  - The site type-checks and builds; the review scripts run (hero B, desktop and phone: 0 errors, 0 overflow).
  - Kept Node 22.23.5.
  - Later the same day (owner: "stop the old dev server, install whatever you want, start the final home page"):
    - Stopped the stale dev server; installed cwebp.
    - Built the production foundation (section 7). Mobile Lighthouse 100/100/100 (SEO 69 = the `noindex` gate).
    - Two small visual changes from the prototype: grey small text darkened for contrast (`--ink-3` #7a8396 → #667085); phone header shows logo and Menu only.
    - Re-asked the round-5 questions and asked #35–#38.
- **2026-11-23 (evening, PC):** Round-5 verdict (#39–#47): heroes turned down, both scroll stories loved.
  - Mark film re-rendered with 335 frames (smoother scroll; `mark.py` samples every half story frame).
  - Round 6 built and rendered: Daybreak, Neem shade, Bullet time (`docs/prototypes/README.md`). Round 5 archived at `/prototype/round-5/`.
  - Product URLs now carry "epal" for EPAL-licensed products (`productPath()` in `range28.ts`).
  - Catalogue renderer brought over from GitHub `apiplSite`; tested on EPAL 1 and CP3 (views + GLB) on the Radeon. `brand.json`: EPAL 2/3 and CP mark layouts.
  - Waiting: round-6 questions #48–#50.
- **2026-11-23 (night, PC):** Round-6 verdict (#51–#53): no hero ("good, but not up to what we want"); the X-ray and Two worlds ideas kept only if refined; catalogue render approved.
  - Round 6 archived at `/prototype/round-6/`. Round 7 built and rendered (`blueprint.py`, `frieze.py`, `carved.py`; `compose_lines.py` colours the drawing's ink).
  - Inner-page demos at `/prototype/inner/`: the part inspector (`inspect.py` photo + ID map, `Inspect.astro`, `epal1-parts.ts`) and before/after (`inspect.py --pass generic`, `BeforeAfter.astro`).
  - Catalogue rendered: 28 × 5 views + 28 GLBs with dev marks (35 min). Not used by any page yet (#57).
  - Shared sawdust helper moved into `common.py` (`grains`, `set_grains`). New review script `tools/shot/inner.mjs`.
  - Waiting: round-7 questions #54–#57.
- **2026-11-23 (late night, PC):** Round-7 verdict (#58–#62): no hero, and no more cursor-driven heroes; the owner picked four kinds of motion for round 8.
  - Round 7 archived at `/prototype/round-7/`. Round 8 built: `layers.py` (explode, assemble, film, orbit, orbit-ids), `container.py --still`, `jaali.py --glide`; components in `r8/`.
  - Anatomy viewer replaces the inspector (`Anatomy.astro`, `trace_ids.py`, OpenCV installed). Product cards switched to the catalogue renders.
  - Lesson: a render started with a trailing `&` in the Bash tool keeps running; two queues then share the GPU at half speed. Start long renders only with the tool's background option.
- **2026-11-23 (round-8 verdict, PC):** #65–#66. Round 8 archived at `/prototype/round-8/`; round 9 = four bold stills (`r9.py`, `r9/HeroStill.astro`), motion to follow the pick. Anatomy fixed: nothing selected by itself, selections clear (same item again, empty space, Esc), smooth eased turning on 72 angles. Waiting: #67.

## 13. Updating this file

At the end of each session: rewrite section 1 to match reality; add one line to section 12 (date, what changed, what is waiting); update sections 7–8 when code or render settings change; move answered questions out of section 9 (the full answers go in `docs/decisions.md`). Keep it short enough to read in five minutes.
