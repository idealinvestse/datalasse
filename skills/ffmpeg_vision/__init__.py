"""ffmpeg-vision: kostnadseffektiv frame-extraktion + vision-LLM-beskrivning av videor.

Två huvudsakliga användningsområden:
1. **Adaptiv frame-extraktion** från en video baserat på ett transkript
   - Extraherar frames tätare vid "viktiga" ställen (höjdpunkter, byten av talare, keywords)
   - Glesare vid lugna partier
   - Default 5-30s intervall, konfigurerbart
2. **Vision-beskrivning** av frames via billig LLM (Llama 4 Scout som default)

Modell: billig som standard, dyr vid behov (cost-routing).
"""
from .extractor import FrameExtractor, extract_frames_at_timestamps, get_video_metadata
from .sampler import AdaptiveSampler, TranscriptTimeline, sample_adaptive_timestamps
from .vision import VisionDescriber, describe_frames, MODELS

__version__ = "0.1.0"
__all__ = [
    "FrameExtractor",
    "extract_frames_at_timestamps",
    "get_video_metadata",
    "AdaptiveSampler",
    "TranscriptTimeline",
    "sample_adaptive_timestamps",
    "VisionDescriber",
    "describe_frames",
    "MODELS",
]
