# 🧩 BlockVision Edu

> *Snap a photo of physical code blocks → watch a Scratch cat bring them to life.*

A kids' educational robotics programming tool inspired by Matatalab.
Children place colored blocks on a table, photograph them with a phone,
and watch an animated cat execute the program in a web browser.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Photo analysis** | OpenCV HSV color detection — no ML model required |
| **Block types** | Move Up/Down/Left/Right, Loop (with digit OCR), Start |
| **Cat stage** | Scratch-like animated sprite on an 8×8 grid |
| **Real-time WS** | Step-by-step execution streamed over WebSocket |
| **Nested loops** | Full recursive Composite Pattern support |
| **Extensible** | Add new block types with one class + one config line |

---

## 🏗️ Architecture

```
block_vision_edu/
│
├── main.py                      # Entry point (uvicorn)
├── requirements.txt
│
├── backend/
│   ├── app.py                   # FastAPI app factory
│   ├── config.py                # Pydantic-settings (env vars)
│   ├── dependencies.py          # FastAPI DI providers
│   │
│   ├── models/
│   │   ├── block_models.py      # Domain: BlockType, DetectedBlock, BoundingBox
│   │   └── api_models.py        # HTTP/WS schemas (Pydantic)
│   │
│   ├── detection/               # ── VISION LAYER ──
│   │   ├── base_detector.py     # Abstract Strategy contract
│   │   ├── color_block_detector.py  # OpenCV HSV implementation
│   │   ├── block_sorter.py      # Spatial reading-order sort
│   │   └── color_config.py      # HSV ranges per block color
│   │
│   ├── commands/                # ── COMMAND LAYER ──
│   │   ├── base_command.py      # Abstract Command
│   │   ├── movement_commands.py # Move{Up,Down,Left,Right}Command
│   │   ├── loop_command.py      # LoopCommand (Composite)
│   │   └── command_factory.py   # Factory + recursive parser
│   │
│   ├── services/
│   │   └── program_service.py   # Orchestrator (Facade)
│   │
│   └── api/
│       ├── image_router.py      # POST /api/analyze-image
│       └── websocket_router.py  # WS  /ws/execute
│
├── frontend/
│   ├── index.html               # Single-page app
│   ├── css/style.css            # Full design system
│   └── js/
│       ├── config.js            # All constants
│       ├── api.js               # HTTP + WebSocket client
│       ├── stage.js             # Cat sprite controller
│       ├── ui.js                # All DOM operations
│       └── app.js               # App controller (Mediator)
│
└── tests/
    ├── conftest.py
    ├── test_block_sorter.py
    ├── test_command_factory.py
    └── test_program_service.py
```

---

## 🎨 Design Patterns Used

| Pattern | Where | Why |
|---|---|---|
| **Strategy** | `BaseBlockDetector` | Swap color detector for ML model without changing anything |
| **Command** | `BaseCommand` subclasses | Each block = encapsulated, independently testable action |
| **Composite** | `LoopCommand` | Nested loops for free, no special-case code |
| **Factory** | `CommandFactory` | Translates domain blocks → command tree, one place |
| **Facade** | `ProgramService` | One clean entry point for the API layer |
| **Dependency Injection** | `dependencies.py` | Testable routes; swap implementations in tests |
| **Mediator** | `app.js` | JS controller wires UI/Stage/API without coupling them |

---

## ⚙️ SOLID Principles Applied

- **S** — Every class has one job (`BlockSorter` sorts, `CommandFactory` builds, `ProgramService` orchestrates).
- **O** — Add a block type by adding a class + one config line. Nothing existing changes.
- **L** — Any `BaseBlockDetector` subclass can replace `ColorBlockDetector` safely.
- **I** — `BaseCommand.to_steps()` is the only interface — no fat interfaces.
- **D** — `ProgramService` depends on `BaseBlockDetector`, not `ColorBlockDetector`.

---

## 🚀 Quick Start

### 1 — Install

```bash
# Clone the repo
git clone https://github.com/yourname/block-vision-edu
cd block-vision-edu

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: OCR for loop count digits
sudo apt install tesseract-ocr    # Ubuntu/Debian
brew install tesseract            # macOS
```

### 2 — Run

```bash
python main.py
# → http://localhost:8000
```

### 3 — Use

1. Open `http://localhost:8000` on any device (desktop or phone).
2. Print and laminate colored blocks (see color guide below).
3. Arrange blocks on a flat, well-lit surface.
4. **On phone**: tap "Take a Photo" → use camera.
5. Tap **Analyze Blocks** — detected sequence appears.
6. Tap **▶ Run** — the cat executes your program!

---

## 🎨 Block Color Guide

Print these colors on 6×6 cm square cards:

| Block | Color | Purpose |
|---|---|---|
| 🟢 **Start** | Bright Green `#52C41A` | Program begins here |
| 🔵 **Move Up** | Sky Blue `#4A90D9` | Cat moves one cell up |
| 🔴 **Move Down** | Red `#E03030` | Cat moves one cell down |
| 🟡 **Move Left** | Yellow `#FADB14` | Cat moves one cell left |
| 🟣 **Move Right** | Purple `#722ED1` | Cat moves one cell right |
| 🟠 **Loop Start** | Orange `#FA8C16` | Write a digit (2–9) on the block |
| 🩷 **Loop End** | Magenta `#EB2F96` | Marks end of loop body |

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 🔌 Adding a New Block Type

1. Choose a distinct color → add to `color_config.py`:
   ```python
   BlockType.JUMP: ColorProfile(lower=(…), upper=(…))
   ```
2. Add enum value to `BlockType` in `block_models.py`.
3. Create `JumpCommand(BaseCommand)` in `commands/`.
4. Register in `CommandFactory._MOVEMENT_MAP`.
5. Add display metadata to frontend `config.js → BLOCK_META`.

That's it — no other file changes needed.

---

## 📱 Phone Deployment

To use your phone as the camera:

```bash
# Make the server reachable on your local network
uvicorn main:app --host 0.0.0.0 --port 8000

# Connect phone to same WiFi
# Open: http://<your-laptop-ip>:8000
# The "Take a Photo" button triggers the phone camera directly
```

For HTTPS (required for camera on some browsers):
```bash
pip install uvicorn[standard]
uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
```
