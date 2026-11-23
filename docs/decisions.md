# Decisions log

Owner answers, newest first. Never re-ask anything answered here.

## 2026-11-23 (late night: round-7 verdict)

| # | Question | Answer |
|---|---|---|
| 58 | (#54) Round 7 hero: A "From the drawing"? | **Another round.** Round 7 is "good", but not the final hero. **"All the different designs using the same move-your-cursor thing is getting boring: try something new."** |
| 59 | Round 8: which kinds of motion? | **All four offered:** a scroll story (computers: the hero changes as you scroll, like the Mark film; phones: plays once), scenes that advance by themselves (made in India → loaded → in Europe), tap to transform (tap a product name, the pallet rebuilds itself into it), and plays by itself (one seamless cinematic loop). One hero per motion, no cursor scrubbing. |
| 60 | (#55) The part inspector on every product page? | **No: "kind of unnecessary" there.** It lives on **one guide page** ("What makes an EPAL pallet": every part and size), linked from the EPAL product pages. It is "pretty good", but needs: (1) a better, polished highlight (the blue fill and jagged outline do not look polished); (2) more than one isometric view, since not every part is visible; (3) a way to show the parts layer by layer; (4) an exploded 3D view to interact with, or a playable animation of it. |
| 61 | (#56) Before and after on the About page, with the draft copy? | **Yes:** "the before and after is good." |
| 62 | (#57) Product cards to the new catalogue renders now? | **Yes.** Done the same night (`Range.astro`, production and prototype). |

Claude's calls (round 8 and the anatomy viewer):
- One hero per kind of motion, all with the same headline and copy, none moving with the cursor: A "Built in layers" (scroll story: pinned on computers, the EPAL 1 comes apart into its layers with a small name tag on each; phones play it once), B "The journey" (three scenes advance by themselves with a slow push-in: round 7's sandstone courtyard "Made in India", a new container still "Loaded for export", round 5's European warehouse "To Europe's standard"), C "The family" (EPAL 1, EPAL 2, EPAL 3 and CP1: a tap sends the parts of the pallet flying up and drops the new one in, layer by layer; it changes by itself until the first tap), D "Living photograph" (round 4's Indian light, the owner's favourite so far, as a slow camera glide that plays forward and back with no input).
- Anatomy viewer (guide page): photoreal frames only, no live 3D (the owner found live 3D fake in round 3): a 48-frame exploded-view film, 36 angles of the exploded pallet to drag or turn, "Layer by layer" with each layer's parts, sizes and a one-line note; the highlight is a vector outline (white edge, blue line) traced from an ID map, with the rest of the pallet softly veiled.
- B's scene captions say only "Made in India", "Loaded for export" and "To Europe's standard": no claim of customers or exports yet.

### Open questions (round 8, asked 2026-11-23)

63. Round 8 hero: A "Built in layers"? (Alternatives: B "The journey", C "The family", D "Living photograph", or a mix, e.g. one as the hero and another further down the page.)
64. The anatomy viewer (`/prototype/inner/?variant=A`) as built, for the guide page "What makes an EPAL pallet"?

## 2026-11-23 (night: round-6 verdict)

| # | Question | Answer |
|---|---|---|
| 51 | (#48) Round 6 hero: B "Neem shade"? | **No hero chosen:** "good, but still not up to what we want." **Another round**, keeping round 6 and every earlier round saved. Round 6 archived at `/prototype/round-6/`; round 7 built the same night. |
| 52 | (#49) Reuse the X-ray lens on product pages and "Two worlds" on About? | **"Maybe", but refined a lot.** X-ray: "looks very cartoonish"; keep the idea of moving the cursor over the parts to see details, but make it **technical, professional and clean**. Two worlds: don't just change the room, **change the pallet: before = a generic, non-EPAL pallet, broken or damaged; after = our clean EPAL pallet.** Both rebuilt as demos at `/prototype/inner/`. |
| 53 | (#50) Render the full catalogue now on the PC? | **Yes.** Done: 28 pallets × 5 views (the collar 4) in `src/assets/products/<slug>/`, and 28 GLB models in `public/models/`, all with the dev marks (EPAL oval, `IN-XXX`). |

Claude's calls (round 7 and the inner-page demos):
- Round 7 keeps the brief "two simple, one crazy cool", but **moves something other than the light** (rounds 4 and 6 all moved the sun or shade): A "From the drawing" (a deep-blue technical drawing of the EPAL 1 turns into the real pallet part by part, in assembly order, with its dimension lines; the brand blue finally appears in the hero picture), B "Eye level" (the camera on the courtyard floor at the pallet's own height, the long side as a frieze with its three branded blocks, a sunlit sandstone arcade with pointed arches behind), C "Carved" (a solid slab of spruce the size of an EPAL 1 turns to sawdust and reveals the pallet inside).
- Inspect (product page): the real photo stays; the part under the cursor gets a thin blue outline and a small label with its name and size; a plain HTML parts table (names, sizes in mm, quantities from EPAL's drawing) lights up with it.
- Before and after (About): same studio, same camera, same light; a generic unmarked worn pallet (grey timber, grime and mould, a missing and a broken deck board, a split-off corner, a twisted block, rusty nails standing proud) against the EPAL 1, with a drag handle. Draft copy uses only what the pictures show and the EPAL facts already checked.

### Open questions (round 7, asked 2026-11-23; answered the same night: #58–#62 above)

54. Round 7 hero: A "From the drawing"? (Alternatives: B "Eye level", C "Carved", another round, or round 4's "Indian light".)
55. Inspect (`/prototype/inner/?variant=A`): use it on every product page, each with its own photo and parts list?
56. Before and after (`/prototype/inner/?variant=B`): use it on the About page, with the draft copy?
57. Swap the product cards on the home page to the new catalogue renders now? They carry Pallet Euro's dev marks; the cards still use the copies from the old catalogue with `IN-083 HT`.

## 2026-11-23 (evening: round-5 verdict)

| # | Question | Answer |
|---|---|---|
| 39 | Round 5 hero: B "In its place"? | **No: B disliked.** No hero chosen yet. The owner likes **the simplicity of round 2's A (Studio) and round 4's A (Indian light)** and wants a new round: **two new, unique heroes built on that simplicity, and one "crazy cool" one.** Built the same day as round 6 (`docs/prototypes/README.md`). |
| 40 | The Mark scroll story as built? | **"Absolutely yes, I love it"**, with **more frames so it is smoother.** Done: 335 frames instead of 168 (every half story frame; phones 168 instead of 84). |
| 41 | The container scroll story as built? | **Yes, loves it.** |
| 42 | Reuse the heroes not chosen on other pages (Two worlds on About, the X-ray lens on product pages)? | The owner did not understand the question: asked again in plainer words. |
| 43 | Visible placeholders for company facts until the owner sends them; domain, address and phone first? | **Yes.** |
| 44 | (#35) Domain palleteuro.com, the owner's? | **Yes.** |
| 45 | (#36) Product URLs without "EPAL"? | **No: keep "EPAL" in the address.** Done: EPAL-licensed products get `/products/epal-1-euro-pallet-1200x800/`, `/products/epal-cp1-pallet-1000x1200/` …; the others keep their plain slug (`productPath()` in `src/data/range28.ts`). |
| 46 | (#37) Draft home title and description until the keyword research? | **Yes.** |
| 47 | (#38) Bring the batch catalogue renderer over from the Mac? | **Yes; fetch it from the apiplSite repo.** Done from GitHub (`WeWake1/apiplSite`, read only): `render_pallet.py`, `pallets.py`, `make_stamps.py`, the CP1–CP9 and EPAL 2/3 stamp artwork, and a new `render_all.py`. Ambica's 28 GLBs and catalogue renders were **not** copied (they carry Ambica's `IN-083 HT` and this repo is public): the PC regenerates both, with Pallet Euro's dev marks, in about 25 s per pallet. |

Claude's calls: round 6 = A "Daybreak" (white studio, the cursor carries the sun from sunrise to sunset), B "Neem shade" (lime-plaster courtyard under the moving shade of a neem tree), C "Bullet time" (a dropped EPAL 1 frozen as its corner meets the floor, sawdust in the air, the camera orbits). Two ideas were tried and dropped before showing: a long striped shadow (physically impossible with a 14 cm pallet) and a granite block landing on the pallet (the dust hid the product). `brand.json` now has EPAL's mark layouts for EPAL 2/3 and CP1–CP9 (dev marks).

### Open questions (round 6, asked 2026-11-23; answered the same night: #51–#53 above)

48. Round 6 hero: B "Neem shade"? (Alternatives: A "Daybreak", C "Bullet time", or round 4's "Indian light".)
49. (Re-asked #42) Use the two unused round-5 heroes inside other pages: the X-ray lens on each product page (move it over the pallet to see its inside and name each part), and "Two worlds" (the same pallet in a European and an Indian room) on the About page?
50. Render the full catalogue now on the PC (28 pallets × 5 views plus 3D models, with the dev marks) for building the product pages?

## 2026-11-23 (moving to the Windows PC)

| # | Question | Answer |
|---|---|---|
| 29 | The GitHub repo `WeWake1/Pallet-Euro` is public (EPAL-oval renders, `IN-083` renders and notes naming Ambica are visible). Make it private? | **Keep it public** (owner's choice, after the warning). Do not change visibility unless asked. |
| 30 | Commit and push the handoff work? | **No: the owner commits and pushes themselves.** |
| 31 | Round-5 questions | Owner will answer later; do not push for answers. |

The owner now also works on a Windows PC (AMD Radeon RX 9060 XT, 32 GB RAM) for heavier Blender renders. `docs/handoff.md` carries the context between machines.

Later the same day:

| # | Question | Answer |
|---|---|---|
| 32 | Stop the stale dev server and install the tools the PC needs? | **Yes: "you can install whatever you want."** |
| 33 | Start the parts of the production home page that do not depend on the hero (SEO tags and schema, the noindex gate, sitemap, the kept sections as production components)? | **Yes.** Built the same day (`docs/handoff.md`, section 7). |
| 34 | Round 5 | The owner asked to continue from where the work stopped: the round-5 questions were asked again (below). |

Claude's calls while setting up the PC (the owner said "read the handoff and continue"):
- Keep Node 22.23.5 there instead of replacing the system Node with 24 (every package accepts 22.23.4 or newer).
- Render on the dedicated GPU only (the RX 9060 XT without the CPU's built-in GPU: about 25% faster).
- Production home page: hero stand-in = a still of round 5's B; phone header = logo and Menu (the quote button moves into the menu below 560 px); grey small text darkened to pass WCAG contrast (#7a8396 → #667085).

### Questions asked 2026-11-23 (answered the same evening: #44–#47 above)

35. Domain: palleteuro.com, registered in the owner's name? (Canonical URLs, the sitemap and the schema already use it.)
36. Product page addresses: keep `/products/euro-pallet-1200x800/` style (sizes, no "EPAL" in the address, so no URL changes if the licence covers fewer products)?
37. Home page title "EPAL Euro Pallets, Made in India | Pallet Euro Packaging" and the draft description: keep until the keyword research?
38. The batch catalogue renderer is only on the Mac: copy it into this repo next time on the Mac (scripts only, Ambica names removed), so the launch re-render of all 28 pallets and their 3D models can run on the PC?

## 2026-11-07 (after round 4)

| # | Question | Answer |
|---|---|---|
| 21 | Round 4 heroes | **A (Indian light) is "still good enough"**: it stays the fallback hero. **B (On the headline) and C (White desert) disliked.** Wants another round of new, creative hero ideas. |
| 22 | R4-2 Renders | **Yes.** Photoreal renders for everything visitors look at; live 3D only for "drag to rotate" on product pages, loaded on tap. |
| 23 | R4-3 The Mark | **Yes**, as a scroll story right after the hero, Apple-style: pinned and scrubbed by scrolling on computers, plays once by itself on phones. The owner especially wants to see it "moving in action with some creativeness". |
| 24 | R4-4 Container | **Yes, and make it a scroll story too**, the same way as the Mark, in the "Your next container" band at the end of the home page. |
| 25 | R4-5 The Line | **Yes**, on the Products page. |
| 26 | R4-6 Pages | **Yes**: Home, Products (one page per pallet), Certifications (one page per certificate), About, Contact/Quote, Guides. |
| 27 | R4-7 Typeface | **Yes**: Urbanist everywhere; condensed capitals only for big statement bands. |
| 28 | Archive | Round 4 kept for reference at `/prototype/round-4/` and in `docs/prototypes/round-4-heroes/`. |

EPAL facts checked for the Mark captions (EPAL's EPAL 1 page, 7 Nov 2026): 11 boards, 9 blocks, "the position of the 78 nails used is stipulated"; 1200 × 800 × 144 mm, approx. 25 kg, safe working load 1,500 kg; EPAL calls the markings "branded markings"; the ISPM 15 HT mark sits on both middle blocks of the long sides; the EPAL control staple is mandatory; all new EPAL Euro pallets have been heat treated to ISPM 15 since 1 Jan 2010. EPAL's product sheets put "EPAL in oval" on the left and right corner blocks, and the EPAL ID (licence number, year, month) on the middle block.

Round 5 (three new heroes: Two worlds, In its place, Look inside; plus the Mark and container scroll stories) is described in `docs/prototypes/README.md`.

### Open questions (round 5, asked 2026-11-08)

1. Hero: B "In its place" (the anamorphic gallery)? Alternatives: A "Two worlds", C "Look inside", or round 4's A "Indian light" (the fallback).
2. The Mark scroll story as built (brand, IPPC HT mark, fly under the deck, whole pallet), captions as written?
3. The container scroll story as built, ending on the deep-blue quote card?
4. Reuse the two heroes not chosen: "Two worlds" on the About page, "Look inside" (the X-ray lens) on every product page?
5. Next: once the hero is chosen, build the production home page (phone loading, Lighthouse 99–100, SEO tags), then the inner pages?
6. Company facts (round-2 questions 1–9): keep visible placeholders until the owner sends them; the domain, address and phone are needed first?

## 2026-11-07 (after round 3)

| # | Question | Answer |
|---|---|---|
| 17 | Round 3 heroes | None is hero-worthy. **C (The Mark)** is good: reuse it as an Apple-style scroll section after the hero. **A (The Line)** is good: reuse it on a products or certifications page. **B (The Stack)** and **D (The Container)** disliked; the container idea may go into the "Your next container, on EPAL pallets" band. |
| 18 | 3D quality | The owner noticed the live 3D (wood, container) looked "low quality, fake, non-realistic". Round 4 therefore uses photoreal Blender renders only (pre-rendered frames). Where live 3D stays is open question R4-2. |
| 19 | One page or many | **Multi-page site** (SEO): separate pages for products, certifications, about, contact and so on. Finish the hero and the whole home page first, then the other pages. |
| 20 | Archive | Round 3 kept for reference at `/prototype/round-3/` and in `docs/prototypes/round-3-heroes/`. |

Round 4 (three photoreal heroes: Indian light, On the headline, White desert) is described in `docs/prototypes/README.md`.

Round-4 questions 1–7 were all answered on 2026-11-07: see #21–#27 above.

## 2026-11-07 (after the light prototype, round 2)

| # | Question | Answer |
|---|---|---|
| 13 | Hero headline | **"Europe’s standard pallet, made in India."** Keep this wording. |
| 14 | Hero concepts | None of the three. The five-angle turntable is "good but generic". New, very unique hero concepts needed. |
| 15 | Sections to keep | **Product cards after the hero (A)**, **"Certified at every step" (B)**, **"Your next container, on EPAL pallets" as the quote band (C).** |
| 16 | Old prototypes | Keep them for reference (not as projects): `/prototype/round-2/` and `docs/prototypes/`. |

Round 3 (four new heroes: Line, Stack, Mark, Container) is described in `docs/prototypes/README.md`.

## 2026-11-07 (after the first prototype)

The owner rejected the first prototype entirely: all three dark directions (Register, Object, Port) and every UI element in them. "I clearly asked you to use light colour for the background." Claude had misread a contradictory line in the brief as dark. Redo from scratch.

| # | Question | Answer |
|---|---|---|
| 8 | Theme | **Light background.** Never dark. |
| 9 | Closest reference sites | **Jay Wood, We Are Pallets, Golden Pallet.** Many liked sites use video; Pallet Euro has none and never will, so show creativity without it. |
| 10 | First screen | Owner unsure ("idk"). The new prototype shows three first-screen options. |
| 11 | Motion | **Rich, premium** (smooth reveals, a hero that comes alive), lighter on phones. |
| 12 | Brand colour | **Deep blue.** |

## 2026-11-07

| # | Question | Answer |
|---|---|---|
| 1 | EPAL licence status for Pallet Euro Packaging | **Applied, in progress.** Not in EPAL's register yet. Site stays private/noindex until the licence certificate is issued. |
| 2 | Which pallets the site sells | **All 28, EPAL family first.** EPAL 1/2/3 and CP1–CP9 up front; pinewood, hardwood, GMA and the collar in a separate section with no EPAL marks. |
| 3 | Show the link to Ambica Patterns? | **No connection shown between the two companies.** |
| 4 | Keyword data for SEO | **Self-host OpenSEO now**, locally, with the owner's own DataForSEO key (the owner pastes the key). |
| 5 | Tech stack | Owner wants complete creative freedom and leaves the call to Claude. **Astro + TypeScript + React islands + Tailwind**, because Astro renders any React component and ships static HTML for SEO. |
| 6 | Skills | Installed in `.claude/skills/`: `grilling`, `prototype` (mattpocock), `karpathy-guidelines`. Not installed: gstack (heavy framework, overlaps with GSD, its install disables Chrome tools), elayadesign `landing-page-design` (forces a SaaS template). Their checklists are folded into `CLAUDE.md`. |
| 7 | Theme | ~~Very dark~~ Misread by Claude. **Superseded by #8: light background.** |

## Research facts (2026-11-07)

- EPAL's official licensee search lists **23 active licences in India**: 22 producers, 1 repairer. Codes run to IND-039. By product: Euro pallet 21, EPAL 3 8, CP 8, EPAL 2 4, EPAL 6 half 1, box 1.
- Bengaluru area: one licensee (GWP Solutions, Nelamangala, Euro pallets only). Nobody in Karnataka holds EPAL 2, EPAL 3 or CP.
- Jay Wood Industry holds IND-007 and IND-016 (Pune).
- EPAL licensing: €1,150 (processing + evaluation visit); should take no more than 3 months, 6 at most.
- DataForSEO: $1 free credit on sign-up; minimum top-up $50.

## Component shortlist (reactbits)

SplitFlapText (licence numbers, export ports), Counter (real figures only), Stack (certificates as documents), StatusMark (licence valid + checked date), Stepper and ElasticSlider (quote flow, container calculator). Maybe: HoloCard (EPAL licence card only), Topography (faint wood grain, if fast on phones). 3D stays on Google's model-viewer, loaded on tap.

## Open questions (round 2, asked 2026-11-07)

1. Domain: palleteuro.com, registered in the owner's name?
2. Factory: its own address, phones and @palleteuro.com email, separate from Ambica?
3. Which EPAL products does the application cover (EPAL 1, 2, 3, CP, half pallets, box)?
4. Status of the other seven (TM, SOP, PEFC, ISPM-15 HT, ISO, IIP, FSC): issued to Pallet Euro Packaging or still to come? Numbers, issuers, validity, scans.
5. Trademark: registered (®) or applied (™)? Class?
6. What exactly are "SOP" and "IIP" here?
7. May the site say the team has 20+ years of pallet-making experience, without naming any company?
8. Real figures to publish (capacity, area, HT chamber capacity, people) and whether factory photos/video exist.
9. Launch timing: build now on private staging, go public the day the EPAL certificate arrives?

## Light prototype (2026-11-07): heroes rejected, three sections kept (archived at `/prototype/round-2/`)

`/prototype/` (`?variant=A|B|C`, arrow keys). All light, deep blue `#0B3A9E`, rich motion. They differ mainly in the first screen (owner was unsure):

- **A · Studio** (We Are Pallets + Jay Wood): EPAL 1 render on pure white, cross-fading through its five studio angles like a turntable; licence card in the first screen; certification strip; product cards whose image turns on hover; certificate wall with a blue EPAL card. Urbanist.
- **B · Assembly** (Jay Wood): thin uppercase "Built to the EPAL standard"; a live 3D EPAL 1 builds itself from `pallet-geometry.json`, gets its EPAL and IPPC marks, shows its dimensions, then turns (drag to rotate); "Show the layers" pulls it apart. Spec sheet, draggable product rail, certificate list. Albert Sans + three.js.
- **C · Certified** (Golden Pallet): bold condensed headline on a deep-blue block; the eight certificates are the hero, a cycling stack of documents with Verify links; product explorer with family tabs. Sofia Sans (Condensed).

## First prototype (2026-11-07): REJECTED, deleted

All three were dark and the owner disliked every element. Kept here only so they are never repeated:

- **A · The Register:** passport-style record card for the EPAL 1, guilloche security linework, bilingual EN/DE labels, machine-readable zone, red rubber stamps, certificate ledger with a Verify link per row. Archivo (expanded) + IBM Plex Mono; ink black, paper white, stamp vermilion.
- **B · The Object:** "1200 × 800 × 144" numerals, low-angle pallet on black with engineering callouts, product lineup, three-view technical drawing generated from `pallet-geometry.json`, certifications as one statement with footnoted Verify links. Host Grotesk + Martian Mono; black and white, the wood is the only colour.
- **C · The Port:** split-flap "how many fit" board (real floor-fit maths, live floor plan), stencil wordmark, certificates as a "Cleared for Europe" board. Big Shoulders (+ Stencil) + Instrument Sans; night navy, sodium orange.

Render note for the later re-render job: the high-key studio light looks flat on black. A dark-site version wants a directional key light and deeper shadows, and a transparent background.

## Launch blockers

- EPAL licence certificate issued, and licence number known.
- Re-render all 28 products and GLBs with the EPAL marks and Pallet Euro's own HT code (current images carry Ambica's IN-083 HT). The round-4 hero frames (`public/dev/r4/`, from `tools/render/hero/`) carry the EPAL oval and the `IN-XXX` placeholder: re-render them too once the licence and HT code exist.
- Real company details: address, phones, WhatsApp, email, hours.
- Delete the prototype: `src/pages/prototype/`, `src/components/proto/`, `src/layouts/Proto.astro`, `src/assets/dev-renders/`, `public/dev/`, and the prototype rules in `src/styles/global.css`. The production components still use dev pictures (`Range.astro`, the hero stand-in in `src/pages/index.astro`, the EPAL stamp in `Hero.astro`): swap them for the re-render first.
- Certificates on the home page (`Certified.astro`): only the ones issued to Pallet Euro Packaging, with real numbers.
- Then set `LAUNCHED = true` in `src/data/site.ts` (drops `noindex`, opens `robots.txt`, adds the sitemap line).
