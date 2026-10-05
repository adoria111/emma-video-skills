#!/usr/bin/env python3
"""Local transcription adapter; no media uploads, implicit downloads or API keys."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path


def timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds_part, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds_part:02},{milliseconds:03}"


def write_outputs(output: Path, source: Path, model: str, language: str,
                  segments: list[dict]) -> None:
    # Validate before creating anything; keep chronological positive intervals.
    previous_end = 0.0
    for segment in segments:
        start, end = float(segment["start"]), float(segment["end"])
        if not 0 <= start < end or start < previous_end - .001:
            raise ValueError("Transcription has invalid or overlapping segment times; review the raw result")
        previous_end = end
    payload = {"source": str(source.resolve()), "model": model, "language": language,
               "automatic_transcript": True, "segments": segments}
    text = "\n".join(s["text"].strip() for s in segments) + ("\n" if segments else "")
    srt = "\n\n".join(f'{i}\n{timestamp(s["start"])} --> {timestamp(s["end"])}\n{s["text"].strip()}'
                        for i, s in enumerate(segments, 1)) + ("\n" if segments else "")
    output.mkdir(parents=True, exist_ok=False)
    (output / "transcript.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "transcript.txt").write_text(text, encoding="utf-8")
    (output / "transcript.srt").write_text(srt, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model", default="small", help="Cached model name or local model directory")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--allow-model-download", action="store_true")
    args = parser.parse_args()
    source = args.input.expanduser().resolve()
    output = args.output_dir.expanduser().absolute()
    if not source.is_file():
        parser.error("Input must be an existing media file")
    if output.exists() or output.is_symlink():
        parser.error("Output directory must not exist; choose a new path")
    if args.threads < 1:
        parser.error("--threads must be positive")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        parser.exit(1, "Missing faster-whisper. Use a Python environment with the optional transcription dependency.\n")
    try:
        model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=args.threads,
                             local_files_only=not args.allow_model_download)
        segments, info = model.transcribe(str(source), language=args.language, beam_size=3,
                                          word_timestamps=True, vad_filter=True)
        collected = []
        for segment in segments:
            collected.append(asdict(segment))
            print(f"Transcribed through {segment.end:.1f}s", flush=True)
        write_outputs(output, source, args.model, info.language, collected)
    except Exception as exc:
        parser.exit(1, f"Transcription stopped: {exc}\nNo alternative service was called.\n")
    print(f"Saved {len(collected)} segments to {output}")
    if not collected:
        print("No speech recognized; inspect the input audio before treating this as a finished transcript.")


if __name__ == "__main__":
    main()
