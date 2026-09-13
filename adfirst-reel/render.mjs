/**
 * Renders reel.html to video, one exact frame at a time.
 *
 * Playback is frozen and every frame is produced by calling __seek(t), so the
 * output is deterministic and independent of how fast the machine draws — no
 * dropped or doubled frames, and re-running gives a byte-comparable result.
 *
 *   node adfirst-reel/render.mjs                 # full render
 *   node adfirst-reel/render.mjs --preview       # key stills only, for review
 *   node adfirst-reel/render.mjs --fps 24 --scale .5
 */
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PAGE = 'file://' + path.join(HERE, 'reel.html');

const argv = process.argv.slice(2);
const flag = (name, fallback) => {
  const i = argv.indexOf('--' + name);
  return i === -1 ? fallback : argv[i + 1];
};
const PREVIEW = argv.includes('--preview');
const SCALE = parseFloat(flag('scale', '1'));

/* Playwright ships an ffmpeg; it is VP8/WebM only, which is what we target. */
const FFMPEG = flag('ffmpeg', '/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux');

const browser = await chromium.launch({
  args: ['--force-device-scale-factor=1', '--hide-scrollbars', '--disable-lcd-text'],
});

const page = await browser.newPage({ viewport: { width: 100, height: 100 } });
await page.goto(PAGE, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);

const meta = await page.evaluate(() => window.__meta);
const FPS = parseInt(flag('fps', String(meta.fps)), 10);
const W = Math.round(meta.width * SCALE);
const H = Math.round(meta.height * SCALE);

await page.setViewportSize({ width: W, height: H });
await page.evaluate(() => window.__freeze());
await page.waitForTimeout(120);

/* ------------------------------------------------------------------ stills -- */
if (PREVIEW) {
  const dir = path.join(HERE, 'preview');
  fs.mkdirSync(dir, { recursive: true });
  const marks = [0.55, 1.02, 1.30, 2.60, 3.60, 4.25, 5.10, 6.30, 7.40, 8.60,
                 9.60, 10.60, 11.60, 12.40, 13.40, 14.60];
  for (const t of marks) {
    await page.evaluate(t => window.__seek(t), t);
    const name = `t-${t.toFixed(2).replace('.', '_')}.jpg`;
    await page.screenshot({ path: path.join(dir, name), type: 'jpeg', quality: 88 });
  }
  console.log(`wrote ${marks.length} stills -> ${path.relative(path.resolve(HERE, '..'), dir)}`);
  await browser.close();
  process.exit(0);
}

/* ------------------------------------------------------------------ video -- */
const total = Math.round(meta.duration * FPS);
const out = path.join(HERE, `adfirst-reel-${W}x${H}.webm`);

const ff = spawn(FFMPEG, [
  '-y',
  '-f', 'image2pipe', '-c:v', 'mjpeg', '-r', String(FPS), '-i', 'pipe:0',
  '-c:v', 'libvpx',
  '-b:v', '9M', '-crf', '6', '-qmin', '0', '-qmax', '24',
  '-deadline', 'good', '-cpu-used', '1',
  '-auto-alt-ref', '0',
  '-an', '-f', 'webm', out,
], { stdio: ['pipe', 'ignore', 'pipe'] });

let ffErr = '';
ff.stderr.on('data', d => { ffErr += d.toString(); });
const done = new Promise((res, rej) => {
  ff.on('close', code => (code === 0 ? res() : rej(new Error(`ffmpeg exited ${code}\n${ffErr.slice(-2500)}`))));
  ff.on('error', rej);
});

const write = buf => new Promise((res, rej) => {
  ff.stdin.write(buf, err => (err ? rej(err) : res()));
});

console.log(`rendering ${total} frames @ ${FPS}fps  ${W}x${H}`);
const started = Date.now();

for (let i = 0; i < total; i++) {
  await page.evaluate(t => window.__seek(t), i / FPS);
  const buf = await page.screenshot({ type: 'jpeg', quality: 96 });
  await write(buf);
  if (i % 45 === 0 || i === total - 1) {
    const pct = Math.round(((i + 1) / total) * 100);
    process.stdout.write(`  ${String(pct).padStart(3)}%  frame ${i + 1}/${total}\r`);
  }
}

ff.stdin.end();
await done;
await browser.close();

const secs = ((Date.now() - started) / 1000).toFixed(1);
const mb = (fs.statSync(out).size / 1048576).toFixed(2);
console.log(`\ndone in ${secs}s -> ${path.basename(out)} (${mb} MB, ${meta.duration}s)`);
