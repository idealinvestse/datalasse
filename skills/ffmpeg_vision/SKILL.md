---
name: ffmpeg-vision
description: Adaptiv frame-extraktion från video + kostnadseffektiv vision-LLM-beskrivning. Använd ffmpeg för att klippa ut högupplösta frames baserat på ett transkript (5-30s intervall, tätare vid höjdpunkter/keyword), och beskriv dem med en billig vision-LLM (Llama 4 Scout som default) eller en dyr vid behov (Claude Sonnet / GPT-4o).
---

# ffmpeg-vision

Adaptiv frame-extraktion från video + kostnadseffektiv vision-LLM-beskrivning.

## Vad den gör

1. **Läser video-metadata** med `ffprobe` (duration, upplösning, codec, fps)
2. **Extraherar frames** med `ffmpeg` (hög upplösning, originalstorlek eller skalad)
3. **Adaptiv sampling** baserat på ett transkript:
   - Regular frames var 30s (default, justerbart)
   - Extra frames vid höjdpunkter (±5s)
   - Extra frames när keywords dyker upp (t.ex. "kill", "bucket", "goodnight")
   - Minsta gap 5s (justerbart)
   - Max 50 frames totalt (justerbart, budget-styrd)
4. **Vision-beskrivning** av frames:
   - Default: **Llama 4 Scout 17B** via Groq (~$0.017/100 frames)
   - Billig: GPT-4o mini via OpenRouter (~$0.029/100 frames)
   - Dyr: Claude Sonnet 4.5 / GPT-4o för svåra scener

## Användning

### Smoke test: video info

```bash
bin/ffmpeg-vision info episode.mp4
```

### Extrahera frames (jämnt intervall)

```bash
bin/ffmpeg-vision extract episode.mp4 --interval 30 --output ./frames
```

### Adaptiv sampling med transcript

```bash
bin/ffmpeg-vision adaptive episode.mp4 \
  --transcript data/kill-tony/transcripts/ep-774.transcript.json \
  --analysis data/kill-tony/ep-774-summary.md \
  --output data/kill-tony/frames-ep-774 \
  --max-frames 30
```

### Beskriv frames med vision-LLM

```bash
bin/ffmpeg-vision describe data/kill-tony/frames-ep-774 \
  --model llama-4-scout-groq \
  --output data/kill-tony/ep-774-descriptions.json \
  --max-frames 30 \
  --budget 0.05
```

### Lista modeller + kostnader

```bash
bin/ffmpeg-vision models
bin/ffmpeg-vision cost 100 --model claude-sonnet-vision
```

## Modeller

| Nyckel | Modell | Provider | ~$ / 100 frames |
|---|---|---|---|
| `llama-4-scout-groq` | Llama 4 Scout 17B | Groq | $0.017 |
| `gpt-4o-mini` | GPT-4o mini | OpenRouter | $0.029 |
| `llama-3.2-90b-vision` | Llama 3.2 90B Vision | OpenRouter | $0.117 |
| `gpt-4o` | GPT-4o | OpenRouter | $0.476 |
| `claude-sonnet-vision` | Claude Sonnet 4.5 | OpenRouter | $0.491 |

**Rekommenderad routing:**
- Default: `llama-4-scout-groq` (snabbast + billigast)
- Om Llama 4 Scout missar detaljer: `gpt-4o-mini` (~70% dyrare men bättre på text-i-bild)
- Viktiga scener (t.ex. höjdpunkter i highlights-manifest): `claude-sonnet-vision` (29x dyrare men bäst)

## Adaptiv sampling-logik

1. **Regular frames**: var `base_interval` sekunder (default 30s)
2. **Highlight-frames**: varje höjdlpunkt i analysen ger 3 extra frames (vid ±5s)
3. **Keyword-frames**: om keyword i transcript-segment → frame vid segment-start
4. **Dedup**: prioritera högsta priority vid samma timestamp (±0.5s)
5. **Min interval**: ga till 0 frames om för tätt (<5s default)
6. **Max frames**: behåll högst prioriterade (default 50)

**Prioritetsvikter (justerbara i `AdaptiveSampler`):**
- `weight_highlight = 3.0` (3x vikt vid höjdpunkter)
- `weight_keyword = 1.5` (1.5x vid keyword)
- `weight_regular = 1.0` (default)
- `weight_silence = 0.3` (låg vid tysta partier, framtida feature)

## Output-format

### Manifest (per frame)

```json
{
  "timestamp": 123.5,
  "path": "frames/frame-0042-t123.5s.jpg",
  "reason": "highlight:joke:Mason Bird joke"
}
```

### Descriptions

```json
{
  "frames_dir": "frames/",
  "model": "llama-4-scout-groq",
  "count": 30,
  "estimated_cost_usd": 0.0051,
  "descriptions": [
    {
      "frame_path": "frames/frame-0001-t0.0s.jpg",
      "timestamp": 0.0,
      "description": "Tony står på scen med mikrofonen, publiken skrattar",
      "model": "llama-4-scout-groq",
      "cost_usd": 0.00017
    }
  ]
}
```

## Begränsningar / TODOs

- **Video-nedladdning**: SkILLen tar video-FIL som input. YouTube-blockerar VPS-IP, så ladda ner från tillåten källa först (RSS, archive.org, egen fil). För att ladda ner YouTube: använd `--cookies-from-browser` eller Cloudflare WARP.
- **Speaker diarization**: Whisper ger inga talar-ID:n. För att separera Tony/Redban/gäst behövs `pyannote-audio` eller liknande (M5 feature).
- **Batch-beskrivning**: `images_per_call=1` är default. Kan ökas för kostnadsbesparing (1 API-call = N bilder), men output är svårare att parsa.
- **Cache**: ingen caching av descriptions — samma frame beskrivs igen om du kör describe två gånger. TODO: hash-baserad cache.

## Tester

```bash
python3 skills/ffmpeg_vision/tests/test_ffmpeg_vision.py
```

8/8 tester PASS, ingen nätverksaccess krävs (testar med syntetisk ffmpeg-video + fejk-transcript).

## Designbeslut

- **Modell-registret är hårdkodat** i `vision.py` (5 modeller). Lägg till fler genom att utöka `MODELS`-dict.
- **Adaptiv sampling är deterministisk** — samma transcript + analys ger samma timestamps varje gång. Bra för caching + testbarhet.
- **Bilder sparas som JPG** (default) — bra balans mellan kvalitet och storlek. PNG för skarpa detaljer, WebP för komprimering.
- **Cost-log per batch** — `VisionDescriber.cost_log` ger full spårbarhet per anrop.

## Exempel: Kill Tony pipeline (M5)

```bash
# 1. Ladda ner video (utanför skILLen, t.ex. via archive.org)
yt-dlp --format mp4 "https://www.youtube.com/watch?v=..." -o kt-774.mp4

# 2. Adaptiv sampling
bin/ffmpeg-vision adaptive kt-774.mp4 \
  --transcript data/kill-tony/transcripts/ep-774.transcript.json \
  --analysis data/kill-tony/ep-774-summary.md \
  --output data/kill-tony/frames-ep-774

# 3. Beskriv med billig modell
bin/ffmpeg-vision describe data/kill-tony/frames-ep-774 \
  --model llama-4-scout-groq \
  --output data/kill-tony/ep-774-vision.json

# 4. (Valfritt) Beskriv höjdpunkter med dyr modell
jq '.descriptions[] | select(.reason | startswith("highlight"))' \
  data/kill-tony/frames-ep-774/manifest.json | \
  xargs -I {} bin/ffmpeg-vision describe {} --model claude-sonnet-vision
```
