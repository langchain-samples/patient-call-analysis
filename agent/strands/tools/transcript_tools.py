"""Transcript ingestion tool for the Strands implementation."""

from strands import tool

from ..mock_data import MOCK_TRANSCRIPT


@tool
def transcribe_call(audio_file_path: str = "") -> str:
    """Transcribe a patient call audio file and return the demo transcript.

    Args:
        audio_file_path: Path to the audio file. Leave empty for demo mode.
    """
    return MOCK_TRANSCRIPT
