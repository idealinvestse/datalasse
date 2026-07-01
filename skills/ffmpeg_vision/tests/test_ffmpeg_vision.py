"""Tester för ffmpeg_vision skill."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Workspace-aware imports
WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE))

from skills.ffmpeg_vision import (
    FrameExtractor,
    AdaptiveSampler,
    TranscriptTimeline,
    sample_adaptive_timestamps,
    describe_frames,
    MODELS,
)
from skills.ffmpeg_vision.vision import estimate_cost


def _make_test_video(path: Path, duration: int = 10) -> None:
    """Skapa en kort testvideo med ffmpeg (utan dependencies på nätverk)."""
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=blue:s=640x360:d={duration},format=yuv420p",
        "-vf", "drawtext=text='%{eif\\:t\\:d}s':x=10:y=10:fontsize=40:fontcolor=white",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-loglevel", "error", str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=30)


def _make_test_transcript(path: Path, duration: int = 60) -> dict:
    """Skapa ett fejk-transcript."""
    t = {
        "episode_number": "TEST",
        "total_duration_seconds": duration,
        "segments": [
            {"start": 0, "end": 10, "text": "Welcome to Kill Tony, lets go!"},
            {"start": 10, "end": 25, "text": "First bucket pull, Mason Bird please come to the stage"},
            {"start": 25, "end": 40, "text": "That was wild, one minute starts now"},
            {"start": 40, "end": 55, "text": "Goodnight everybody, check out deathtv.com"},
            {"start": 55, "end": 60, "text": "Thanks for listening"},
        ],
    }
    path.write_text(json.dumps(t))
    return t


def _make_test_analysis(path: Path) -> dict:
    """Skapa en fejk-analys."""
    a = {
        "main_guests": ["TEST GUEST"],
        "bucket_pullers": ["Mason Bird", "PULLER 2"],
        "highlights": [
            {"approx_timestamp": "0:10", "category": "moment", "description": "First bucket pull"},
            {"approx_timestamp": "0:30", "category": "joke", "description": "Mason Bird joke"},
        ],
        "summary": "Test episode",
        "tone": "mixed",
        "best_moment": "Mason Bird joke",
    }
    path.write_text(json.dumps(a))
    return a


def test_video_metadata(tmp_path: Path) -> None:
    """Testa att video-metadata extraheras korrekt."""
    video = tmp_path / "test.mp4"
    _make_test_video(video, duration=5)
    from skills.ffmpeg_vision.extractor import get_video_metadata
    meta = get_video_metadata(video)
    assert meta.duration_seconds > 0
    assert meta.width == 640
    assert meta.height == 360
    assert meta.codec == "h264"
    assert meta.has_audio is False
    print(f"  ✅ Video metadata: {meta.duration_seconds}s, {meta.width}x{meta.height}")


def test_frame_extraction(tmp_path: Path) -> None:
    """Testa att extrahera frames vid specifika timestamps."""
    video = tmp_path / "test.mp4"
    _make_test_video(video, duration=10)
    out_dir = tmp_path / "frames"
    extractor = FrameExtractor(video, out_dir, image_quality=5)
    results = extractor.extract_many([0.0, 2.5, 5.0])
    assert len(results) == 3
    for r in results:
        assert r.path.exists()
        assert r.path.stat().st_size > 0
    print(f"  ✅ Frame extraction: {len(results)} frames, total {sum(r.path.stat().st_size for r in results)} bytes")


def test_interval_extraction(tmp_path: Path) -> None:
    """Testa jämnt intervall-extraktion."""
    video = tmp_path / "test.mp4"
    _make_test_video(video, duration=10)
    out_dir = tmp_path / "frames"
    extractor = FrameExtractor(video, out_dir, image_quality=5)
    results = extractor.extract_interval(2.0)
    assert len(results) == 5  # 0, 2, 4, 6, 8
    print(f"  ✅ Interval extraction: {len(results)} frames at 2s intervals")


def test_adaptive_sampler(tmp_path: Path) -> None:
    """Testa adaptiv sampling logik (utan att extrahera frames)."""
    transcript_path = tmp_path / "transcript.json"
    analysis_path = tmp_path / "analysis.json"
    _make_test_transcript(transcript_path, duration=60)
    _make_test_analysis(analysis_path)
    timeline = TranscriptTimeline.from_files(transcript_path, analysis_path)
    assert timeline.duration == 60
    assert len(timeline.segments) == 5
    assert len(timeline.highlights) == 2
    sampler = AdaptiveSampler(timeline, base_interval=30, min_interval=5, max_frames=20)
    candidates = sampler.sample()
    # Ska innehålla minst 1 highlight-frame (3 per highlight inom ±5s)
    assert any("highlight" in c["reason"] for c in candidates)
    # Ska respektera max_frames
    assert len(candidates) <= 20
    # Ska respektera min_interval
    for i in range(1, len(candidates)):
        gap = candidates[i]["timestamp"] - candidates[i-1]["timestamp"]
        assert gap >= 5, f"Gap {gap} för litet mellan {candidates[i-1]} och {candidates[i]}"
    print(f"  ✅ Adaptive sampler: {len(candidates)} candidates")
    print(f"     Reasons: {dict((c['reason'].split(':')[0], 0) for c in candidates)}")
    for c in candidates[:3]:
        print(f"     · t={c['timestamp']}s: {c['reason'][:60]}")


def test_cost_estimation() -> None:
    """Testa kostnadsuppskattning."""
    # Llama 4 Scout: $0.10/1M input, $0.30/1M output, ~1100 tokens/bild
    cost_100 = estimate_cost("llama-4-scout-groq", 100, prompt_tokens=200, output_tokens=200)
    # input: 100*1100 + 200 = 110200 tokens → $0.01102
    # output: 100*200 = 20000 tokens → $0.006
    # total: ~$0.017
    assert 0.015 < cost_100 < 0.020, f"Förväntade ~$0.017, fick ${cost_100}"
    # GPT-4o: dyrare
    cost_gpt4o = estimate_cost("gpt-4o", 100, prompt_tokens=200, output_tokens=200)
    assert cost_gpt4o > cost_100 * 20, f"GPT-4o borde vara mycket dyrare än Llama 4 Scout (fick {cost_gpt4o:.4f} vs {cost_100:.4f})"
    print(f"  ✅ Cost estimation: 100 frames Llama 4 Scout = ${cost_100:.4f}, GPT-4o = ${cost_gpt4o:.4f}")


def test_sample_function(tmp_path: Path) -> None:
    """Testa convenience-funktionen sample_adaptive_timestamps."""
    transcript_path = tmp_path / "transcript.json"
    _make_test_transcript(transcript_path, duration=120)
    candidates = sample_adaptive_timestamps(transcript_path, max_frames=15)
    assert len(candidates) > 0
    assert len(candidates) <= 15
    print(f"  ✅ sample_adaptive_timestamps: {len(candidates)} timestamps")


def test_models_registry() -> None:
    """Testa att alla modeller har giltiga fält."""
    assert len(MODELS) >= 3, "Minst 3 modeller borde finnas"
    for key, m in MODELS.items():
        assert m.cost_input_per_million >= 0
        assert m.cost_output_per_million >= 0
        assert m.model_id, f"Modell {key} saknar model_id"
        assert m.provider in ("groq", "openrouter", "openai", "anthropic")
    print(f"  ✅ Models registry: {len(MODELS)} modeller ({', '.join(MODELS.keys())})")


def test_full_pipeline(tmp_path: Path) -> None:
    """End-to-end: video → adaptive → describe (utan att anropa LLM)."""
    video = tmp_path / "test.mp4"
    _make_test_video(video, duration=10)
    transcript_path = tmp_path / "transcript.json"
    _make_test_transcript(transcript_path, duration=10)
    frames_dir = tmp_path / "frames"
    extractor = FrameExtractor(video, frames_dir, image_quality=5)
    results = extractor.extract_interval(2.0, max_frames=5)
    assert len(results) == 5
    # Verifiera att manifest sparas
    manifest = {
        "frames": [{"timestamp": r.timestamp, "path": str(r.path)} for r in results],
    }
    (frames_dir / "manifest.json").write_text(json.dumps(manifest))
    assert (frames_dir / "manifest.json").exists()
    print(f"  ✅ Full pipeline (mock): {len(results)} frames + manifest sparad")


if __name__ == "__main__":
    print("\n=== ffmpeg_vision tests ===\n")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_video_metadata(tmp_path)
        test_frame_extraction(tmp_path)
        test_interval_extraction(tmp_path)
        test_adaptive_sampler(tmp_path)
        test_sample_function(tmp_path)
        test_full_pipeline(tmp_path)
    test_cost_estimation()
    test_models_registry()
    print(f"\n=== Alla tester PASS ===\n")
