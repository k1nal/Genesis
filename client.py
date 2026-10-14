"""
Main game execution loop for the Track 02: Beat the Bot agent.

This module implements the continuous non-blocking game loop that:
1. Fetches game state from the REST API
2. Compresses state using deterministic math offloading
3. Queries the Laya decision engine
4. Applies confidence-gated fallbacks
5. Executes actions and logs telemetry
"""

import json
import time
from datetime import datetime
from typing import Any, Dict

import requests

from config import (
    API_TIMEOUT_SECONDS,
    CONFIDENCE_THRESHOLD,
    ENDPOINT_MOVE,
    ENDPOINT_STATE,
    GAME_ACTIONS,
    GAME_API_URL,
    HAZARD_ESCAPE_PRIORITY,
    LOOP_SLEEP_SECONDS,
    LOG_FILE_PATH,
    LOG_TIMESTAMP_FORMAT,
    MOVEMENT_ACTIONS,
    SESSION_ID,
    SAFE_MOVE_PRIORITY,
)
from laya_wrapper import LayaDecisionEngine
from state_compressor import compress_game_state


def get_safe_fallback_move(
    hazard_detected: bool, 
    computed_math: Dict[str, Any]
) -> str:
    """
    Determine a safe fallback action based on game state.
    
    Args:
        hazard_detected: Whether a hazard was detected adjacent to player
        computed_math: Dictionary with computed position data
        
    Returns:
        Safe action name from the action set
    """
    if hazard_detected:
        # Prioritize escape actions when hazard detected
        for action in HAZARD_ESCAPE_PRIORITY:
            if action in GAME_ACTIONS:
                return action
    
    # Otherwise, move toward target
    dX = computed_math.get("dX", 0)
    dY = computed_math.get("dY", 0)
    blocked_directions = computed_math.get("blocked_directions", [])
    
    # Determine preferred direction based on target offset
    if abs(dX) > abs(dY):
        # Prioritize horizontal movement
        if dX > 0 and "RIGHT" not in blocked_directions:
            return "MOVE_RIGHT"
        elif dX < 0 and "LEFT" not in blocked_directions:
            return "MOVE_LEFT"
    else:
        # Prioritize vertical movement
        if dY > 0 and "UP" not in blocked_directions:
            return "MOVE_UP"
        elif dY < 0 and "DOWN" not in blocked_directions:
            return "MOVE_DOWN"
    
    # Fall back to first available safe move
    for action in SAFE_MOVE_PRIORITY:
        if action in GAME_ACTIONS:
            return action
    
    # Last resort: wait
    return "WAIT"


def append_audit_log(
    timestamp: str,
    session_id: str,
    raw_state_snippet: str,
    compressed_context: str,
    laya_probabilities: Dict[str, float],
    selected_action: str,
    fallback_triggered: bool,
    server_status: str,
) -> None:
    """
    Append a decision audit record to the JSONL log file.
    
    Args:
        timestamp: ISO-formatted timestamp
        session_id: Session identifier
        raw_state_snippet: Truncated raw state for debugging
        compressed_context: Compressed text context sent to Laya
        laya_probabilities: Full probability distribution from Laya
        selected_action: Action that was executed
        fallback_triggered: Whether fallback logic was used
        server_status: HTTP status or error message
    """
    log_entry = {
        "timestamp": timestamp,
        "session_id": session_id,
        "raw_state_snippet": raw_state_snippet,
        "compressed_context": compressed_context,
        "laya_probabilities": laya_probabilities,
        "selected_action": selected_action,
        "fallback_triggered": fallback_triggered,
        "server_status": server_status,
    }
    
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except IOError as e:
        print(f"Error writing to audit log: {e}")


def fetch_game_state() -> tuple[Dict[str, Any], str]:
    """
    Fetch the current game state from the API.
    
    Returns:
        Tuple of (state_dict, status_message)
    """
    try:
        params = {"session_id": SESSION_ID}
        response = requests.get(
            ENDPOINT_STATE, 
            params=params, 
            timeout=API_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            return response.json(), f"HTTP {response.status_code}"
        else:
            return {}, f"HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return {}, "API Timeout"
    except requests.exceptions.ConnectionError:
        return {}, "Connection Error"
    except requests.exceptions.RequestException as e:
        return {}, f"Request Error: {str(e)}"
    except json.JSONDecodeError:
        return {}, "Invalid JSON Response"


def execute_action(action: str) -> str:
    """
    Execute an action by POSTing to the game API.
    
    Args:
        action: Action name to execute
        
    Returns:
        Status message from the server
    """
    try:
        payload = {
            "session_id": SESSION_ID,
            "action": action,
        }
        
        response = requests.post(
            ENDPOINT_MOVE,
            json=payload,
            timeout=API_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            return f"HTTP {response.status_code}"
        else:
            return f"HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return "API Timeout"
    except requests.exceptions.ConnectionError:
        return "Connection Error"
    except requests.exceptions.RequestException as e:
        return f"Request Error: {str(e)}"


def game_loop() -> None:
    """
    Main game execution loop running at ~20 Hz.
    
    This loop:
    1. Fetches game state
    2. Checks if game is over
    3. Compresses state and checks for hazards
    4. Queries Laya decision engine
    5. Applies confidence-gated fallback
    6. Executes action
    7. Logs telemetry
    8. Sleeps for 0.05s (20 Hz)
    """
    print(f"Starting game loop for session {SESSION_ID}")
    print(f"API Endpoint: {GAME_API_URL}")
    print(f"Log file: {LOG_FILE_PATH}")
    
    # Initialize Laya decision engine
    laya_engine = LayaDecisionEngine()
    
    if laya_engine.is_model_loaded():
        print("Laya model loaded successfully")
    else:
        print("Using fallback simulation mode")
    
    print("Entering game loop...")
    
    while True:
        # 1. Fetch game state
        state, fetch_status = fetch_game_state()
        
        if not state:
            print(f"Failed to fetch state: {fetch_status}")
            time.sleep(LOOP_SLEEP_SECONDS)
            continue
        
        # 2. Check if game is over
        is_game_over = state.get("is_game_over", state.get("game_over", False))
        if is_game_over:
            print("Game over detected. Exiting loop.")
            break
        
        # 3. Compress state and detect hazards
        compressed_context, hazard_detected, computed_math = compress_game_state(state)
        
        # 4. Query Laya decision engine
        choice_options = {
            action_name: action.display_name 
            for action_name, action in GAME_ACTIONS.items()
        }
        
        laya_probabilities = laya_engine.evaluate_choices(
            compressed_context, 
            choice_options
        )
        
        # 5. Get top choice and check confidence
        top_action, confidence = laya_engine.get_top_choice(laya_probabilities)
        
        # 6. Apply confidence-gated fallback
        fallback_triggered = False
        selected_action = top_action
        
        if confidence < CONFIDENCE_THRESHOLD or hazard_detected:
            fallback_triggered = True
            selected_action = get_safe_fallback_move(hazard_detected, computed_math)
            print(f"Fallback triggered: confidence={confidence:.2f}, hazard={hazard_detected}")
        
        # 7. Execute action
        server_status = execute_action(selected_action)
        
        # 8. Log telemetry
        timestamp = datetime.now().strftime(LOG_TIMESTAMP_FORMAT)
        
        # Create truncated state snippet for logging
        raw_state_snippet = json.dumps(state)[:200] + "..." if len(json.dumps(state)) > 200 else json.dumps(state)
        
        append_audit_log(
            timestamp=timestamp,
            session_id=SESSION_ID,
            raw_state_snippet=raw_state_snippet,
            compressed_context=compressed_context,
            laya_probabilities=laya_probabilities,
            selected_action=selected_action,
            fallback_triggered=fallback_triggered,
            server_status=server_status,
        )
        
        # Sleep for loop frequency
        time.sleep(LOOP_SLEEP_SECONDS)


if __name__ == "__main__":
    try:
        game_loop()
    except KeyboardInterrupt:
        print("\nGame loop interrupted by user")
    except Exception as e:
        print(f"Fatal error in game loop: {e}")
        import traceback
        traceback.print_exc()
