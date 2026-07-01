"""Vision-LLM-beskrivning med kostnadsstyrd modell-routing.

Default: billig modell (Llama 4 Scout via Groq eller OpenRouter)
Valfri: dyr modell (Claude Sonnet vision via OpenRouter) för viktiga frames
"""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# Modellregister: billig → dyr
@dataclass
class VisionModel:
    name: str
    provider: str  # "groq" | "openrouter" | "openai" | "anthropic"
    model_id: str
    cost_input_per_million: float
    cost_output_per_million: float
    supports_video: bool = False
    max_tokens: int = 4096
    description: str = ""
    # ~1700 tokens för 1920x1080-bild, ~85 för lågupplöst
    avg_tokens_per_image: int = 1100


MODELS: dict[str, VisionModel] = {
    # Billig: Llama 4 Scout 17B (vision) via Groq
    "llama-4-scout-groq": VisionModel(
        name="Llama 4 Scout 17B",
        provider="groq",
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        cost_input_per_million=0.10,  # Groq pricing
        cost_output_per_million=0.30,
        supports_video=False,
        max_tokens=4096,
        description="Billigaste vision-LLM med bra kvalitet. Default.",
        avg_tokens_per_image=1100,
    ),
    # Billig: Llama 3.2 90B Vision (äldre, via OpenRouter)
    "llama-3.2-90b-vision": VisionModel(
        name="Llama 3.2 90B Vision",
        provider="openrouter",
        model_id="meta-llama/llama-3.2-90b-vision-instruct",
        cost_input_per_million=0.90,  # via OpenRouter
        cost_output_per_million=0.90,
        max_tokens=2048,
        description="Lite äldre, dyrare, men pålitlig vision. Bra för detaljerade scener.",
        avg_tokens_per_image=1100,
    ),
    # Medel: GPT-4o mini via OpenRouter
    "gpt-4o-mini": VisionModel(
        name="GPT-4o mini",
        provider="openrouter",
        model_id="openai/gpt-4o-mini",
        cost_input_per_million=0.15,
        cost_output_per_million=0.60,
        max_tokens=4096,
        description="OpenAI:s billiga vision. Bra för de flesta användningsfall.",
        avg_tokens_per_image=1100,
    ),
    # Dyr: Claude Sonnet 4.5 vision via OpenRouter
    "claude-sonnet-vision": VisionModel(
        name="Claude Sonnet 4.5",
        provider="openrouter",
        model_id="anthropic/claude-sonnet-4.5",
        cost_input_per_million=3.00,
        cost_output_per_million=15.00,
        max_tokens=8192,
        description="Bästa kvalitet. Använd sparsamt för viktiga frames.",
        avg_tokens_per_image=1300,
    ),
    # Dyr: GPT-4o (full) via OpenRouter
    "gpt-4o": VisionModel(
        name="GPT-4o",
        provider="openrouter",
        model_id="openai/gpt-4o",
        cost_input_per_million=2.50,
        cost_output_per_million=10.00,
        max_tokens=4096,
        description="Bästa universal-vision. Använd för svåra scener.",
        avg_tokens_per_image=1100,
    ),
}


def estimate_cost(model_key: str, num_frames: int, prompt_tokens: int = 200, output_tokens: int = 200) -> float:
    """Uppskatta kostnad för att beskriva N frames."""
    m = MODELS[model_key]
    input_tokens = num_frames * m.avg_tokens_per_image + prompt_tokens
    output_tokens_total = num_frames * output_tokens
    cost = (input_tokens / 1_000_000) * m.cost_input_per_million + \
           (output_tokens_total / 1_000_000) * m.cost_output_per_million
    return round(cost, 4)


def _encode_image(path: Path) -> str:
    """Läs bild och returnera base64-data-URL."""
    suffix = path.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "gif": "gif"}.get(suffix, "jpeg")
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/{mime};base64,{b64}"


def _call_groq_vision(model: VisionModel, prompt: str, images: list[Path], max_tokens: int) -> tuple[str, int, int]:
    """Anropa Groq med vision-input."""
    import requests
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY saknas")
    url = "https://api.groq.com/openai/v1/chat/completions"
    content: list[dict] = [{"type": "text", "text": prompt}]
    for img in images:
        content.append({"type": "image_url", "image_url": {"url": _encode_image(img)}})
    payload = {
        "model": model.model_id,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Groq vision fel {r.status_code}: {r.text[:300]}")
    result = r.json()
    text = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _call_openrouter_vision(model: VisionModel, prompt: str, images: list[Path], max_tokens: int) -> tuple[str, int, int]:
    """Anropa OpenRouter med vision-input."""
    import requests
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY saknas")
    url = "https://openrouter.ai/api/v1/chat/completions"
    content: list[dict] = [{"type": "text", "text": prompt}]
    for img in images:
        content.append({"type": "image_url", "image_url": {"url": _encode_image(img)}})
    payload = {
        "model": model.model_id,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/idealinvestse/datalasse",
        "X-Title": "Moss/ffmpeg-vision",
    }
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"OpenRouter vision fel {r.status_code}: {r.text[:300]}")
    result = r.json()
    text = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


@dataclass
class FrameDescription:
    """Beskrivning av en frame."""
    frame_path: Path
    timestamp: float
    description: str
    model: str
    cost_usd: float = 0.0


@dataclass
class VisionDescriber:
    """Beskriv frames med vision-LLM."""
    model_key: str = "llama-4-scout-groq"
    prompt_template: str = (
        "Beskriv denna bild kort och koncist på svenska (max 2 meningar). "
        "Fokusera på: 1) vem/vad som syns, 2) var (plats/scen), 3) känsla/stämning. "
        "Om text syns, inkludera nyckelfraser."
    )
    max_tokens_per_call: int = 300
    images_per_call: int = 1  # 1 = en bild per anrop; >1 = batch
    cost_log: list[dict] = field(default_factory=list)

    def model(self) -> VisionModel:
        if self.model_key not in MODELS:
            raise KeyError(f"Modell '{self.model_key}' finns inte. Tillgängliga: {list(MODELS)}")
        return MODELS[self.model_key]

    def describe(self, frame_path: Path) -> FrameDescription:
        """Beskriv EN frame."""
        return self.describe_many([frame_path])[0]

    def describe_many(self, frame_paths: list[Path]) -> list[FrameDescription]:
        """Beskriv flera frames, batchade enligt images_per_call."""
        results: list[FrameDescription] = []
        m = self.model()
        for i in range(0, len(frame_paths), self.images_per_call):
            batch = frame_paths[i:i + self.images_per_call]
            try:
                if m.provider == "groq":
                    text, in_tok, out_tok = _call_groq_vision(m, self.prompt_template, batch, self.max_tokens_per_call)
                elif m.provider == "openrouter":
                    text, in_tok, out_tok = _call_openrouter_vision(m, self.prompt_template, batch, self.max_tokens_per_call)
                else:
                    raise NotImplementedError(f"Provider '{m.provider}' ej implementerad")
                cost = (in_tok / 1_000_000) * m.cost_input_per_million + \
                       (out_tok / 1_000_000) * m.cost_output_per_million
                self.cost_log.append({
                    "model": self.model_key,
                    "batch_size": len(batch),
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "cost_usd": round(cost, 6),
                })
                # Om batch: splitta beskrivning per frame (eller använd hela texten för första)
                if len(batch) == 1:
                    results.append(FrameDescription(
                        frame_path=batch[0],
                        timestamp=0.0,  # Sätts av anroparen
                        description=text.strip(),
                        model=self.model_key,
                        cost_usd=cost,
                    ))
                else:
                    # Försök splitta på "Bild 1:", "Bild 2:" etc.
                    parts = re.split(r"\n?Bild\s+\d+[:\.]", text)
                    parts = [p.strip() for p in parts if p.strip()]
                    if len(parts) == len(batch):
                        for j, frame in enumerate(batch):
                            results.append(FrameDescription(
                                frame_path=frame,
                                timestamp=0.0,
                                description=parts[j],
                                model=self.model_key,
                                cost_usd=cost / len(batch),
                            ))
                    else:
                        # Kunde inte splitta — använd hela texten för första
                        for j, frame in enumerate(batch):
                            results.append(FrameDescription(
                                frame_path=frame,
                                timestamp=0.0,
                                description=text.strip() if j == 0 else f"(del av batch — se {batch[0].name})",
                                model=self.model_key,
                                cost_usd=cost / len(batch),
                            ))
            except Exception as e:
                for frame in batch:
                    results.append(FrameDescription(
                        frame_path=frame,
                        timestamp=0.0,
                        description=f"[FEL: {e}]",
                        model=self.model_key,
                        cost_usd=0.0,
                    ))
        return results


def describe_frames(
    frame_paths: list[Path],
    model_key: str = "llama-4-scout-groq",
    prompt_template: str | None = None,
    max_frames: int = 50,
) -> list[FrameDescription]:
    """Convenience-funktion: beskriv frames med en modell."""
    if len(frame_paths) > max_frames:
        frame_paths = frame_paths[:max_frames]
    describer = VisionDescriber(
        model_key=model_key,
        prompt_template=prompt_template or VisionDescriber.prompt_template,
    )
    return describer.describe_many(frame_paths)
