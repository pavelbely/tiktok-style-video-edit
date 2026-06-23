# TikTok-style video edit

Turn a raw vertical talking-head recording into a polished 9:16 Short: clean-take editing with
punch-in zooms, accumulating on-screen bullets, and STT captions (a plain `.srt` plus a burnt-in
TikTok-style version). This is the exact toolkit used to make the "Is AI making us dumber?" Short —
the scripts ship with that video's settings as a worked example you replace with your own.

> Heads up: this is a **template + method, not a one-click tool**. The cut list (`EDL`) is hand-built
> per take. If you use **Claude Code**, point it at `SKILL.md` and let it drive the whole workflow on
> your footage — that's the intended experience. Otherwise you'll build the EDL by hand (doable, but
> the EDL *is* the work).

## Install

- **ffmpeg** (with libx264): `sudo apt install ffmpeg` / `brew install ffmpeg`
- **Python 3.9+** and: `pip install -r requirements.txt`
- A **bold sans TTF**. On Linux: `sudo apt install fonts-liberation`. macOS/Windows already have Arial
  Bold (the script auto-detects; override `BOLD` in `make_bullets.py` if needed).
- First `make_captions.py` run downloads the faster-whisper `small.en` model (~0.5 GB).

## Use

1. Put your raw take at `raw/take.mp4` and (optional) a 9:16 thumbnail at `raw/thumbnail.png`
   (or set `THUMB = None` in `edit_short.py` to skip the poster-frame flash).
2. **Build the EDL.** Open `edit_short.py` and replace the example `EDL` with cuts for your take.
   The method (transcribe → pick clean takes → find boundaries with `silencedetect` → fill rows) is in
   `SKILL.md`. Quick boundary check on a slice:
   ```bash
   ffmpeg -ss 120 -to 135 -i raw/take.mp4 -ac 1 -ar 16000 /tmp/s.wav
   ffmpeg -i /tmp/s.wav -af silencedetect=n=-30dB:d=0.05 -f null -    # add 120 back to the times
   ```
3. **Bullets** (optional): edit the `NAV` / `AI` lists in `make_bullets.py`, then:
   ```bash
   python3 make_bullets.py        # writes assets/bullets/*.png
   ```
4. **Render the video:**
   ```bash
   python3 edit_short.py          # writes output.mp4
   ```
5. **Captions:**
   ```bash
   python3 make_captions.py       # writes captions.srt + captions.ass (edit its correction map for your words)
   # burn the TikTok captions into a second file:
   ffmpeg -i output.mp4 -vf "ass=captions.ass" -c:v libx264 -crf 18 -pix_fmt yuv420p \
          -c:a copy -movflags +faststart output_captions.mp4
   ```

You now have `output.mp4` (clean) and `output_captions.mp4` (TikTok captions), plus `captions.srt`.

## Tips / gotchas

- **Boundaries: trust `silencedetect`, not whisper word times.** That's how you strip a leading "and",
  a clipped first syllable, a cling/false-start before the first word, or trailing dead air.
- **One clean take beats a stitch.** Stitching two takes mid-phrase leaves a doubled half-word at the seam.
- Phone `.mp4`s often report 1920×1080 but carry a rotation flag → ffmpeg decodes 1080×1920 (no crop).
- ASS captions: the `Format:` line **must** include the `Name` field, or libass renders a stray leading
  comma (already correct in `make_captions.py` — don't remove it).
- `edit_short.py` writes per-clip intermediates to `_clips/`; safe to delete between runs.

## Files

| File | Edit this | What it does |
|------|-----------|--------------|
| `edit_short.py` | `SRC`, `THUMB`, `EDL` | Renders the assembled video |
| `make_bullets.py` | `NAV`, `AI` lists | Accumulating bullet overlays |
| `make_captions.py` | correction map | STT → SRT + TikTok ASS |
| `SKILL.md` | — | Claude Code skill / method reference |
