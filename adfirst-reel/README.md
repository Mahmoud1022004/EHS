# AdFirst — brand reel

A 15-second vertical motion-graphics film for AdFirst, built as code so every
frame is reproducible and the copy can be re-cut without re-animating anything.

| | |
|---|---|
| Output | `adfirst-reel-1080x1920.webm` — 1080×1920, 30 fps, 15 s, VP8 |
| Source | `src/reel.template.html` — the animation |
| Preview | open `reel.html` in a browser; it loops on its own |

## Brand

Values are taken verbatim from `brand/Logo_Color_Guide.pdf`:

| Role | Value |
|---|---|
| Background | `#282828` |
| Accent (rules) | `#35C2FF` |
| Type / dot | `#F5F5F5` |
| Wordmark face | Barlow Condensed SemiBold |

Barlow Condensed isn't installed here and there's no network to fetch it, so
`build.mjs` lifts the **real glyphs out of the logo artwork** instead of
approximating them: Chromium decodes `brand/adfirst-logo.jpg`, the charcoal
background is keyed back to alpha from luminance (which recovers the original
antialiasing rather than leaving a dark fringe), and the seven letters are
sliced apart on their column gaps. The wordmark you see is therefore the
genuine typeface, and each letter can still animate independently.

The rules and the dot are redrawn live from measurements of the same file, so
they can move on their own while staying true to the lockup.

Supporting copy is Manrope (already in `assets/fonts/`) given a measured
horizontal compression so it sits with the condensed wordmark.

## Sequence

| Time | Beat |
|---|---|
| 0.0 – 2.1 s | Rules fly in from both edges and meet; the dot lands with a shockwave and a camera shake |
| 2.1 – 4.1 s | `ADFIRST` builds letter by letter out of the rule line |
| 4.1 – 7.0 s | *We don't chase attention. We command it.* |
| 7.0 – 10.0 s | Capabilities — strategy, creative, media, performance |
| 10.0 – 12.2 s | *Built for brands that refuse to blend in.* |
| 12.2 – 15.0 s | Logo lockup rebuilds, tagline resolves |

Scenes are separated by a curtain wipe made from the logo's own two rules.

## Editing

All wording lives in one `COPY` object near the top of the `<script>` in
`src/reel.template.html` — change the strings, rebuild, re-render. Beat times
live in the `T` object just below it.

```sh
node adfirst-reel/build.mjs      # artwork + fonts -> self-contained reel.html
node adfirst-reel/render.mjs     # reel.html -> webm
node adfirst-reel/render.mjs --preview   # key stills only, for a quick look
```

`render.mjs` takes `--fps`, `--scale` and `--ffmpeg` if you need to override
anything.

## How the render works

Playback is frozen and each frame is produced by calling `__seek(t)` with an
exact timestamp, then screenshotting. Nothing depends on how fast the machine
draws, so there are no dropped or doubled frames and re-running produces the
same file.

## Getting an MP4

This machine has no network and no general-purpose ffmpeg — only the VP8/WebM
build that ships with Playwright — so the deliverable is WebM. Any normal
ffmpeg will transcode it for Instagram/TikTok:

```sh
ffmpeg -i adfirst-reel-1080x1920.webm \
  -c:v libx264 -profile:v high -pix_fmt yuv420p \
  -crf 18 -preset slow -movflags +faststart \
  adfirst-reel-1080x1920.mp4
```

Re-rendering straight to H.264 is a one-line change to the `ff` args in
`render.mjs` once a full ffmpeg is on the path.

There is no audio track; drop a music bed on in the edit.
