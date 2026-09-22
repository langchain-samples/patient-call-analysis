"""
Transcript ingestion tool with LangSmith file upload.

Generates a realistic MP3 audio file from the mock transcript using macOS TTS
with different voices for patient and agent, then attaches it to the
LangSmith trace for auditability.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path

from langsmith import traceable
from langsmith.schemas import Attachment
from langchain_core.tools import tool

from mock_data import MOCK_TRANSCRIPT

_AUDIO_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "call_recording.mp3")

AGENT_VOICE = "Samantha"
PATIENT_VOICE = "Karen"


def _generate_audio_from_transcript() -> bytes:
    """Generate an MP3 audio file from the mock transcript using macOS TTS.

    Uses different voices for the agent and patient speakers.
    Generates AIFF segments with `say`, concatenates with `sox`,
    then converts to MP3 with `lame`.
    """
    os.makedirs(os.path.dirname(_AUDIO_CACHE_PATH), exist_ok=True)

    segments = []
    for line in MOCK_TRANSCRIPT.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        cleaned = re.sub(r"\[\d{2}:\d{2}:\d{2}\]\s*", "", line)
        if not cleaned:
            continue

        if cleaned.startswith("AGENT:"):
            segments.append((AGENT_VOICE, cleaned.replace("AGENT: ", "", 1)))
        elif cleaned.startswith("PATIENT:"):
            segments.append((PATIENT_VOICE, cleaned.replace("PATIENT: ", "", 1)))

    segment_files = []
    aiff_path = os.path.join(tempfile.gettempdir(), "call_recording_full.aiff")
    try:
        for i, (voice, text) in enumerate(segments):
            seg_path = os.path.join(tempfile.gettempdir(), f"call_seg_{i}.aiff")
            subprocess.run(
                ["say", "-v", voice, "-o", seg_path, "--", text],
                check=True,
                capture_output=True,
            )
            segment_files.append(seg_path)

        if not segment_files:
            subprocess.run(
                ["say", "-o", aiff_path, "--", "Call recording placeholder"],
                check=True,
                capture_output=True,
            )
        elif len(segment_files) == 1:
            os.rename(segment_files[0], aiff_path)
            segment_files = []
        else:
            try:
                subprocess.run(
                    ["sox"] + segment_files + [aiff_path],
                    check=True,
                    capture_output=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                os.rename(segment_files[0], aiff_path)
                segment_files = segment_files[1:]

        # Convert AIFF to MP3
        try:
            subprocess.run(
                ["lame", "--quiet", "-V", "2", aiff_path, _AUDIO_CACHE_PATH],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # lame not available — fall back to AIFF
            os.rename(aiff_path, _AUDIO_CACHE_PATH)

    finally:
        for f in segment_files:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(aiff_path):
            os.remove(aiff_path)

    return Path(_AUDIO_CACHE_PATH).read_bytes()


def _get_audio_bytes() -> tuple[bytes, str]:
    """Get audio bytes and mime type, using cached file if available."""
    if os.path.exists(_AUDIO_CACHE_PATH):
        return Path(_AUDIO_CACHE_PATH).read_bytes(), "audio/mpeg"
    return _generate_audio_from_transcript(), "audio/mpeg"


@traceable(name="transcribe_call_audio")
def _run_transcription(call_audio: Attachment) -> str:
    """Traced function that accepts the audio attachment.

    The @traceable decorator automatically uploads the Attachment
    to the LangSmith trace, making the audio file visible in the UI.
    """
    return MOCK_TRANSCRIPT


@tool
def transcribe_call(audio_file_path: str = "") -> str:
    """Transcribe a patient call audio file and return the transcript.

    Ingests the audio file, produces a transcript, and uploads the audio
    as an attachment to the LangSmith trace for auditability.

    If no audio file is provided, generates audio from the demo transcript.
    The transcript is always the mock demo transcript.

    Args:
        audio_file_path: Path to the audio file. Leave empty for demo mode.
    """
    if audio_file_path and os.path.exists(audio_file_path):
        audio_data = Path(audio_file_path).read_bytes()
        mime_type = "audio/mpeg" if audio_file_path.endswith(".mp3") else "audio/aiff"
    else:
        audio_data, mime_type = _get_audio_bytes()

    attachment = Attachment(mime_type=mime_type, data=audio_data)

    transcript = _run_transcription(call_audio=attachment)

    return transcript
