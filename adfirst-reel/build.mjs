/**
 * Builds the self-contained AdFirst reel.
 *
 * The wordmark in the supplied logo is set in Barlow Condensed SemiBold, which
 * isn't installed here and can't be fetched (no egress). So instead of
 * approximating it we lift the real glyphs straight out of the logo artwork:
 * Chromium decodes the JPEG, we key the charcoal background out to alpha, and
 * each of the seven letters is sliced on its column gap. That keeps the
 * wordmark pixel-faithful while still letting every letter animate on its own.
 *
 * Everything (glyphs, fonts, geometry) is inlined into reel.html so the file
 * can be opened, hosted or rendered anywhere with no sibling assets.
 *
 *   node adfirst-reel/build.mjs
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..');
const LOGO = path.join(HERE, 'brand', 'adfirst-logo.jpg');
const TEMPLATE = path.join(HERE, 'src', 'reel.template.html');
const OUT = path.join(HERE, 'reel.html');

/** Padding kept around each slice so antialiased edges aren't clipped. */
const PAD = 4;
const LETTERS = ['A', 'D', 'F', 'I', 'R', 'S', 'T'];

/** Weights pulled from the repo's Manrope set for the supporting copy. */
const FONTS = [
  ['Manrope', 500, 'assets/fonts/manrope-latin-500.woff2'],
  ['Manrope', 700, 'assets/fonts/manrope-latin-700.woff2'],
  ['Manrope', 800, 'assets/fonts/manrope-latin-800.woff2'],
];

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setContent('<body></body>');
const jpg = fs.readFileSync(LOGO).toString('base64');

// ---------------------------------------------------------------- geometry --
// Measure the mark rather than hard-coding it, so re-exporting the logo at a
// different size still produces a correct build.
const geo = await page.evaluate(async (jpg) => {
  const img = new Image();
  img.src = 'data:image/jpeg;base64,' + jpg;
  await img.decode();

  const W = img.width;
  const H = img.height;
  const cv = document.createElement('canvas');
  cv.width = W;
  cv.height = H;
  const ctx = cv.getContext('2d');
  ctx.drawImage(img, 0, 0);
  const d = ctx.getImageData(0, 0, W, H).data;
  const at = (x, y) => {
    const i = (y * W + x) * 4;
    return [d[i], d[i + 1], d[i + 2]];
  };
  const isCyan = ([r, g, b]) => b > 170 && g > 130 && r < 150 && b - r > 60;
  const isLight = ([r, g, b]) => r > 150 && g > 150 && b > 150 && Math.abs(r - b) < 40;

  // Cyan band: its vertical extent gives the rule, its column runs give the
  // two bars and the gap the dot sits in.
  let bandY0 = 1e9;
  let bandY1 = -1;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x += 3) {
      if (isCyan(at(x, y))) {
        bandY0 = Math.min(bandY0, y);
        bandY1 = Math.max(bandY1, y);
        break;
      }
    }
  }
  const barY = Math.round((bandY0 + bandY1) / 2);

  const cols = [];
  for (let x = 0; x < W; x++) if (isCyan(at(x, barY))) cols.push(x);
  const runs = [];
  let start = cols[0];
  let prev = cols[0];
  for (const x of cols.slice(1)) {
    if (x - prev > 3) {
      runs.push([start, prev]);
      start = x;
    }
    prev = x;
  }
  runs.push([start, prev]);

  // Dot: light pixels inside the gap between the two bars.
  const dot = { x0: 1e9, y0: 1e9, x1: -1, y1: -1 };
  for (let y = bandY0 - 80; y < bandY1 + 80; y++) {
    for (let x = runs[0][1]; x < runs[1][0]; x++) {
      if (isLight(at(x, y))) {
        dot.x0 = Math.min(dot.x0, x);
        dot.y0 = Math.min(dot.y0, y);
        dot.x1 = Math.max(dot.x1, x);
        dot.y1 = Math.max(dot.y1, y);
      }
    }
  }

  // Wordmark: the light band below the rule.
  const wordTop = bandY1 + 20;
  let wx0 = 1e9;
  let wx1 = -1;
  let wy0 = 1e9;
  let wy1 = -1;
  const colCount = new Array(W).fill(0);
  for (let y = wordTop; y < H; y++) {
    for (let x = 0; x < W; x++) {
      if (isLight(at(x, y))) {
        colCount[x]++;
        wx0 = Math.min(wx0, x);
        wx1 = Math.max(wx1, x);
        wy0 = Math.min(wy0, y);
        wy1 = Math.max(wy1, y);
      }
    }
  }

  // Letters = runs of columns that contain ink.
  const letters = [];
  let ls = null;
  for (let x = wx0; x <= wx1 + 1; x++) {
    if (colCount[x] > 0 && ls === null) ls = x;
    else if (colCount[x] === 0 && ls !== null) {
      letters.push([ls, x - 1]);
      ls = null;
    }
  }
  if (ls !== null) letters.push([ls, wx1]);

  return {
    source: [W, H],
    bar: { y0: bandY0, y1: bandY1, cy: barY, left: runs[0], right: runs[1] },
    dot,
    word: { x0: wx0, x1: wx1, y0: wy0, y1: wy1 },
    letters,
  };
}, jpg);

if (geo.letters.length !== LETTERS.length) {
  throw new Error(`expected ${LETTERS.length} glyph slices, measured ${geo.letters.length}`);
}

// ------------------------------------------------------------- glyph alpha --
// The artwork is flat #F5F5F5 ink on flat #282828. Mapping luminance back onto
// alpha recovers the original antialiasing instead of leaving a dark fringe.
const glyphs = await page.evaluate(
  async ({ jpg, word, letters, PAD }) => {
    const img = new Image();
    img.src = 'data:image/jpeg;base64,' + jpg;
    await img.decode();
    const src = document.createElement('canvas');
    src.width = img.width;
    src.height = img.height;
    const sctx = src.getContext('2d');
    sctx.drawImage(img, 0, 0);

    const BG = 40;   // #282828
    const FG = 245;  // #F5F5F5

    const cut = (x0, x1, y0, y1) => {
      const w = x1 - x0 + 1 + PAD * 2;
      const h = y1 - y0 + 1 + PAD * 2;
      const c = document.createElement('canvas');
      c.width = w;
      c.height = h;
      const cx = c.getContext('2d');
      const inp = sctx.getImageData(x0 - PAD, y0 - PAD, w, h);
      const out = cx.createImageData(w, h);
      for (let i = 0; i < inp.data.length; i += 4) {
        const lum = inp.data[i] * 0.299 + inp.data[i + 1] * 0.587 + inp.data[i + 2] * 0.114;
        const a = Math.max(0, Math.min(1, (lum - BG) / (FG - BG)));
        out.data[i] = 245;
        out.data[i + 1] = 245;
        out.data[i + 2] = 245;
        out.data[i + 3] = Math.round(a * 255);
      }
      cx.putImageData(out, 0, 0);
      return c.toDataURL('image/png').split(',')[1];
    };

    return letters.map(([a, b]) => ({ x0: a, x1: b, png: cut(a, b, word.y0, word.y1) }));
  },
  { jpg, word: geo.word, letters: geo.letters, PAD }
);

await browser.close();

// ------------------------------------------------------------------ inline --
const fontFaces = FONTS.map(([family, weight, rel]) => {
  const b64 = fs.readFileSync(path.join(REPO, rel)).toString('base64');
  return `@font-face{font-family:'${family}';font-style:normal;font-weight:${weight};font-display:block;` +
    `src:url(data:font/woff2;base64,${b64}) format('woff2');}`;
}).join('\n');

const payload = {
  pad: PAD,
  bar: geo.bar,
  dot: geo.dot,
  word: geo.word,
  glyphs: glyphs.map((g, i) => ({
    name: LETTERS[i],
    x0: g.x0,
    x1: g.x1,
    src: 'data:image/png;base64,' + g.png,
  })),
};

const html = fs
  .readFileSync(TEMPLATE, 'utf8')
  .replace('/*__FONT_FACES__*/', () => fontFaces)
  .replace('/*__BRAND_ASSETS__*/', () => JSON.stringify(payload));

fs.writeFileSync(OUT, html);

const kb = (n) => (n / 1024).toFixed(0) + 'KB';
console.log(`measured mark  : bar y${geo.bar.y0}-${geo.bar.y1}, runs ${JSON.stringify([geo.bar.left, geo.bar.right])}`);
console.log(`wordmark       : x${geo.word.x0}-${geo.word.x1} y${geo.word.y0}-${geo.word.y1}`);
console.log(`glyphs         : ${glyphs.map((g, i) => LETTERS[i]).join(' ')}`);
console.log(`wrote          : ${path.relative(REPO, OUT)} (${kb(fs.statSync(OUT).size)})`);
