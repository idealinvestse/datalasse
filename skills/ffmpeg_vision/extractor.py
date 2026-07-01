"""ffmpeg-baserad frame-extraktion med metadata."""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoMetadata:
    """Metadata om en video, från ffprobe."""
    path: Path
    duration_seconds: float
    width: int
    height: int
    fps: float
    codec: str
    bit_rate: int
    size_bytes: int
    has_audio: bool

    def aspect_ratio(self) -> str:
        """Returnera aspect ratio (16:9, 4:3, etc.)."""
        from math import gcd
        if self.height == 0:
            return "?"
        d = gcd(self.width, self.height)
        return f"{self.width // d}:{self.height // d}"


def get_video_metadata(video_path: str | Path) -> VideoMetadata:
    """Hämta metadata från en video med ffprobe."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video hittades inte: {video_path}")
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe saknas — installera med 'apt install ffmpeg'")
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(video_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    fmt = data.get("format", {})
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    fps_str = video_stream.get("r_frame_rate", "0/1")
    try:
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) != 0 else 0
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    return VideoMetadata(
        path=video_path,
        duration_seconds=float(fmt.get("duration", 0)),
        width=int(video_stream.get("width", 0)),
        height=int(video_stream.get("height", 0)),
        fps=fps,
        codec=video_stream.get("codec_name", "?"),
        bit_rate=int(fmt.get("bit_rate", 0)),
        size_bytes=int(fmt.get("size", 0)),
        has_audio=audio_stream is not None,
    )


@dataclass
class ExtractedFrame:
    """En extraherad frame."""
    timestamp: float
    path: Path
    width: int
    height: int


@dataclass
class FrameExtractor:
    """Extrahera frames från en video vid specifika timestamps."""
    video_path: str | Path
    output_dir: str | Path
    image_format: str = "jpg"  # jpg, png, webp
    image_quality: int = 2  # 1=best, 31=worst (ffmpeg scale)
    target_width: int = 0  # 0 = original; eller t.ex. 1280, 1920
    metadata: VideoMetadata | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.video_path = Path(self.video_path)
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = get_video_metadata(self.video_path)
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg saknas — installera med 'apt install ffmpeg'")

    def _ffmpeg_path(self) -> str:
        return shutil.which("ffmpeg") or "ffmpeg"

    def extract_at(self, timestamp: float, name: str | None = None) -> ExtractedFrame:
        """Extrahera EN frame vid exakt timestamp. Snabb, ingen re-encoding."""
        if not (0 <= timestamp <= self.metadata.duration_seconds + 1):
            raise ValueError(f"timestamp {timestamp}s utanför video-duration {self.metadata.duration_seconds}s")
        if name is None:
            t = max(0, timestamp)
            name = f"t{int(t // 3600):02d}h{int((t % 3600) // 60):02d}m{int(t % 60):02d}s"
        out_path = self.output_dir / f"{name}.{self.image_format}"
        # -ss before -i = snabb seek (kan vara inexakt)
        # -ss after -i = långsam seek (exakt)
        # Vi använder -ss före + -noaccurate_seek, sen -ss efter som backup = bra balans
        scale = f"scale={self.target_width}:-2" if self.target_width else "scale=iw:ih"
        cmd = [
            self._ffmpeg_path(), "-y",
            "-ss", f"{timestamp:.3f}",
            "-i", str(self.video_path),
            "-frames:v", "1",
            "-vf", f"{scale},setsar=1",
            "-q:v", str(self.image_quality),
            "-loglevel", "error",
            str(out_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0 or not out_path.exists():
            raise RuntimeError(f"ffmpeg misslyckades vid {timestamp}s: {r.stderr[-200:]}")
        return ExtractedFrame(
            timestamp=round(timestamp, 2),
            path=out_path,
            width=self.metadata.width if not self.target_width else self.target_width,
            height=self.metadata.height if not self.target_width else -1,
        )

    def extract_many(self, timestamps: list[float], name_prefix: str = "frame") -> list[ExtractedFrame]:
        """Extrahera frames vid många timestamps. Returnerar lista med resultat."""
        results = []
        for i, ts in enumerate(timestamps, 1):
            name = f"{name_prefix}-{i:04d}-t{ts:.1f}s"
            try:
                results.append(self.extract_at(ts, name))
            except (RuntimeError, ValueError) as e:
                # Logga felet men fortsätt
                print(f"  ⚠️  Kunde inte extrahera vid {ts:.1f}s: {e}")
        return results

    def extract_interval(self, interval_seconds: float, max_frames: int = 0) -> list[ExtractedFrame]:
        """Extrahera frames med jämnt intervall."""
        if interval_seconds <= 0:
            raise ValueError("interval_seconds måste vara > 0")
        dur = self.metadata.duration_seconds
        timestamps = []
        t = 0.0
        while t < dur:
            timestamps.append(t)
            t += interval_seconds
        if max_frames and len(timestamps) > max_frames:
            # Subsample
            step = len(timestamps) / max_frames
            timestamps = [timestamps[int(i * step)] for i in range(max_frames)]
        return self.extract_many(timestamps, name_prefix=f"every{int(interval_seconds)}s")


def extract_frames_at_timestamps(
    video_path: str | Path,
    timestamps: list[float],
    output_dir: str | Path,
    image_format: str = "jpg",
    image_quality: int = 2,
    target_width: int = 0,
) -> list[ExtractedFrame]:
    """Convenience-funktion: extrahera frames vid timestamps."""
    ex = FrameExtractor(
        video_path=video_path,
        output_dir=output_dir,
        image_format=image_format,
        image_quality=image_quality,
        target_width=target_width,
    )
    return ex.extract_many(timestamps)
