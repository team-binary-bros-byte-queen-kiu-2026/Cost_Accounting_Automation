"""
Central configuration — models and API settings from environment variables.
Lab 11: never hardcode model IDs in call sites.
"""
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Chat / general LLM fallback chain
PRIMARY_MODEL = os.environ.get("PRIMARY_MODEL", "anthropic/claude-3-5-haiku")
SECONDARY_MODEL = os.environ.get("SECONDARY_MODEL", "anthropic/claude-3-5-haiku")
OSS_FALLBACK = os.environ.get("OSS_FALLBACK", "openai/gpt-4o-mini")

# Vision (multimodal) — separate primary, same secondary / OSS fallback
PRIMARY_VISION_MODEL = os.environ.get("PRIMARY_VISION_MODEL", "google/gemini-2.5-flash")

# Aliases used across the codebase
PRIMARY_CHAT_MODEL = PRIMARY_MODEL
TERTIARY_MODEL = OSS_FALLBACK

FALLBACK_CHAIN = [PRIMARY_VISION_MODEL, SECONDARY_MODEL, OSS_FALLBACK]
CHAT_FALLBACK_CHAIN = [PRIMARY_MODEL, SECONDARY_MODEL, OSS_FALLBACK]

# OpenRouter GDPR — opt out of data collection on every request
OPENROUTER_DATA_COLLECTION = "deny"
