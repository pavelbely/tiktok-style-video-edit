---
name: tiktok-style-video-edit
description: Edit a vertical 9:16 talking-head Short from a raw take — pick the clean takes, render punch-in zooms, add accumulating bullet overlays, generate STT captions (SRT + burnt TikTok style), and a thumbnail flash. Use when turning a raw phone/webcam recording into a polished TikTok/Reels/YouTube Short.
---

# TikTok-style video edit — talking-head editing pipeline

A small ffmpeg + Python toolkit for cutting a polished vertical Short from ONE raw take (or a few
retakes of the same lines). Built for "talking head + on-screen bullets + captions" explainer Shorts.

## The pieces

- `make_bullets.py` — renders the accumulating lower-third bullet overlays (`assets/bullets/*.png`).
  Edit the `NAV` / `AI` lists, run it first. Long lines wrap to 2 lines at a uniform size.
- `edit_short.py` — the editor. Reads your raw take + an **EDL** (the cut list) and renders the
  assembled video (`output.mp4`, 1080×1920/30fps). This is where the real work is.
- `make_captions.py` — STT on `output.mp4` → `captions.srt` + a TikTok-style `captions.ass`; the
  README shows the one-line ffmpeg burn into `output_captions.mp4`.

## How to drive it (the method that matters)

The EDL is bespoke to each take's exact timings — there is no auto mode. Build it like this:

1. **Transcribe** the raw take with faster-whisper (`small.en`, `word_timestamps=True`) to get a rough
   word map and find each script line.
2. **Pick the LAST clean take** of every line; skip takes with multi-second hesitation gaps.
3. **Find exact cut boundaries with `silencedetect`, NOT whisper timings.** Whisper word times pad,
   merge, drift ~0.2–0.5s, and hide artifacts. On a windowed slice:
   `ffmpeg -i slice.wav -af silencedetect=n=-30dB:d=0.05 -f null -` (add the window offset back).
   This is what removes **word artifacts bleeding in from the take**: a leading "and" before a phrase,
   a clipped onset syllable (start before the word), a cling / lip-smack / false-start burst sitting
   just before the first real word (start the clip *after* it), and trailing dead air after the last word.
4. **Prefer ONE continuous clean take over stitching a phrase** — stitches leave audible seams (a
   doubled half-word). Only stitch at a natural phrase/comma boundary, never mid-word.
5. Fill the `EDL` list: each row is `(in, out, zoom, overlay, overlay_fade, blackfade)`.
   Zoom grammar: a number = static crop-zoom; `("p", z0, z1)` = slow push over the clip;
   `("snap", z0, z1[, ramp])` = fast slam-in; `("snapd", z0, z1, delay, ramp)` = hold then snap
   (use to land the zoom on an eye-contact moment instead of a glance-down).
6. Run `make_bullets.py`, then `edit_short.py`, then `make_captions.py`.
7. **Verify** by re-transcribing `output.mp4` and diffing against the script (catches clipped/dup words).

See `README.md` for install + exact commands.
