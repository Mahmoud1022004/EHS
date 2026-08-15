# EHS — Egyptian Hospital Supplies · Website

Bilingual (English + Arabic RTL) static marketing website for **EHS — Egyptian Hospital Supplies**
(شركة مصر لإمداد المستشفيات) and its **MedPress** medical compression-stocking line.

No framework, no build server required to host — the site is plain HTML/CSS/JS and can be
uploaded to any static hosting (shared hosting, Netlify, Vercel, GitHub Pages, etc.).
Target domain on company material: **ehs-med.com**.

## Structure

```
ehs-website/
├── index.html …………………… English pages (18)
├── about / products / medpress / medpress-stockings /
│   mastercast-tube-grip / mastercast-cast-net / mastercast-elastic-bandage /
│   gauze-wound-care / medical-textiles / orthopedic / masks-ppe /
│   size-guide / how-to-wear / professionals / factory / faq / contact
├── ar/ ………………………………… Arabic versions of the same 18 pages (dir="rtl")
├── assets/
│   ├── css/style.css …………… design system (EHS brand tokens, RTL-ready)
│   ├── js/main.js ……………… nav, loader, reveal animations, demo forms
│   ├── fonts/ ………………………… self-hosted Manrope + IBM Plex Sans Arabic (woff2)
│   ├── img/ ………………………… optimized product photography (JPG)
│   ├── video/ ………………………… hero video (2.2 MB mp4) + poster
│   └── logos/ ………………………… EHS logo SVG/PNG set + favicons
├── loading-samples.html ……… internal demo of 6 loading-screen concepts (not linked publicly)
└── _build/ ……………………………… page generator (optional, for editing)
    ├── build.py
    └── content/en/*.html · content/ar/*.html
```

## Editing pages

Header, footer, and `<head>` metadata are generated from shared templates so all 22 pages stay
consistent. To change content:

1. Edit the page body in `_build/content/en/<page>.html` or `_build/content/ar/<page>.html`
   (or shared strings/nav/footer/meta in `_build/build.py`).
2. Run:

```bash
cd _build && python3 build.py
```

Editing the generated HTML directly also works — just remember the same change belongs in the
`_build/content/` source, or a future rebuild will overwrite it.

## Deploying a preview on Render

The repo is a plain static site, committed pre-built, so Render needs no build
step. `render.yaml` in the repo root already declares the service.

1. Render dashboard → **New → Static Site** → connect the private GitHub repo
   `Mahmoud1022004/EHS` (authorise Render for the repo if prompted).
2. Settings Render should pick up from `render.yaml` (or enter manually):
   - **Build command:** *(none / the placeholder echo)*
   - **Publish directory:** `.`
3. Deploy. Render gives a URL like `https://ehs-website.onrender.com` — share
   that with the client for review.

Every push to `main` redeploys automatically. After editing anything in
`_build/content/`, run `python3 _build/build.py` and commit the regenerated
HTML, otherwise the deployed pages stay unchanged.

## Local preview

```bash
python3 -m http.server 8741
```

Then open http://localhost:8741/ — Arabic version at http://localhost:8741/ar/.

## Loading screen — “The Care Line”

The support-line draws itself, the EHS monogram lands, the tagline fades in (~2.9 s).
It plays **once per browsing session**, is skipped for users with reduced-motion enabled,
is hidden entirely without JavaScript, and can be bypassed for testing with `?noloader=1`.
Other explored concepts remain viewable at `/loading-samples.html`.

## Confirmed by company documentation (Aug 2026)

From `COMPANY PORTFOLIO.docx` and `Factory Overview.docx` (now reflected on the site):

- [x] Founded **1988** + company timeline (About)
- [x] Vision & mission (About)
- [x] Leadership team names & roles (About — **verify Arabic spellings of names**)
- [x] Factory figures: 2,240 m² land, 2,462 m² built-up, 1,822 m² production,
      500 m² warehouse, 500 KVA, **10 production lines, 60+ employees** (Quality)
- [x] Product portfolio: gauze & wound care, elastic bandages, compression therapy
      (MedPress), orthopedic products, face masks & PPE (Products)
- [x] Markets served incl. UPA, government healthcare, military (Professionals)

## Before going live — still awaiting confirmation

Everything marked **“to be confirmed”** on the site is a deliberate placeholder.
Do **not** publish real values until the company owner provides documentation:

- [ ] Compression class / mmHg values
- [ ] Material composition and care label
- [ ] Additional formats, colors, and exact short/long length measurements
- [ ] **WhatsApp number** — the floating WhatsApp button and contact links currently use a
      PLACEHOLDER (`WHATSAPP_NUMBER` in `_build/build.py`). Replace with the confirmed
      number (digits only, international format) and rebuild before launch.
- [ ] Phone numbers and email addresses (none are published on the site yet)
- [x] Face-mask range photography — cropped from the supplied banner (Aug 2026).
      NOTE: the FFP2 respirator tile was deliberately **excluded** — it carries a printed
      "CE 2834" marking, and the site must not display CE claims until certification
      documents are provided.
- [ ] Points of sale / where-to-buy list
- [ ] Certifications & regulatory registrations (none are claimed on the site —
      the portfolio mentions quality systems but names no certificates)
- [ ] Concept products (abdominal support, lumbar support, surgical towels) — currently
      shown only as clearly-labelled “in development” previews on the Products page
- [ ] Real factory photo for the Quality page (the polished gate photo shared on WhatsApp —
      save it into the project and it can replace the macro image)
- [ ] **Arabic medical and regulatory text must be professionally reviewed before publication**
- [ ] Size-chart values — currently shown exactly as printed on the existing MedPress packaging

## Activating the contact / enquiry forms

Both forms run in **preview mode** (nothing is sent — a notice tells the visitor).
When contact channels are confirmed: point the forms at a form backend or the ehs-med.com
mail server and remove the demo handler — see the `data-demo-form` comment in
`assets/js/main.js` and the `<form data-demo-form>` blocks in the professionals/contact pages.

## MasterCast product galleries

Each MasterCast product (Tube Grip, Cast-Net, Elastic Bandage) has its own page and a
strictly separate gallery — images are never shared between products. The organized
source library lives in `~/Desktop/EHS/products/` with per-product category folders
(product-only, box-front, box-angle, box-with-product, lifestyle, hero).
`product-only` and most `box-angle` images were derived by cropping the supplied
box-with-product photos. **Missing:** a dedicated Cast-Net box-angle shot (mesh overlaps
the label in the source photo, so no clean crop exists) — a generation brief is in
`products/cast-net/box-angle/NEEDED.md`.

## Notes

- Fonts are self-hosted (no Google Fonts calls at runtime) — good for privacy and load speed.
- Every page carries `hreflang` EN↔AR alternates and Open Graph tags; URLs assume
  https://ehs-med.com — adjust `BASE_URL` in `_build/build.py` if the domain changes.
- The medical disclaimers required by the brief appear on product pages and in every footer.
- Hero video: `assets/video/medpress-hero.mp4` (re-encoded from the 15.6 MB original to 2.2 MB,
  poster frame included, no logos/text baked into the footage as required).
