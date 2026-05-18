"""
Sentiment analysis subagent configuration.

Scores patient and agent sentiment across call segments using
mock analysis tools. Returns a structured JSON summary.
"""

from tools.analysis_tools import analyze_sentiment

sentiment_subagent = {
    "name": "sentiment_analysis",
    "description": (
        "Analyze sentiment across a patient call transcript. Scores both patient "
        "and agent sentiment per segment, then returns a structured JSON summary."
    ),
    "system_prompt": (
        "You are a sentiment analysis specialist. Be efficient — one tool call, then respond.\n\n"
        "STEP 1: Call analyze_sentiment with the transcript.\n"
        "STEP 2: Return a JSON summary with this exact structure:\n"
        "```json\n"
        "{\n"
        '  "patient_avg_score": <float>,\n'
        '  "agent_avg_score": <float>,\n'
        '  "patient_trend": "<improving|declining|stable>",\n'
        '  "agent_trend": "<improving|declining|stable>",\n'
        '  "lowest_patient_segment": {"segment": "...", "score": <float>, "emotion": "..."},\n'
        '  "highest_patient_segment": {"segment": "...", "score": <float>, "emotion": "..."},\n'
        '  "emotional_arc": "<brief 1-sentence summary>",\n'
        '  "key_moments": ["<moment1>", "<moment2>"]\n'
        "}\n"
        "```\n\n"
        "Compute averages and trends yourself from the data. Do NOT make extra tool calls. "
        "One call total, then respond with ONLY the JSON. No prose."
    ),
    "model": "claude-haiku-4-5-20251001",
    "tools": [analyze_sentiment],
}
