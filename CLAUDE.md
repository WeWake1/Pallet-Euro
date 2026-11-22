# Pallet Euro Packaging website

Website for **Pallet Euro Packaging** ("Pallet Euro" large, "packaging" small), a new Indian company focused on EPAL pallets. Goal: be the name every Indian buyer thinks of for EPAL pallets. SEO is the top priority, on every decision.

**Start every session by reading `docs/handoff.md`** (current status, what is waiting on the owner, setup on a new machine, render pipeline, session log), then `docs/decisions.md` (every owner answer and open question; never re-ask an answered question). The owner works on two machines (a Mac and a Windows PC with an AMD Radeon RX 9060 XT) and moves between them with git, so **end every session by updating `docs/handoff.md`** (Status and a Session log line) before committing.

## Working with the owner

- Ask at every decision. Use the `grilling` format: numbered questions, each with a recommended answer, worded so "yes" accepts it.
- For visual or motion choices, show a working demo (`prototype` skill: variants on one route, `?variant=` switcher), not a description.
- Log every answer in `docs/decisions.md` the same day.

## Hard rules

1. **No connection to Ambica Patterns India Pvt Ltd, anywhere.** No name, address, phone, email, photos, text, links, schema `sameAs`/`parentOrganization`, founding year 2001, or the IPPC code `IN-083`. Pallet Euro stands alone.
2. **EPAL licence is applied for, not granted.** EPAL's stipulations forbid using the "EPAL in oval" mark for advertising before the licence is granted. Nothing with the EPAL oval or EPAL claims goes public until the licence certificate exists. Keep the launch gate (`noindex`, private staging) on until then.
3. **Certificates:** show only what is issued to Pallet Euro Packaging itself, each with number, issuer, valid-until date and a Verify link to the official register. Never use the ISO logo (show the certifier's mark). FSC/PEFC logos only with a licence code and certifier approval. ® only once the trademark is registered, ™ before.
4. **Never invent facts:** no made-up numbers, clients, testimonials, dates or certificate numbers. Use visible placeholders like `{{capacity}}`.
5. **Product names:** "EPAL ..." only for products the EPAL licence covers. Non-EPAL pallets (pinewood, hardwood, GMA, collar) get plain names and no EPAL marks.
6. **Renders are dev-only for now.** The images and GLBs copied from the Ambica repo carry Ambica's `IN-083 HT` mark. Re-render with the EPAL marks and Pallet Euro's own HT code before launch. Render rules: `docs/handoff.md`, section "Render rules".
7. **Phones:** Lighthouse mobile 99–100. No scroll-driven or pinned animation on phones, no Lenis smooth scroll, no dot-grid background (all rejected before). 3D models load only on tap on touch devices.

## Design: avoid AI slop

The look must be unique, premium and minimal, on a **light background** (never a dark theme), with **deep blue** as the brand colour and rich, premium motion. References the owner likes most: Jay Wood, We Are Pallets, Golden Pallet. There is no video and never will be: liveliness comes from renders, 3D models and animation. The first three dark prototypes were rejected entirely; do not reuse their ideas (see `docs/decisions.md`). Do not use:

- glow/aurora/beam/galaxy backgrounds, radial halos, dark-mode glows, gradient or shiny text
- the 3-column icon-title-text feature grid, icons in coloured circles, bento grids, nested cards
- logo marquees, "hero eyebrow" chips, three big numbers with tiny labels under the hero
- frosted glass everywhere, uniform bubbly radius, gradient buttons, stock-photo heroes
- generic copy ("Welcome to", "Unlock the power of", "world class", "cutting edge", "seamless")
- fake testimonials, avatars or star ratings

Use reactbits/21st.dev components only when they do a real job (shortlist in `docs/decisions.md`).

## Stack

Astro + TypeScript, React islands for interactive parts, Tailwind CSS. Static build for Hostinger, one PHP file for the quote form. All content must be in the static HTML (no client-only rendering of text or links).

## Asset sources

- Pallet geometry, render pipeline, 28 product renders and GLBs came from the Ambica site repo, which exists only on the owner's Mac (`/Users/wewake/VSC/APIPL/apiplSite`: `tools/render/`, `src/data/products.json`, `src/assets/products/`, `public/models/`). What this project needs is already copied in (see `docs/handoff.md`, "Not in this repo"). Copy assets; never edit that repo.
- Earlier Pallet Euro attempt (EPAL stamp setup `tools/render/brand.json`, `stamps/`, product copy, guides): `github.com/WeWake1/PalletEuro`. Reuse data and copy only, not its design.
- This repo's render tools: `tools/render/palletkit.py` (the Ambica builder, importable in Blender; marks from `tools/render/brand.json`), the scenes in `tools/render/hero/`, and `tools/render/run.py`, which renders any scene with its saved settings on either machine (Cycles on Metal on the Mac, HIP on the Radeon). Pictures people look at are photoreal Blender renders; live WebGL looked fake to the owner (round 3).
- Review tools: `tools/shot/sheet.mjs` (contact sheet of frames) and `tools/shot/shots.mjs` (page screenshots, console errors, overflow) with headless Chrome.
