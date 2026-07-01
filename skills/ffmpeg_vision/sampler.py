"""Adaptiv frame-sampling baserat på transkript + LLM-analys.

Mål: extrahera FLER frames vid "intressanta" ställen, färre vid lugna partier.
Intressanta ställen = höjdpunkter, byten av talare, långa pauser, specifika keywords.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TranscriptTimeline:
    """Tidslinje med segment, höjdpunkter och keywords från en episod."""
    duration: float
    segments: list[dict] = field(default_factory=list)  # [{start, end, text}]
    highlights: list[dict] = field(default_factory=list)  # [{timestamp, category, description}]
    speakers: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_files(cls, transcript_json: str | dict, analysis_json: str | dict | None = None) -> "TranscriptTimeline":
        """Bygg från JSON-filer (transcript + ev. analys)."""
        import json
        if isinstance(transcript_json, (str, Path)):
            t = json.loads(Path(transcript_json).read_text())
        else:
            t = transcript_json
        if isinstance(analysis_json, (str, Path)):
            try:
                a = json.loads(Path(analysis_json).read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                a = None
        elif analysis_json is None:
            # Försök hitta analysis_json i samma katalog
            try:
                tp = Path(transcript_json)
                # Letar efter <stem>-analysis.json eller ep-NNN-summary.md
                a = None
            except (TypeError, OSError):
                a = None
        else:
            a = analysis_json
        segments = t.get("segments", [])
        duration = t.get("total_duration_seconds", 0)
        if duration == 0 and segments:
            duration = segments[-1].get("end", 0)
        highlights = []
        if a:
            for h in a.get("highlights", []):
                ts = h.get("approx_timestamp", "")
                ts_sec = _parse_timestamp(str(ts))
                if ts_sec is not None:
                    highlights.append({
                        "timestamp": ts_sec,
                        "category": h.get("category", "other"),
                        "description": h.get("description", ""),
                    })
        # Hitta unika talare från segment-text (heuristik)
        speakers = _detect_speakers_from_segments(segments)
        # Default keywords för podcast/politiska shows
        keywords = [
            "kill", "goodnight", "let's go", "thank you",
            "one minute", "bucket", "pulled",
            "controversial", "wild", "crazy", "hilarious",
            "breaking news", "introducing", "welcome",
        ]
        return cls(
            duration=duration,
            segments=segments,
            highlights=highlights,
            speakers=speakers,
            keywords=keywords,
        )


def _parse_timestamp(ts: str) -> float | None:
    """Parsa 'MM:SS' eller 'HH:MM:SS' till sekunder."""
    if not ts or not isinstance(ts, str):
        return None
    if ":" not in ts:
        try:
            return float(ts)
        except ValueError:
            return None
    parts = ts.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    return None


def _detect_speakers_from_segments(segments: list[dict]) -> list[str]:
    """Försök hitta unika talare (Whisper ger oss inte labels, men vi kan gissa från context)."""
    # Whisper ger oss inte talar-ID, så vi returnerar bara en heuristik
    # av att det finns flera talare om segment-längderna varierar kraftigt
    if not segments:
        return []
    # Hitta unika "röster" via längd-variation
    return ["Speaker A", "Speaker B", "Speaker C"]  # Placeholder — riktig diarization behövs


@dataclass
class AdaptiveSampler:
    """Adaptiv timestamp-sampling baserat på transcript + analys.

    Strategi:
    1. Börja med jämnt intervall (default 30s)
    2. Vid varje highlight: extra frame inom ±5s
    3. Vid keyword i segment: extra frame vid segment-start
    4. Mellan långa pauser (>15s): färre frames
    5. Total budget: max_frames (default 50, $0.01 med Llama 4 Scout)
    """
    timeline: TranscriptTimeline
    base_interval: float = 30.0  # seconds between "regular" frames
    min_interval: float = 5.0  # minimum gap between any two frames
    highlight_radius: float = 5.0  # extra frame ±5s around highlights
    keyword_window: float = 2.0  # if keyword found in segment, add frame
    max_frames: int = 50
    # Weight-multipliers
    weight_highlight: float = 3.0
    weight_keyword: float = 1.5
    weight_regular: float = 1.0
    weight_silence: float = 0.3  # low priority for long silent stretches

    def sample(self) -> list[dict]:
        """Returnera lista med {timestamp, priority, reason}."""
        if self.timeline.duration <= 0:
            return []
        candidates: list[dict] = []
        # 1. Regular interval frames
        t = 0.0
        while t < self.timeline.duration:
            candidates.append({
                "timestamp": round(t, 2),
                "priority": self.weight_regular,
                "reason": "regular",
            })
            t += self.base_interval
        # 2. Highlight frames
        for h in self.timeline.highlights:
            ts = h["timestamp"]
            if ts is None:
                continue
            for offset in [-self.highlight_radius, 0, self.highlight_radius]:
                cand_ts = max(0, min(self.timeline.duration, ts + offset))
                candidates.append({
                    "timestamp": round(cand_ts, 2),
                    "priority": self.weight_highlight,
                    "reason": f"highlight:{h.get('category', '?')}:{h.get('description', '')[:60]}",
                })
        # 3. Keyword-triggered frames
        for seg in self.timeline.segments:
            text = seg.get("text", "").lower()
            for kw in self.timeline.keywords:
                if kw.lower() in text:
                    cand_ts = seg.get("start", 0)
                    candidates.append({
                        "timestamp": round(cand_ts, 2),
                        "priority": self.weight_keyword,
                        "reason": f"keyword:{kw}",
                    })
                    break  # bara en trigger per segment
        # Sortera och dedup (behåll högsta priority vid samma timestamp)
        by_ts: dict[float, dict] = {}
        for c in candidates:
            ts = c["timestamp"]
            # Round till 0.5s för fuzzy match
            ts_key = round(ts * 2) / 2
            if ts_key not in by_ts or c["priority"] > by_ts[ts_key]["priority"]:
                by_ts[ts_key] = c
        # Sortera efter timestamp
        result = sorted(by_ts.values(), key=lambda c: c["timestamp"])
        # Tillämpa min_interval (slå ihop för tätt liggande frames)
        result = self._enforce_min_interval(result)
        # Tillämpa max_frames (behåll högst prioriterade)
        result = self._limit_max_frames(result)
        return result

    def _enforce_min_interval(self, candidates: list[dict]) -> list[dict]:
        """Slå ihop frames som ligger för tätt."""
        if not candidates or self.min_interval <= 0:
            return candidates
        result = [candidates[0]]
        for c in candidates[1:]:
            if c["timestamp"] - result[-1]["timestamp"] >= self.min_interval:
                result.append(c)
            # Om för tätt: ignorera (vi har redan en frame)
        return result

    def _limit_max_frames(self, candidates: list[dict]) -> list[dict]:
        """Behåll högst prioriterade frames om vi har för många."""
        if len(candidates) <= self.max_frames:
            return candidates
        # Sortera efter priority (desc) och välj topp
        indexed = sorted(enumerate(candidates), key=lambda x: -x[1]["priority"])
        kept_indices = set(i for i, _ in indexed[:self.max_frames])
        return [c for i, c in enumerate(candidates) if i in kept_indices]


def sample_adaptive_timestamps(
    transcript_json: str | dict,
    analysis_json: str | dict | None = None,
    base_interval: float = 30.0,
    min_interval: float = 5.0,
    max_frames: int = 50,
) -> list[dict]:
    """Convenience: bygg timeline och kör adaptive sampling."""
    timeline = TranscriptTimeline.from_files(transcript_json, analysis_json)
    sampler = AdaptiveSampler(
        timeline=timeline,
        base_interval=base_interval,
        min_interval=min_interval,
        max_frames=max_frames,
    )
    return sampler.sample()
