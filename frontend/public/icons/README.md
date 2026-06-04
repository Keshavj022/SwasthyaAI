# App Icons

These icons back the PWA manifest (`/public/manifest.json`).

## Files

- `icon.svg` — primary scalable, maskable icon (teal `#0d9488` background, white
  medical cross + heartbeat). Preferred for browsers that support SVG icons.
- `icon-192.png` — 192×192 raster fallback (also used as Apple touch icon).
- `icon-512.png` — 512×512 raster fallback / install splash.

## Note on the PNGs

`icon-192.png` and `icon-512.png` are **generated placeholders** (a flat teal
square with a white cross), produced without external image tooling because the
`sharp`/`canvas` packages were intentionally not added (to keep the build
dependency-free).

For production, replace them with properly designed, brand-accurate raster
icons. The easiest path is to render `icon.svg` at the target sizes, e.g.:

```bash
# requires librsvg / rsvg-convert, or an online SVG->PNG converter
rsvg-convert -w 192 -h 192 icon.svg -o icon-192.png
rsvg-convert -w 512 -h 512 icon.svg -o icon-512.png
```

Keep important content within the central ~80% "safe zone" so the maskable
variants are not clipped on Android adaptive-icon launchers.
