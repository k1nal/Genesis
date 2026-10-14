"""
Game state compression module with deterministic math offloading.

This module processes raw game state JSON, calculates relative positions and hazard
proximity using Python arithmetic, and compresses the context into a compact
text representation suitable for the Laya decision model.
"""

from typing import Any, Dict, Tuple


def compress_game_state(raw_json: Dict[str, Any]) -> Tuple[str, bool, Dict[str, Any]]:
    """
    Compress raw game state into a compact text representation.
    
    This function:
    1. Parses the raw JSON state from the game API
    2. Calculates exact player/target relative offsets using Python arithmetic
    3. Checks 1-tile adjacent hazard boundaries
    4. Formats a compressed text string under 512 tokens
    
    Args:
        raw_json: Raw game state dictionary from the API
        
    Returns:
        Tuple containing:
        - compressed_prompt: 2-3 sentence compressed text context
        - hazard_detected_flag: True if hazard is adjacent to player
        - computed_math_dict: Dictionary with all calculated values
    """
    # Extract player position with flexible field name handling
    player_pos = _extract_position(raw_json, ["player", "player_position", "agent", "position"])
    player_x, player_y = player_pos[0], player_pos[1]
    
    # Extract target position
    target_pos = _extract_position(raw_json, ["target", "goal", "objective", "destination"])
    target_x, target_y = target_pos[0], target_pos[1]
    
    # Calculate relative offsets (deterministic math offloading)
    dX = target_x - player_x
    dY = target_y - player_y
    distance = (dX ** 2 + dY ** 2) ** 0.5  # Euclidean distance
    
    # Extract obstacles and hazards
    obstacles = _extract_list(raw_json, ["obstacles", "walls", "barriers"])
    hazards = _extract_list(raw_json, ["hazards", "dangers", "threats", "traps"])
    
    # Check for adjacent hazards (1-tile boundary check)
    hazard_detected = _check_adjacent_hazards(player_x, player_y, hazards)
    
    # Check for adjacent obstacles
    blocked_directions = _check_adjacent_obstacles(player_x, player_y, obstacles)
    
    # Determine movement status
    if hazard_detected:
        movement_status = "IMMEDIATE HAZARD nearby"
    elif blocked_directions:
        movement_status = f"Blocked: {', '.join(blocked_directions)}"
    else:
        movement_status = "Clear path"
    
    # Build compressed prompt (2-3 qualitative sentences)
    compressed_prompt = (
        f"Player at ({player_x},{player_y}). "
        f"Target offset: dX={dX}, dY={dY}, distance={distance:.1f}. "
        f"Hazard status: {movement_status}."
    )
    
    # Computed math dictionary for debugging and telemetry
    computed_math_dict = {
        "player_position": (player_x, player_y),
        "target_position": (target_x, target_y),
        "dX": dX,
        "dY": dY,
        "distance": distance,
        "hazard_detected": hazard_detected,
        "blocked_directions": blocked_directions,
        "obstacle_count": len(obstacles),
        "hazard_count": len(hazards),
    }
    
    return compressed_prompt, hazard_detected, computed_math_dict


def _extract_position(data: Dict[str, Any], possible_keys: list[str]) -> Tuple[int, int]:
    """
    Extract a position (x, y) from JSON data with flexible key matching.
    
    Args:
        data: JSON data dictionary
        possible_keys: List of possible field names to check
        
    Returns:
        Tuple of (x, y) coordinates, defaults to (0, 0) if not found
    """
    for key in possible_keys:
        if key in data:
            pos = data[key]
            if isinstance(pos, dict):
                # Handle nested position like {"x": 4, "y": 2}
                return (pos.get("x", 0), pos.get("y", 0))
            elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
                # Handle array like [4, 2]
                return (int(pos[0]), int(pos[1]))
    return (0, 0)


def _extract_list(data: Dict[str, Any], possible_keys: list[str]) -> list[Any]:
    """
    Extract a list from JSON data with flexible key matching.
    
    Args:
        data: JSON data dictionary
        possible_keys: List of possible field names to check
        
    Returns:
        List of items, empty list if not found
    """
    for key in possible_keys:
        if key in data:
            items = data[key]
            if isinstance(items, list):
                return items
    return []


def _check_adjacent_hazards(
    player_x: int, 
    player_y: int, 
    hazards: list[Any]
) -> bool:
    """
    Check if any hazard is adjacent to the player (1-tile boundary).
    
    Args:
        player_x: Player X coordinate
        player_y: Player Y coordinate
        hazards: List of hazard positions
        
    Returns:
        True if hazard is adjacent, False otherwise
    """
    adjacent_offsets = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Up, Down, Right, Left
    
    for hazard in hazards:
        hazard_pos = _extract_position_from_item(hazard)
        hazard_x, hazard_y = hazard_pos[0], hazard_pos[1]
        
        # Check if hazard is in any adjacent position
        for dx, dy in adjacent_offsets:
            if hazard_x == player_x + dx and hazard_y == player_y + dy:
                return True
    
    return False


def _check_adjacent_obstacles(
    player_x: int, 
    player_y: int, 
    obstacles: list[Any]
) -> list[str]:
    """
    Check which directions are blocked by adjacent obstacles.
    
    Args:
        player_x: Player X coordinate
        player_y: Player Y coordinate
        obstacles: List of obstacle positions
        
    Returns:
        List of blocked direction names (e.g., ["UP", "RIGHT"])
    """
    adjacent_offsets = {
        "UP": (0, 1),
        "DOWN": (0, -1),
        "RIGHT": (1, 0),
        "LEFT": (-1, 0),
    }
    
    blocked = []
    
    for obstacle in obstacles:
        obstacle_pos = _extract_position_from_item(obstacle)
        obstacle_x, obstacle_y = obstacle_pos[0], obstacle_pos[1]
        
        for direction, (dx, dy) in adjacent_offsets.items():
            if obstacle_x == player_x + dx and obstacle_y == player_y + dy:
                blocked.append(direction)
    
    return blocked


def _extract_position_from_item(item: Any) -> Tuple[int, int]:
    """
    Extract position from a single item (obstacle or hazard).
    
    Args:
        item: Either a dict with x/y keys or a list/tuple
        
    Returns:
        Tuple of (x, y) coordinates, defaults to (0, 0)
    """
    if isinstance(item, dict):
        return (item.get("x", 0), item.get("y", 0))
    elif isinstance(item, (list, tuple)) and len(item) >= 2:
        return (int(item[0]), int(item[1]))
    return (0, 0)
