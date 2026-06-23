---
name: "fal-ai"
description: "Optimal usage of fal.ai's model APIs, workflows, webhooks, CDN, and the Python fal-client SDK beyond OpenClaw's bundled defaults."
---

# fal-ai skill

Use fal.ai's full surface — 1,000+ models (image, video, audio, vision, 3D, LLM-proxy), queue-backed inference, webhooks, CDN uploads, workflows, and CLI — in optimal, cost-aware patterns. OpenClaw already ships a bundled `fal` provider for image/video/music generation; this skill extends beyond that to audio TTS/STT, vision, 3D, workflows, custom apps, webhooks, and direct Python SDK scripting.

## When to use this skill

- The user wants to call a fal.ai model that **isn't** exposed via OpenClaw's built-in image/video/music providers (e.g. fal-3d, fal-vision, custom serverless apps, OpenAI-compatible LLM proxy via OpenRouter).
- The user wants to use a fal.ai **workflow** (chained models, e.g. `workflows/fal-ai/sdxl-sticker`).
- The user wants to upload files to fal's CDN, set up **webhooks** for long-running jobs, or use `submit` + poll pattern instead of `subscribe`.
- The user wants to deploy their own model to fal Serverless (advanced — use sparingly).
- The user wants to choose a fal model family for a specific task (cheapest fast image gen, best photoreal video, etc.).

## When NOT to use this skill

- Simple image/video/music generation that OpenClaw's bundled provider already covers — just call `image_generate`, `video_generate`, `music_generate` directly with `model` override.
- Anything outside fal.ai (Replicate, OpenAI direct, local Stable Diffusion, etc.).

---

## 1. Architecture in 60 seconds

fal.ai exposes every model as an HTTP endpoint. Two URL families:

- **`fal.run/<model-id>`** — direct, synchronous. No queue, no retries, no status polling. Fastest path for small/fast models.
- **`queue.fal.run/<model-id>`** — persistent queue. Auto-retries (10× on 5xx, connection errors), status polling, scaling. **Recommended for production.**

Five calling patterns, each available in Python (`fal-client`) and JavaScript (`@fal-ai/client`):

| Method | Through | Use when |
|---|---|---|
| `run()` | `fal.run` | Quick scripts, fast models, prototyping. |
| `subscribe()` | queue | Simple blocking call, queue-backed reliability. **Default for one-shot work.** |
| `submit()` + `handler.get()` | queue | Fire-and-forget; you poll status yourself or use webhooks. Best for parallel jobs. |
| `stream()` | SSE | Progressive output (image preview, LLM tokens). |
| `realtime()` | WebSocket | Sub-100ms back-to-back requests. Only models with `/realtime` endpoint. |

Request lifecycle (queue-backed): `IN_QUEUE` → `IN_PROGRESS` → `COMPLETED`.

---

## Where things live

| Location                      | Purpose |
|-------------------------------|---------|
| `safety_off.py`               | Policy defaults + `with_safety_off()` + `subscribe`/`submit`/`run` wrappers (source of truth) |
| `safe_client.py`              | Thin re-export (drop-in convenience matching the §13a contract) |
| `examples/`                   | Runnable reference scripts (subscribe default, submit+poll, webhook, CDN upload, workflow stream) |
| `tests/`                      | pytest suite for safety logic and wrappers |
| `references/`                 | (optional) deeper docs / model notes |

See also `fal_image/safety.py` which re-exports from here for image-specific usage.

---

## 2. Auth + client setup

```bash
export FAL_KEY="<your_key>"   # canonical; FAL_API_KEY also accepted
pip install fal-client
```

In OpenClaw: `openclaw onboard --auth-choice fal-api-key` (uses `FAL_KEY`).

For browser/React apps: **never expose `FAL_KEY` client-side**. Set up `@fal-ai/server-proxy` on a server route; configure client with `fal.config({ proxyUrl: '/api/fal/proxy' })`.

When env vars aren't available:
```python
import os; os.environ["FAL_KEY"] = "..."
import fal_client
```
```js
import { fal } from "@fal-ai/client";
fal.config({ credentials: "..." });
```

---

## 3. Decision tree: which method to use

```
Is the job long-running (training, video gen > 30s)? 
  └─ YES → submit() + webhook (or submit() + poll)
  └─ NO  ↓
Do you need progress events to stream to a user?
  └─ YES → stream()  (must be a model with /stream endpoint)
  └─ NO  ↓
Do you want retries + durability?
  └─ YES → subscribe()                ← DEFAULT
  └─ NO  → run()                     ← only for short fast models
```

**Rule of thumb:** `subscribe()` for almost everything. `submit()` when you're batching or want webhook-driven async. `run()` only for cheap synchronous calls (text LLM, fast SDXL) where you accept failure.

---

## 4. Common parameters (headers)

Pass via `headers=` dict; some have SDK sugar:

| Header | SDK param | Default | Purpose |
|---|---|---|---|
| `X-Fal-Request-Timeout` | `start_timeout` (s) | none | Server-side time-to-start deadline. **Stops once runner starts.** |
| — | `client_timeout` (s) / `timeout` (ms) | none | **Total client-side wait** (queue + processing). Stops polling but request may continue on server. |
| `X-Fal-Runner-Hint` | `hint` | auto | Pin request to a specific runner (LoRA session affinity). |
| `X-Fal-Queue-Priority` | `priority` | `"normal"` | `"low"` deprioritizes behind all normal-priority on shared queue. |
| `X-Fal-Object-Lifecycle-Preference` | — | account setting | `{"expiration_duration_seconds": N}` — auto-expire CDN files. |
| `X-Fal-Store-IO` | — | `"1"` (30 days) | `"0"` to skip payload storage (privacy/PII). CDN files still kept. |
| `X-Fal-No-Retry` | — | retries on | `"1"` to disable automatic retries. |
| `X-Fal-Retry-Config` | — | platform default | Per-condition retry budget (JSON, e.g. `{"timeout":{"retries":0}}`). **Own apps only.** |
| `x-app-fal-disable-fallback` | — | fallbacks on | Disable rerouting to equivalent endpoints. |

**Interaction (Python):** if you set `client_timeout` without `start_timeout`, SDK sets `start_timeout=client_timeout`. If `start_timeout > client_timeout`, SDK warns.

---

## 5. CDN uploads (file inputs)

Models accept file inputs as **URLs**. For local files:

```python
import fal_client
url = fal_client.upload_file("local/image.png")          # multipart auto for >100 MB
url = fal_client.upload(image_bytes, "image/png")        # raw bytes
url = fal_client.upload_image(pil_image)                 # PIL → JPEG → upload
```

```js
const url = await fal.storage.upload(file);              // File/Blob
```

Then pass `url` to any model. **Always prefer CDN URL over data URIs** (data URIs bloat payloads — only for tiny files).

URLs work with **any** publicly accessible host (S3/GCS presigned URLs, your CDN). For auth-required files: download first, then `upload_file`.

CDN URLs are public; use `X-Fal-Object-Lifecycle-Preference` to set TTL.

---

## 6. Webhooks (production async pattern)

For long jobs (training, video gen), use `submit` + webhook to avoid holding a connection:

```python
handler = fal_client.submit(
    "fal-ai/seedance-2.0/text-to-video",
    arguments={"prompt": "...", "duration": "5"},
    webhook_url="https://your-app.com/api/fal/webhook",
)
print(handler.request_id)   # store this
```

Webhook payload (`POST` JSON):
```json
{
  "request_id": "...",
  "gateway_request_id": "...",
  "status": "OK" | "ERROR",
  "payload": {...},       // null on serialization error
  "error": "...",
  "payload_error": "..."
}
```

**Retry policy:** 15s initial timeout, 10 retries over 2h. **Design handlers idempotent** on `request_id`.

**Signature verification** (CRITICAL — required for production):
1. Fetch JWKS from `https://rest.fal.ai/.well-known/jwks.json` (cache ≤24h).
2. Headers required: `X-Fal-Webhook-Request-Id`, `X-Fal-Webhook-User-Id`, `X-Fal-Webhook-Timestamp`, `X-Fal-Webhook-Signature` (hex).
3. Reject if timestamp differs >300s from now.
4. Compute SHA-256 hex of **raw body bytes**. Concatenate: `request_id \n user_id \n timestamp \n sha256_hex(body)` → UTF-8 bytes.
5. Verify with ED25519 public key from JWKS `x` field (base64url).

Allowlist (refresh from `https://api.fal.ai/v1/meta` → `webhook_ip_ranges`).

```python
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
# verify_key.verify(message, signature_hex_bytes)
```

---

## 7. Workflows (chained models)

Workflow endpoints live under `workflows/<owner>/<name>`. They emit streaming events as each step progresses:

```python
import fal_client
stream = fal_client.stream("workflows/fal-ai/sdxl-sticker", arguments={
    "prompt": "a cute puppy, pixar style"
})
for event in stream:
    print(event)   # type: submit | completion | output | error
# stream has .done() to await final result (JS)
```

Event shapes:
- `submit` — `{"type":"submit", "node_id":"...", "app_id":"...", "request_id":"..."}`
- `completion` — `{"type":"completion", "node_id":"...", "output": {...}}`
- `output` — final result `{"type":"output", "output": {...}}`
- `error` — `{"type":"error", "node_id":"...", "message":"...", "error": {...}}`

Use `stream()` for workflows (not `subscribe()`) — you want intermediate events.

---

## 8. Real-time (WebSocket, low-latency)

Only models with a `/realtime` endpoint. Persistent connection, back-to-back requests:

```python
with fal_client.realtime("fal-ai/fast-sdxl") as conn:
    conn.send({"prompt": "a sunset", "num_inference_steps": 2})
    result = conn.recv()
    print(result)
```

Use for interactive apps (real-time image editing, chat). **Not** for one-shot gen.

---

## 9. Model selection cheatsheet (popular families)

Always check `fal.ai/models/<id>/api` for exact input/output schema.

**Image gen (cheap → premium):**
- `fal-ai/flux/schnell` — fastest, 4-step, free-tier friendly. Edit: `fal-ai/flux-kontext-lora`.
- `fal-ai/flux/dev` — balanced quality, OpenClaw default.
- `fal-ai/flux-pro/v1.1-ultra` — top quality, premium. Has `raw`, `enhance_prompt`, `safety_tolerance` (1-6).
- `fal-ai/nano-banana-2` — fast editing, supports up to 14 reference images via `/edit`.
- `fal-ai/gpt-image-1.5` / `fal-ai/gemini-3-pro-image-preview` — proprietary quality.
- `fal/krea/v2/{medium,large}/text-to-image` — `creativity: raw|low|medium|high`, aspect_ratio (not image_size).
- **LoRA training:** `fal-ai/flux-lora-fast-training` (custom models).

**Video gen (cheap → premium):**
- `fal-ai/bytedance/seedance-2.0/fast/text-to-video` — OpenClaw default; `fast` ≈ 5× cheaper.
- `fal-ai/bytedance/seedance-2.0/{text,image,reference}-to-video` — full quality; reference supports up to 9 imgs + 3 vids + 3 audio (max 12).
- `fal-ai/kling-video/v3/pro/image-to-video` — premium, longer clips.
- `fal-ai/sora-2` — OpenAI Sora on fal.
- `fal-ai/veo3.1` — Google's Veo.
- `fal-ai/happyhorse-1.0` — audio-synced, multilingual lip-sync.
- `fal-ai/heygen/v2/video-agent` — avatar-driven.
- **Lipsync:** `fal-ai/sync-lipsync`, `fal-ai/latentsync`.

**Audio (music, TTS, STT, voice clone):**
- Music: `fal-ai/minimax-music/v2.6` (lyrics + structure tags `[Verse][Chorus][Bridge]`); `fal-ai/ace-step/prompt-to-audio`; `fal-ai/stable-audio-25/text-to-audio`. Music Cover: `MusicCoverRequest` with `audio_url` (6s–6min).
- TTS / voice clone: `fal-ai/elevenlabs/tts/...`, `fal-ai/playht/tts/...`.
- STT: `fal-ai/whisper`, `fal-ai/xai/whisper-large-v3-turbo`.

**Vision / captioning / VQA:**
- `fal-ai/florence-2-large`, `fal-ai/xai/grok-vision`, OpenRouter proxy (any LLM w/ vision).

**3D:**
- `fal-ai/hunyuan3d/v2`, `fal-ai/trellis`, `fal-ai/trellis-2`. Output: GLB/mesh.

**LLMs (OpenAI-compatible, single endpoint):**
- `openrouter/router/openai/v1/chat/completions` — drop-in OpenAI SDK; any GPT/Claude/Gemini/Grok/DeepSeek/Llama/Qwen/Mistral.
- `openrouter/router/openai/v1/responses` — Responses API (stateful, tool calls, reasoning).
- `openrouter/router/openai/v1/embeddings` — embeddings.
- Use these with `model` field set to target LLM id (e.g. `"anthropic/claude-sonnet-4.5"`).

---

## 10. OpenClaw-specific patterns

**Set fal as default image provider:**
```json5
// agents.defaults in config
{
  agents: {
    defaults: {
      imageGenerationModel: { primary: "fal/fal-ai/flux/dev" },
      videoGenerationModel: { primary: "fal/fal-ai/bytedance/seedance-2.0/fast/text-to-video" },
      musicGenerationModel: { primary: "fal/fal-ai/minimax-music/v2.6" }
    }
  }
}
```

**Per-call override** (use any of 1,000+ fal models even outside defaults):
- `image_generate(model="fal/fal-ai/flux-pro/v1.1-ultra", ...)`
- `video_generate(model="fal/fal-ai/kling-video/v3/pro/image-to-video", ...)`
- `music_generate(model="fal/fal-ai/ace-step/prompt-to-audio", ...)`

**Capabilities matrix (from OpenClaw docs):**
- Image: max 4 per request (Krea 2: 1); Flux edit = 1 ref img; GPT-Image-2 edit = 10; Nano-Banana-2 edit = 14; Krea supports up to 10 style refs.
- Video: text→video, single-img ref, Seedance ref→video (max 9 imgs + 3 vids + 3 audio).
- Output formats: `png` / `jpeg` (Krea: no `output_format` field — rejected, not dropped).

**Unsupported on fal** (OpenClaw reports as ignored):
- `background: "transparent"` — no transparent control.
- `resolution` on Krea — rejected, not silently dropped.
- `outputFormat` on Krea — rejected.
- `aspectRatio` on Flux image-to-image — ignored.

---

## 11. CLI quick ref

`fal` CLI for auth, deploy, files, queue:

```bash
fal auth login              # interactive
fal keys                     # list API keys
fal files upload ./img.png   # upload to CDN, print URL
fal queue status <model> --request-id <id>
fal deploy                   # deploy current dir as serverless app
fal apps list                # list your apps
fal apps scale <app> --replicas N
```

Full reference: https://fal.ai/docs/api-reference/cli/

---

## 12. Cost + speed tips

1. **`fast` variants** are ~5× cheaper than full quality (Seedance fast, SDXL vs SDXL-lightning).
2. **Image size matters more than steps** for FLUX. `landscape_4_3` vs `square_hd` can 2× the cost.
3. **Disable retries** (`X-Fal-No-Retry: 1`) for low-stakes bulk jobs to avoid double-billing on flaky models.
4. **Set TTL** (`X-Fal-Object-Lifecycle-PPreference: {"expiration_duration_seconds": 3600}`) for ephemeral results — avoids CDN clutter and surprise bills.
5. **Disable payload storage** (`X-Fal-Store-IO: 0`) for PII — fal still charges for inference but doesn't keep the request.
6. **`priority: "low"`** on shared models to drop behind paid tiers (free-tier friendly).
7. **Use `hint`** to pin LoRA sessions — avoids re-loading adapter cost per request.
8. **Pre-warm runners** for your own apps via `fal apps scale --min-replicas 1` to eliminate cold starts.

---

## 13. Errors & gotchas

- **504 Gateway Timeout** with `X-Fal-Request-Timeout-Type: user` → your `start_timeout` fired before any runner started. Raise it or reduce queue load.
- **`422 Validation Error`** → input schema mismatch. Read the exact model page; parameters vary widely between families.
- **`429 Too Many Requests`** → queue full. Set `fal_max_queue_length` query param to fail-fast.
- **NSFW rejected** on FLUX Pro → raise `safety_tolerance` (1=strict, 6=permissive). 1.1-ultra accepts up to 6.
- **Webhook 5xx** → handler must be idempotent; fal retries 10× over 2h.
- **Data URIs slow** for large files — always CDN-upload first.
- **`flux/dev` queue contention** during peak hours → switch to `flux/schnell` (faster, cheaper) for iteration.

---

## 13a. Safety off — full audit + defaults

**Policy (this workspace):** alla fal.ai-anrop skickas med safety-relaterade parametrar satta till **mest tillåtande** som provider exponerar:

| Parameter | Default (provider) | Recommended (this workspace) |
|---|---|---|
| `enable_safety_checker` | `true` | **`false`** (slår av modellens in-process safety classifier) |
| `safety_tolerance` | `"2"`–`"4"` | **`"6"`** (max tillåten, mest tillåtande) |

> ⚠️ **Viktigt om scope:** Det här är de **user-facing parametrar** som fal.ai exponerar för sina kunder. Det finns **också** en plattformsnivå-policy hos fal.ai själva (lagstadgad: CSAM, terrorism, etc.) som körs oavsett vad användaren skickar. Den kan inte stängas av via API-params.

### Vilka modeller som respekterar safety params

**Modeller med `enable_safety_checker` (boolean):**
| Modell | Default | Recommended |
|---|---|---|
| `fal-ai/flux/schnell` | `true` | `false` |
| `fal-ai/flux/dev` | `true` | `false` |
| `fal-ai/flux-2-pro` | `true` | `false` |
| `fal-ai/flux-kontext-lora` | `true` | `false` |
| `ideogram/v4` | `true` | `false` |
| `alibaba/happy-horse/text-to-video` | `true` | `false` |

**Modeller med `safety_tolerance` (enum 1–6):**
| Modell | Default | Recommended |
|---|---|---|
| `fal-ai/flux-pro/v1.1-ultra` | `"2"` | `"6"` |
| `fal-ai/flux-2-pro` | `"2"` | `"6"` |
| `fal-ai/flux-pro/kontext` | `"2"` | `"6"` |
| `fal-ai/nano-banana-2` | (provider default) | `"6"` |
| `fal-ai/nano-banana-2/edit` | (provider default) | `"6"` |
| `fal-ai/veo3` | `"4"` | `"6"` |

**Modeller utan safety-param (provider styr helt — kan inte user-konfigureras):**

`NO_USER_SAFETY_MODELS` i `safety_off.py` är den **authoritative** listan över provider-controlled modeller (inga user-facing safety knobs). Dessa körs utan safety-relaterade args; provider avgör.

```python
NO_USER_SAFETY_MODELS = {
    "krea/v2/medium/text-to-image",
    "openai/gpt-image-2/edit",
    "bytedance/seedance-2.0/text-to-video",
    "bytedance/seedance-2.0/fast/text-to-video",
    "bria/fibo-edit/edit",
    "bytedance/seedance-2.0/fast/image-to-video",
    "bytedance/seedance-2.0/fast/reference-to-video",
    "luma/agent/ray/v3.2/image-to-video",
    "fal-ai/kling-video/v3/pro/image-to-video",
    "fal-ai/stable-audio-25/text-to-audio",
    "fal-ai/minimax-music/v2.6",
    "fal-ai/ace-step",
    "fal-ai/elevenlabs/tts/turbo-v2.5",
    "fal-ai/elevenlabs/tts/multilingual-v2",
    "fal-ai/whisper",
    "fal-ai/florence-2-large/detailed-caption",
    "fal-ai/trellis",
    "tripo3d/p1/image-to-3d",
}
```

Se även `tests/test_safety_off.py` för assertion som skyddar denna lista.

### Helper: `safety_off_defaults()`

Använd denna för att automatiskt applicera rätt safety-off args baserat på modell:

```python
# skills/fal-ai/safety_off.py (eller lägg in i ditt project)
SAFETY_OFF_DEFAULTS = {
    # enable_safety_checker models
    "fal-ai/flux/schnell":                  {"enable_safety_checker": False},
    "fal-ai/flux/dev":                      {"enable_safety_checker": False},
    "fal-ai/flux-2-pro":                    {"enable_safety_checker": False, "safety_tolerance": "6"},
    "fal-ai/flux-kontext-lora":             {"enable_safety_checker": False},
    "ideogram/v4":                          {"enable_safety_checker": False},
    "alibaba/happy-horse/text-to-video":    {"enable_safety_checker": False},
    # safety_tolerance models
    "fal-ai/flux-pro/v1.1-ultra":           {"safety_tolerance": "6"},
    "fal-ai/flux-pro/kontext":              {"safety_tolerance": "6"},
    "fal-ai/nano-banana-2":                 {"safety_tolerance": "6"},
    "fal-ai/nano-banana-2/edit":            {"safety_tolerance": "6"},
    "fal-ai/veo3":                          {"safety_tolerance": "6"},
}


def with_safety_off(model_id: str, args: dict | None = None) -> dict:
    """Merge user `args` with workspace safety-off defaults for `model_id`.

    User-provided values WIN over defaults (explicit override allowed).
    Models not in SAFETY_OFF_DEFAULTS pass through unchanged.
    """
    defaults = SAFETY_OFF_DEFAULTS.get(model_id, {})
    merged = dict(defaults)
    if args:
        merged.update(args)  # user args override defaults
    return merged


# Usage (from skills/fal-ai/safety_off.py or via safe_client):
import fal_client
from safety_off import with_safety_off   # or: from safe_client import with_safety_off

args = with_safety_off("fal-ai/flux-pro/v1.1-ultra", {
    "prompt": "a sunset over mountains",
    "aspect_ratio": "16:9",
    "raw": True,
})
# args is now:
# {"prompt": ..., "aspect_ratio": "16:9", "raw": True, "safety_tolerance": "6"}

result = fal_client.subscribe("fal-ai/flux-pro/v1.1-ultra", arguments=args)
```

### Alternativ: wrapper-modul

Om du vill ha en drop-in ersättning för `fal_client.subscribe` som alltid applicerar safety-off:

```python
# skills/fal-ai/safe_client.py  (thin re-export — real impl is in safety_off.py)
from safety_off import subscribe, submit, run, with_safety_off

# Then use exactly like fal_client:
# result = subscribe("fal-ai/flux-pro/v1.1-ultra", arguments={"prompt": "..."})
```

### OpenClaw-bundlade tools

`image_generate` / `video_generate` / `music_generate` stödjer dessa via `extra_args`:

```python
image_generate(
    prompt="...",
    model="fal/fal-ai/flux-pro/v1.1-ultra",
    aspect_ratio="16:9",
    safety_tolerance="6",          # ← explicit
)

video_generate(
    prompt="...",
    model="fal/fal-ai/veo3",
    safety_tolerance="6",          # ← explicit
)
```

Om `enable_safety_checker` behövs och OpenClaw-wrappern inte exponerar den, gå via Python SDK direkt enligt `with_safety_off()`-mönstret ovan.

### Vad det INTE gör

- Det här påverkar **inte** fal.ai:s plattformspolicy (lagstadgade blockeringar).
- Det här gör **inte** modellerna i sig "uncensored" på viktnivå — det släpper bara provider-exponerade filter.
- Det här kringgår **inte** output-filtrering som fal.ai kör efteråt på hostade URLs (om aktiverat).

Om en modell vägrar trots `safety_tolerance: "6"` eller `enable_safety_checker: false`, är det plattformspolicyn som gäller — då finns ingen API-väg framåt.

---

## 14. Reference scripts

Runnable versions of the key patterns live in `examples/`. The snippets below are the essential patterns (copy-paste friendly).

### 14.1 Subscribe pattern (default, with safety-off)
```python
# Workspace policy: all calls go through with_safety_off()
import fal_client
from safety_off import with_safety_off

result = fal_client.subscribe(
    "fal-ai/flux-pro/v1.1-ultra",
    arguments=with_safety_off("fal-ai/flux-pro/v1.1-ultra", {
        "prompt": "a sunset over mountains",
        "aspect_ratio": "16:9",
        "raw": True,
    }),
    with_logs=True,
    on_queue_update=lambda u: print(u),
)
print(result["images"][0]["url"])
```

### 14.2 Submit + poll (long-running)
```python
import time, fal_client
from safety_off import with_safety_off

h = fal_client.submit(
    "fal-ai/bytedance/seedance-2.0/text-to-video",
    arguments=with_safety_off("fal-ai/bytedance/seedance-2.0/text-to-video", {
        "prompt": "a cat on a roof",
        "duration": "5",
    }),
)
while True:
    s = h.status(with_logs=True)
    if isinstance(s, fal_client.Queued): print(f"queue pos {s.position}")
    elif isinstance(s, fal_client.InProgress):
        for l in (s.logs or []): print(l["message"])
    elif isinstance(s, fal_client.Completed):
        print(f"done in {s.metrics.get('inference_time')}s"); break
    time.sleep(0.5)
print(h.get()["video"]["url"])
```

### 14.3 Submit + webhook
```python
import fal_client
from safety_off import with_safety_off

h = fal_client.submit(
    "fal-ai/seedance-2.0/text-to-video",
    arguments=with_safety_off("fal-ai/seedance-2.0/text-to-video", {"prompt": "..."}),
    webhook_url="https://my.app/api/fal/webhook",
)
# store h.request_id; receive POST on completion
```

### 14.4 CDN upload + image-to-image
```python
import fal_client
from safety_off import with_safety_off

ref_url = fal_client.upload_file("./ref.jpg")
result = fal_client.subscribe(
    "fal-ai/flux-pro/v1.1-ultra",
    arguments=with_safety_off("fal-ai/flux-pro/v1.1-ultra", {
        "prompt": "make it sunset",
        "image_url": ref_url,
        "image_prompt_strength": 0.6,
        "aspect_ratio": "16:9",
    }),
)
```

### 14.5 Stream a workflow
```python
import fal_client
from safety_off import with_safety_off

stream = fal_client.stream(
    "workflows/fal-ai/4x4-grid-images",
    arguments=with_safety_off("workflows/fal-ai/4x4-grid-images", {"prompt": "a cute puppy"}),
)
for event in stream:
    print(event)
```

### 14.6 OpenAI-compatible LLM via fal proxy
```python
import fal_client
result = fal_client.subscribe("openrouter/router/openai/v1/chat/completions", arguments={
    "model": "anthropic/claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Hello"}],
})
print(result["choices"][0]["message"]["content"])
```

### 14.7 Music with explicit lyrics
```python
import fal_client
result = fal_client.subscribe("fal-ai/minimax-music/v2.6", arguments={
    "prompt": "City Pop, 80s, groovy synth, 104 BPM",
    "lyrics": "[verse]\nStreetlights flicker, the night breeze sighs\n[chorus]\nWandering, longing, where should I go",
    "is_instrumental": False,
})
print(result["audio"]["url"])
```

### 14.8 Realtime WebSocket
```python
import fal_client
with fal_client.realtime("fal-ai/fast-sdxl") as c:
    c.send({"prompt": "a cat", "num_inference_steps": 2})
    print(c.recv())
```

---

## 15. Deep references

- **Doc index:** https://fal.ai/docs/llms.txt
- **Inference methods:** https://fal.ai/docs/documentation/model-apis/inference
- **Queue + async:** https://fal.ai/docs/documentation/model-apis/inference/queue
- **Webhooks:** https://fal.ai/docs/documentation/model-apis/inference/webhooks
- **Headers:** https://fal.ai/docs/documentation/model-apis/common-parameters
- **CDN:** https://fal.ai/docs/documentation/model-apis/fal-cdn
- **Streaming:** https://fal.ai/docs/documentation/model-apis/inference/streaming
- **Workflows:** https://fal.ai/docs/documentation/model-apis/workflows
- **Model gallery:** https://fal.ai/models
- **OpenClaw provider:** https://docs.openclaw.ai/providers/fal
- **OpenClaw plugin ref:** https://docs.openclaw.ai/plugins/reference/fal
- **Status page:** https://status.fal.ai
- **Discord:** https://discord.gg/fal-ai
- **Pricing:** https://fal.ai/pricing
