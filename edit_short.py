#!/usr/bin/env python3
"""Assemble a vertical (9:16) talking-head Short from ONE raw take, TikTok-style.
How it works (see README.md):
- Pick the LAST clean take of every script line (skip broken takes with multi-second hesitation gaps).
- Tight pacing: phrases trimmed, inter-take dead air dropped; long lines split into punch-in sub-cuts.
- Alternating zooms + push-ins; SHORT/punch lines get a fast snap-in.
- ON-SCREEN BULLETS: accumulating list overlays (assets/bullets/*.png), newest item highlighted.
- The EDL below is the heart of the edit — it's bespoke to YOUR footage's timings. Build it by
  transcribing your take (faster-whisper) and finding exact word boundaries with `silencedetect`
  (see README). The example EDL here is from the reference build; replace it with yours.

==================  EDIT THESE FOR YOUR OWN VIDEO  ==================
  SRC    -> your raw take (.mp4)
  THUMB  -> a 9:16 thumbnail image (or set to None to skip the poster-frame flash)
  EDL    -> (see the big list below) the cut list for YOUR take
  Bullets-> run make_bullets.py first (edit its NAV/AI lists) to (re)generate assets/bullets/*.png
====================================================================
"""
import os, subprocess, shlex

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "raw", "take.mp4")              # <-- your raw take
THUMB = os.path.join(ROOT, "raw", "thumbnail.png")       # <-- 9:16 thumbnail, or set THUMB = None
THUMB_DUR = 0.05      # 50ms thumbnail flash at the very start (sets the poster frame)
BUL = os.path.join(ROOT, "assets", "bullets")
CLIPDIR = os.path.join(ROOT, "_clips")
OUT = os.path.join(ROOT, "output.mp4")
os.makedirs(CLIPDIR, exist_ok=True)

W, H, FPS = 1080, 1920, 30
VBIAS = 0.18      # crop bias toward top (keep face in upper-center)
SNAP_DUR = 0.16

VENC = ("-c:v libx264 -preset medium -crf 14 -profile:v high -pix_fmt yuv420p "
        "-x264-params keyint=60:min-keyint=60:scenecut=0 -video_track_timescale 30000")
AENC = "-c:a pcm_s16le -ar 44100 -ac 2"   # PCM intermediates -> seamless within-phrase joins


def run(cmd):
    print("$", cmd[:150])
    subprocess.run(shlex.split(cmd), check=True)


def even(v):
    v = int(round(v));  return v - (v & 1)


def static_zoom_vf(z):
    w = even(W / z); h = even(H / z)
    x = even((W - w) / 2); y = even((H - h) * VBIAS)
    return f"crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p"


def push_vf(z0, z1, ramp, delay=0.0):
    tf = max(1, int(round(ramp * FPS)))
    df = int(round(delay * FPS))
    inc = (z1 - z0) / tf
    prog = f"max(0,on-{df})" if df else "on"   # hold z0 for `delay`s, then ramp
    return (f"scale={W*2}:{H*2}:flags=lanczos,"
            f"zoompan=z='min({z0}+{inc:.6f}*{prog},{z1})':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*{VBIAS}':"
            f"s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")


def zoom_vf(zoom, dur):
    if isinstance(zoom, tuple):
        kind = zoom[0]
        if kind == "p":
            return push_vf(zoom[1], zoom[2], dur)
        if kind == "snap":
            ramp = zoom[3] if len(zoom) > 3 else SNAP_DUR
            return push_vf(zoom[1], zoom[2], ramp)
        if kind == "snapd":            # (snapd, z0, z1, delay, ramp) — punch-in fires after `delay`s
            return push_vf(zoom[1], zoom[2], zoom[4], delay=zoom[3])
        raise ValueError(kind)
    return static_zoom_vf(zoom)


def render_th(idx, tin, tout, zoom, overlay=None, ovl_fade=False, blackfade=0.0):
    out = os.path.join(CLIPDIR, f"{idx:02d}.mkv")
    dur = tout - tin
    vf = zoom_vf(zoom, dur)
    if blackfade > 0:
        vf += f",fade=t=in:st=0:d={blackfade}"
    af = "aresample=44100,asetpts=N/SR/TB"
    if overlay:
        ovl = os.path.join(BUL, overlay + ".png")
        of = "format=rgba" + (f",fade=t=in:st=0:d=0.18:alpha=1" if ovl_fade else "")
        fc = f"[0:v]{vf}[base];[1:v]{of}[ovl];[base][ovl]overlay=0:0[v]"
        run(f'ffmpeg -y -ss {tin} -to {tout} -i "{SRC}" -loop 1 -i "{ovl}" '
            f'-filter_complex "{fc}" -map "[v]" -map 0:a -t {dur:.3f} '
            f'-af "{af}" {VENC} {AENC} "{out}"')
    else:
        run(f'ffmpeg -y -ss {tin} -to {tout} -i "{SRC}" -vf "{vf}" '
            f'-af "{af}" {VENC} {AENC} "{out}"')
    return out


# ===================== Edit Decision List =====================
# (tin, tout, zoom, overlay, ovl_fade, blackfade). Source order need not be monotonic;
# each clip carries continuous audio internally, gaps BETWEEN clips are dropped by concat.
EDL = [
    # ---- COLD OPEN / PROBLEM (suspense: slow push + black fade-up, then findings punch in) ----
    # "Multiple studies have shown that people using AI exhibit:"
    (143.21, 146.05, ("p", 1.05, 1.18), None, False, 0.32),
    # the three alarming findings -> escalating cuts
    (146.05, 147.80, 1.16, None, False, 0.0),    # "lower neural activity," (full last syllable)
    (147.82, 148.95, 1.30, None, False, 0.0),    # "reduced memory recall,"
    (149.18, 150.35, ("snap", 1.18, 1.44), None, False, 0.0),  # "less critical thinking."
    # "Is it happening to all of us now?"
    (150.89, 152.42, ("p", 1.10, 1.22), None, False, 0.0),
    # "Are we getting dumber because of AI?"  (punch the hook)
    (152.81, 154.45, ("snap", 1.12, 1.36), None, False, 0.0),

    # ---- GPS EFFECT ----
    # "Some call it the GPS effect." (clean ~2:51 take; -300ms leading dead air; zoom delayed to eye-contact)
    (171.36, 172.98, ("snapd", 1.08, 1.30, 0.48, 0.16), None, False, 0.0),
    (186.30, 188.70, 1.20, None, False, 0.0),                  # "as there are similar studies about navigator apps"
    (188.70, 190.05, 1.36, None, False, 0.0),                  # "like Waze or Google Maps."
    (176.95, 179.00, 1.12, None, False, 0.0),                  # "When we rely on navigators too much,"
    (179.30, 181.15, ("p", 1.16, 1.34), None, False, 0.0),     # "our own navigation skills atrophy."

    # ---- NEUROSCIENTISTS RECOMMEND (intro, slow push) ----
    # last take (224.0) is clean+contiguous: "To avoid that, neuroscientists recommend"
    # "To avoid that, neuroscientists recommend:" — one continuous clean take (3:44), static zoom = no jitter
    (224.10, 226.10, 1.12, None, False, 0.0),

    # ---- NAVIGATOR BULLETS (accumulating overlay) ----
    (244.72, 246.20, 1.12, "nav1", True, 0.0),                 # "Try to build the route yourself"
    (247.02, 248.32, 1.22, "nav2", False, 0.0),                # "Study the route before you drive."
    (249.02, 250.40, 1.16, "nav3", False, 0.0),                # "Use paper maps." (drop leading drawn-out "and")
    (250.64, 251.45, ("snap", 1.10, 1.32), "nav3", False, 0.0),# "Remember those?" (full "Re-")

    # ---- AI SECTION (intro) ----
    (323.67, 324.95, ("snap", 1.10, 1.32), None, False, 0.0),  # "But what about AI?"
    (325.53, 326.35, 1.16, None, False, 0.0),                  # "In a similar manner,"

    # ---- AI BULLETS (accumulating overlay, fresh list) ----
    # "Think how you will solve the problem yourself before asking AI" — ONE clean continuous
    # take, uncut (no duplicated "you"); starts after the cling/false-start; static zoom = no artifacts
    (340.05, 343.45, 1.12, "ai1", True, 0.0),
    (360.88, 362.32, 1.18, "ai2", False, 0.0),                 # "Make the first draft yourself."
    (362.54, 365.75, 1.12, "ai2", False, 0.0),                 # "A blog post draft, an email draft, or a Slack message draft"
    (365.75, 367.85, ("p", 1.18, 1.34), "ai2", False, 0.0),    # "in your authentic way." (trim trailing pause)
    # closing: accurate no-VAD boundaries (speaker left long pauses; cut them, keep word onsets intact)
    # Closing line from the clean, complete 6:21-6:28 take (phrase-level cuts, natural pauses trimmed)
    (381.82, 383.10, 1.14, "ai3", False, 0.0),                 # "Read books,"
    (383.55, 384.58, 1.20, "ai3", False, 0.0),                 # "protect your focus,"
    (385.05, 386.15, 1.16, "ai3", False, 0.0),                 # "increase your attention span,"

    # ---- OUTRO ----
    (386.55, 387.55, ("p", 1.10, 1.26), None, False, 0.0),     # "Drive safely."
]

def render_thumb():
    out = os.path.join(CLIPDIR, "thumb.mkv")
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"setsar=1,fps={FPS},format=yuv420p")
    run(f'ffmpeg -y -loop 1 -i "{THUMB}" -f lavfi -i anullsrc=r=44100:cl=stereo '
        f'-t {THUMB_DUR} -vf "{vf}" {VENC} {AENC} -shortest "{out}"')
    return out


clips = [render_thumb()] if THUMB else []      # 50ms poster-frame flash, optional
for i, (tin, tout, zoom, ovl, fade, bf) in enumerate(EDL):
    clips.append(render_th(i, tin, tout, zoom, ovl, fade, bf))

listfile = os.path.join(CLIPDIR, "concat.txt")
with open(listfile, "w") as f:
    for c in clips:
        f.write(f"file '{c}'\n")
run(f'ffmpeg -y -f concat -safe 0 -i "{listfile}" -c:v copy -c:a aac -b:a 192k '
    f'-movflags +faststart "{OUT}"')
print("\nDONE ->", OUT, f"({len(clips)} clips)")
