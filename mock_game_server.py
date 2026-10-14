"""
Mock game server for testing the bot system.

This is a simple Flask server that simulates the game API endpoints
for testing purposes without requiring the actual game server.
"""

from flask import Flask, jsonify, request
import random

app = Flask(__name__)

# Game state
game_state = {
    "player": {"x": 0, "y": 0},
    "target": {"x": 10, "y": 10},
    "obstacles": [],
    "hazards": [],
    "is_game_over": False
}

@app.route('/state')
def get_state():
    """Return current game state."""
    session_id = request.args.get('session_id', 'default')
    
    # Add some randomness to simulate dynamic game
    if random.random() < 0.1:
        game_state['hazards'] = [{"x": random.randint(-2, 2), "y": random.randint(-2, 2)}]
    else:
        game_state['hazards'] = []
    
    # Add obstacles occasionally
    if random.random() < 0.05:
        game_state['obstacles'] = [{"x": random.randint(0, 10), "y": random.randint(0, 10)}]
    
    return jsonify(game_state)

@app.route('/move', methods=['POST'])
def make_move():
    """Process a move action."""
    data = request.json
    action = data.get('action', 'WAIT')
    
    # Simulate player movement based on action
    if action == 'MOVE_UP':
        game_state['player']['y'] += 1
    elif action == 'MOVE_DOWN':
        game_state['player']['y'] -= 1
    elif action == 'MOVE_LEFT':
        game_state['player']['x'] -= 1
    elif action == 'MOVE_RIGHT':
        game_state['player']['x'] += 1
    
    # Check if target reached
    if (game_state['player']['x'] == game_state['target']['x'] and 
        game_state['player']['y'] == game_state['target']['y']):
        game_state['is_game_over'] = True
    
    return jsonify({"status": "success", "action": action})

if __name__ == '__main__':
    print("Mock game server starting on http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=False)
