# Track 02: Beat the Bot - Headless Python Game Agent

A production-grade headless Python bot system for REST API game interaction with Laya decision model, rule-based fallbacks, and real-time telemetry dashboard.

## System Architecture

- **config.py**: System constants, API endpoints, and game action schemas
- **state_compressor.py**: Game state compression with deterministic math offloading
- **laya_wrapper.py**: Thread-safe Laya decision engine with fallback mode
- **client.py**: Main game execution loop (20 Hz) with confidence-gated fallbacks
- **app.py**: Streamlit dashboard for real-time visualization

## Key Features

- ✅ **No Browser Automation**: Pure HTTP/REST via `requests` library
- ✅ **Laya 421M Model**: Non-autoregressive encoder for calibrated probability outputs
- ✅ **Deterministic Math Offloading**: All calculations done in Python before Laya inference
- ✅ **Token Budget Control**: Context compressed to <512 tokens (2-3 sentences)
- ✅ **Confidence-Gated Fallbacks**: Override Laya if confidence <0.45 or hazard detected
- ✅ **Full Audit Telemetry**: Every decision logged to JSONL with complete context
- ✅ **Real-Time Dashboard**: Streamlit UI with metrics, charts, and live data table
- ✅ **Thread-Safe**: Concurrent dashboard reads and game loop writes

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Install Laya model (will download weights on first use)
pip install laya
```

## Configuration

Edit `config.py` to customize:

```python
GAME_API_URL = "http://localhost:8000"  # Update to your game API endpoint
SESSION_ID = "session_001"              # Your session identifier
CONFIDENCE_THRESHOLD = 0.45             # Fallback trigger threshold
```

## Usage

### Start the Game Agent

```bash
python client.py
```

The agent will:
1. Connect to the game API
2. Run at 20 Hz (0.05s per iteration)
3. Log all decisions to `decision_audit_log.jsonl`
4. Apply fallback logic when confidence is low or hazards detected

### Start the Dashboard

In a separate terminal:

```bash
streamlit run app.py
```

The dashboard displays:
- **Metrics**: Session ID, total decisions, latest move, fallback count
- **Probability Chart**: Real-time Laya probability distribution
- **Context Prompt**: Compressed text sent to Laya
- **Live Log Table**: Last 15 telemetry entries

## System Constraints

1. **Strict No-Browser Policy**: Zero Playwright/Selenium - only HTTP requests
2. **Token Budget**: Laya inputs <512 tokens (pre-compressed state)
3. **Option Cardinality**: <15-20 options per request
4. **Confidence Threshold**: Fallback triggered if confidence <0.45
5. **Deterministic Math**: All arithmetic done in Python, not Laya

## Game State Schema

The state compressor handles flexible JSON schemas:

```json
{
  "player": {"x": 4, "y": 2},
  "target": {"x": 6, "y": 2},
  "obstacles": [{"x": 5, "y": 2}],
  "hazards": [{"x": 4, "y": 3}],
  "is_game_over": false
}
```

Alternative field names are supported:
- Player: `player`, `player_position`, `agent`, `position`
- Target: `target`, `goal`, `objective`, `destination`
- Obstacles: `obstacles`, `walls`, `barriers`
- Hazards: `hazards`, `dangers`, `threats`, `traps`

## Action Set

Comprehensive action set (configurable in `config.py`):

- `MOVE_UP`, `MOVE_DOWN`, `MOVE_LEFT`, `MOVE_RIGHT` - Movement
- `WAIT` - Skip turn
- `JUMP` - Escape hazard
- `COLLECT` - Gather item
- `ATTACK` - Offensive action
- `DEFEND` - Defensive action

## Fallback Logic

Fallback triggers when:
- Laya confidence < 0.45
- Hazard detected adjacent to player
- Model unavailable (offline/initial download)

Fallback priority:
1. **Hazard detected**: JUMP → Movement away from hazard
2. **Clear path**: Move toward target (based on dX, dY offsets)
3. **Blocked**: Avoid blocked directions
4. **Last resort**: WAIT

## Telemetry Log Format

Each decision logged to `decision_audit_log.jsonl`:

```json
{
  "timestamp": "2026-10-14 09:30:00.123456",
  "session_id": "session_001",
  "raw_state_snippet": "{\"player\":{\"x\":4,\"y\":2}...",
  "compressed_context": "Player at (4,2). Target offset: dX=2, dY=0, distance=2.0. Hazard status: Clear path.",
  "laya_probabilities": {"MOVE_UP": 0.12, "MOVE_RIGHT": 0.82, ...},
  "selected_action": "MOVE_RIGHT",
  "fallback_triggered": false,
  "server_status": "HTTP 200"
}
```

## Laya Model Integration

The system uses the Laya 421M non-autoregressive encoder model:

```python
agent = laya.load("convaiinnovations/laya")
probabilities = agent.evaluate(context_prompt, choice_options)
```

**Fallback Mode**: If Laya is unavailable, the system uses a context-aware simulation that:
- Generates plausible probability distributions
- Biases toward target movement
- Boosts defensive actions when hazards detected
- Avoids blocked directions

## Performance

- **Loop Frequency**: 20 Hz (0.05s per iteration)
- **Token Budget**: <512 tokens per inference
- **Latency**: ~50ms per decision (API + Laya + fallback)
- **Log Size**: ~500 bytes per decision entry

## Troubleshooting

### API Connection Issues
- Verify `GAME_API_URL` in `config.py`
- Check API is running and accessible
- Ensure session ID is valid

### Laya Model Not Loading
- System automatically uses fallback mode
- Install with: `pip install laya`
- Model weights download on first use (~500MB)

### Dashboard Not Updating
- Check `decision_audit_log.jsonl` is being written
- Verify log file path in `config.py`
- Streamlit auto-refreshes every 1 second

## License

MIT License - Built for Track 02: Beat the Bot Hackathon
