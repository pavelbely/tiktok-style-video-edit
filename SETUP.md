# Setup (works from Belarus / CIS — no US-provider geo-blocks)

Claude, OpenAI, and Google Gemini are not available in Belarus. Use an open-source agent
([OpenCode](https://github.com/sst/opencode)) with a model that is reachable there — a Chinese-provider
API (DeepSeek / GLM / Kimi), or a fully-local model via Ollama.

## 1. System deps

Run the installer (Linux/macOS) — it handles ffmpeg, the font, and the Python packages:
```bash
./install.sh
```
Or install manually: **ffmpeg** (with libx264), **Python 3.9+** (`pip install -r requirements.txt`), and
**a bold sans TTF** (Linux: `sudo apt install fonts-liberation`; macOS/Windows already have Arial Bold).
First `make_captions.py` run downloads the faster-whisper `small.en` model (~0.5 GB).

## 2. Install OpenCode

```bash
curl -fsSL https://opencode.ai/install | bash      # or: npm i -g opencode-ai
```

OpenCode reads `AGENTS.md` in the repo automatically, so it knows how to drive the scripts.

## 3. Pick a model reachable from Belarus

### Option A — DeepSeek (hosted, easiest, cheapest)
Get an API key at platform.deepseek.com, then:
```bash
export DEEPSEEK_API_KEY=sk-...
opencode auth login          # choose DeepSeek, paste the key  (or use the env var)
opencode                     # then: /models  ->  deepseek/deepseek-chat
```

### Option B — other Belarus-reachable hosted models
Same flow via `opencode auth login`, just different provider/key:
- **Zhipu GLM** — `z.ai` / `glm-4.6` (strong coder, cheap subscription)
- **Moonshot Kimi** — `kimi-k2`
- **Alibaba Qwen** — DashScope, `qwen-max` / `qwen2.5-coder`

### Option C — fully local (offline, free, zero geo/payment issues)
Needs a capable GPU or an M-series Mac (32GB+ for the 32B; a 7B/14B works on weaker hardware but is
weaker). Install [Ollama](https://ollama.com), then:
```bash
ollama pull qwen2.5-coder:32b
```
Point OpenCode at the local OpenAI-compatible endpoint (`http://localhost:11434/v1`) via a custom
provider in `opencode.json` — see https://opencode.ai/docs/providers for the current config snippet.

## 4. Run it

```bash
cd tiktok-style-video-edit
opencode
```
Then tell it what you want (e.g. *"build the Short from raw/take.mp4 — transcribe it, build the EDL,
render output.mp4 and the captioned version"*). It will follow `AGENTS.md`. See `README.md` for the
manual command sequence if you'd rather run the scripts yourself.

> Other open-source agents work the same way (Aider, Cline, Continue, goose) — any of them can use
> DeepSeek/GLM/Kimi or a local Ollama model. OpenCode is recommended here for command-driven editing.
