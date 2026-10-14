"""
Configuration module for the Track 02: Beat the Bot game agent.

This module contains all system constants, API endpoints, and game action schemas
used across the bot system.
"""

from dataclasses import dataclass
from typing import Final

# System Constants
GAME_API_URL: Final[str] = "http://localhost:8000"
SESSION_ID: Final[str] = "session_001"
LOG_FILE_PATH: Final[str] = "decision_audit_log.jsonl"

# Decision Model Thresholds
CONFIDENCE_THRESHOLD: Final[float] = 0.45
MAX_CONTEXT_TOKENS: Final[int] = 512

# Game Loop Configuration
LOOP_FREQUENCY_HZ: Final[float] = 20.0
LOOP_SLEEP_SECONDS: Final[float] = 1.0 / LOOP_FREQUENCY_HZ
API_TIMEOUT_SECONDS: Final[int] = 10

# Game Action Schema
@dataclass(frozen=True)
class GameAction:
    """Represents a valid game action with its display name."""
    name: str
    display_name: str


# Comprehensive Action Set
GAME_ACTIONS: dict[str, GameAction] = {
    "MOVE_UP": GameAction(name="MOVE_UP", display_name="Move Up"),
    "MOVE_DOWN": GameAction(name="MOVE_DOWN", display_name="Move Down"),
    "MOVE_LEFT": GameAction(name="MOVE_LEFT", display_name="Move Left"),
    "MOVE_RIGHT": GameAction(name="MOVE_RIGHT", display_name="Move Right"),
    "WAIT": GameAction(name="WAIT", display_name="Wait"),
    "JUMP": GameAction(name="JUMP", display_name="Jump"),
    "COLLECT": GameAction(name="COLLECT", display_name="Collect"),
    "ATTACK": GameAction(name="ATTACK", display_name="Attack"),
    "DEFEND": GameAction(name="DEFEND", display_name="Defend"),
}

# Action categories for fallback logic
MOVEMENT_ACTIONS: set[str] = {"MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"}
DEFENSIVE_ACTIONS: set[str] = {"WAIT", "DEFEND", "JUMP"}
OFFENSIVE_ACTIONS: set[str] = {"ATTACK", "COLLECT"}

# API Endpoints
ENDPOINT_STATE: Final[str] = f"{GAME_API_URL}/state"
ENDPOINT_MOVE: Final[str] = f"{GAME_API_URL}/move"

# Fallback Configuration
SAFE_MOVE_PRIORITY: list[str] = ["MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"]
HAZARD_ESCAPE_PRIORITY: list[str] = ["JUMP", "MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"]

# Logging Configuration
LOG_ROTATION_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
LOG_TIMESTAMP_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S.%f"
