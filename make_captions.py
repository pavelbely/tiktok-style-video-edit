#!/usr/bin/env python3
"""STT the final cut and emit (1) a standard SRT captions file and (2) a TikTok-style ASS
for burn-in (short 1-3 word chunks, big bold white with heavy black outline, centered)."""
import os
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "output.mp4")
SRT = os.path.join(ROOT, "captions.srt")
ASS = os.path.join(ROOT, "captions.ass")

m = WhisperModel("small.en", device="cpu", compute_type="int8")
segs, _ = m.transcribe(SRC, language="en", word_timestamps=True,
                       vad_filter=False, condition_on_previous_text=False)

# flat word list
words = []
for s in segs:
    for w in (s.words or []):
        words.append([w.start, w.end, w.word.strip()])

# light corrections of known STT slips
def replace_seq(words, pat, rep):
    """Replace a run of tokens (matched case-insensitively, ignoring punctuation) with one
    token, preserving the run's time span and the last token's trailing punctuation."""
    patl = pat.lower().split()
    i = 0
    while i <= len(words) - len(patl):
        if [words[i + j][2].lower().strip(".,?!") for j in range(len(patl))] == patl:
            trail = "".join(c for c in words[i + len(patl) - 1][2] if c in ".,?!")
            words[i:i + len(patl)] = [[words[i][0], words[i + len(patl) - 1][1], rep + trail]]
        i += 1


replace_seq(words, "are trophy", "atrophy")     # "...navigation skills atrophy."
replace_seq(words, "a guy", "AI")               # "...before asking AI."
for i, wd in enumerate(words):
    if wd[2].lower().strip(".,?!") == "call" and i and words[i - 1][2].lower().startswith("memory"):
        wd[2] = "recall" + wd[2][4:]      # keep trailing punctuation


def srt_ts(t):
    h, t = divmod(t, 3600); mnt, s = divmod(t, 60)
    return f"{int(h):02d}:{int(mnt):02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}"


def ass_ts(t):
    h, t = divmod(t, 3600); mnt, s = divmod(t, 60)
    return f"{int(h):d}:{int(mnt):02d}:{int(s):02d}.{int(round((s-int(s))*100)):02d}"


# ---- SRT: readable phrase lines (break on sentence punctuation or ~6 words) ----
def srt_lines():
    out, cur = [], []
    for wd in words:
        cur.append(wd)
        ends_sent = wd[2].endswith((".", "?", "!"))
        if ends_sent or len(cur) >= 6:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


with open(SRT, "w") as f:
    for n, line in enumerate(srt_lines(), 1):
        text = " ".join(w[2] for w in line)
        f.write(f"{n}\n{srt_ts(line[0][0])} --> {srt_ts(line[-1][1])}\n{text}\n\n")

# ---- ASS: TikTok chunks (<=3 words, break on sentence end) ----
chunks, cur = [], []
for wd in words:
    cur.append(wd)
    if wd[2].endswith((".", "?", "!")) or len(cur) >= 3:
        chunks.append(cur); cur = []
if cur:
    chunks.append(cur)

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TT, Liberation Sans, 82, &H00FFFFFF, &H000000FF, &H00101010, &H00000000, -1, 0, 0, 0, 100, 100, 0, 0, 1, 6, 2, 5, 80, 80, 0, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

with open(ASS, "w") as f:
    f.write(HEAD)
    for i, ch in enumerate(chunks):
        start = ch[0][0]
        cend = ch[-1][1]
        nxt = chunks[i + 1][0][0] if i + 1 < len(chunks) else cend + 0.4
        end = (nxt - 0.02) if (nxt - cend) < 0.7 else (cend + 0.3)   # hold to next, no overlap
        if end < start + 0.15:
            end = start + 0.15
        text = " ".join(w[2] for w in ch).replace(",", "").upper()  # TikTok punch: no commas, caps
        f.write(f"Dialogue: 0,{ass_ts(start)},{ass_ts(end)},TT,,0,0,0,,{{\\fad(60,40)}}{text}\n")

print("wrote", SRT, "and", ASS, f"({len(chunks)} caption chunks)")
