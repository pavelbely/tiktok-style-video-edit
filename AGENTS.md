# TikTok-style talking-head video edit — agent guide

You are helping turn ONE raw vertical recording (or a few retakes of the same lines) into a polished
9:16 Short: clean-take editing with punch-in zooms, accumulating lower-third bullet overlays, and STT
captions (a plain `.srt` plus a burnt-in TikTok-style version). This file tells you how to drive the
toolkit; `README.md` has the human install/run steps.

## The scripts

- `make_bullets.py` — renders the accumulating bullet overlays (`assets/bullets/*.png`). Edit the
  `NAV` / `AI` lists at the top, run it first. Long lines wrap to 2 lines at a uniform size.
- `edit_short.py` — the editor. Reads the raw take + an **EDL** (the cut list) and renders
  `output.mp4` (1080×1920 / 30fps). The EDL is the heart of the edit.
- `make_captions.py` — STT on `output.mp4` → `captions.srt` + a TikTok-style `captions.ass`; the
  README shows the one-line ffmpeg burn into `output_captions.mp4`.

## The method (this is the actual work)

The EDL is bespoke to each take's exact timings — there is no auto mode. Build it like this:

1. **Transcribe** the raw take with faster-whisper (`small.en`, `word_timestamps=True`) to get a rough
   word map and locate each script line.
2. **Pick the LAST clean take** of every line; skip takes with multi-second hesitation gaps.
3. **Find exact cut boundaries with `silencedetect`, NOT whisper word-timestamps.** Whisper word times
   pad the first word, merge across short gaps, drift ~0.2–0.5s, and silently hide artifacts. On a
   windowed slice:
   ```bash
   ffmpeg -ss 120 -to 135 -i raw/take.mp4 -ac 1 -ar 16000 /tmp/s.wav
   ffmpeg -i /tmp/s.wav -af silencedetect=n=-30dB:d=0.05 -f null -   # add the window offset (120) back
   ```
   This is what removes **word artifacts bleeding in from the take**: a leading "and" before a phrase,
   a clipped onset syllable (start before the word), a cling / lip-smack / false-start burst just
   before the first real word (start the clip *after* it), and trailing dead air after the last word.
4. **Prefer ONE continuous clean take over stitching a phrase** — stitches leave audible seams (a
   doubled half-word). Only stitch at a natural phrase/comma boundary, never mid-word.
5. Fill the `EDL` list in `edit_short.py`: each row is `(in, out, zoom, overlay, overlay_fade, blackfade)`.
   Zoom grammar: a number = static crop-zoom; `("p", z0, z1)` = slow push over the clip;
   `("snap", z0, z1[, ramp])` = fast slam-in; `("snapd", z0, z1, delay, ramp)` = hold then snap
   (land the zoom on an eye-contact moment instead of a glance-down).
6. Run `python3 make_bullets.py`, then `python3 edit_short.py`, then `python3 make_captions.py`.
7. **Verify** by re-transcribing `output.mp4` and diffing against the script (catches clipped/dup words).

## Gotchas

- Phone `.mp4`s often report 1920×1080 but carry a rotation flag → ffmpeg decodes 1080×1920 (no crop).
- ASS captions: the `Format:` line **must** include the `Name` field, or libass renders a stray leading
  comma (already correct in `make_captions.py`).
- `edit_short.py` writes per-clip intermediates to `_clips/`; safe to delete between runs.
