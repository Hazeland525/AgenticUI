# AgenticUI

A prototype AI agent interface that answers questions using **voice or text** and **video context**. It uses Google Gemini to produce structured UI (cards, steps, images) instead of plain text, and supports a personal collections library and place recommendations.

## Key Features

- **Multimodal input** — Type questions or hold **S** to speak; optional video frame is sent with each request for visual context.
- **Voice (Option B)** — Raw audio + video screenshot go directly to Gemini (no transcription dependency), so answers stay accurate. A separate stream shows the transcribed question for display only.
- **Structured responses** — Intent-driven UI: hero/detail modules, step-by-step (e.g. recipes), simple identification, text-only list layouts. Semantic image matching from a local image library.
- **Collections** — Save answers via the **Add** button or voice; personal library (SQLite), gallery view, reload or delete items.
- **Recommendations** — Ask for places (e.g. “Recommend Italian restaurants”); uses user profile, Maps Grounding Lite, and Places API for rich cards (photos, ratings, links).

- **AI Mute** — TTS plays by default for answers; use the **Mute** button to stop or silence future playback.

## Tech Stack

- **Frontend:** React 18, TypeScript, React Router, Axios.
- **Backend:** FastAPI, Google Gemini, SQLite. Services: Gemini (LLM + audio/image), Speech (transcription + voice-command detection), Maps + Places, Storage, User Profile, Image Search.

## Demo

**[AgenticUI – Voice, text, and video context](https://youtu.be/1vRQO1jcMXo)**  
Demo video on YouTube showing the prototype in action.

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 16+
- Google API key with access to: Generative Language (Gemini), Speech-to-Text, Maps Grounding Lite, Places API (see `GOOGLE_CLOUD_SPEECH_SETUP.md` for details).

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Create `backend/.env`:

```bash
GEMINI_API_KEY=your_google_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

Run:

```bash
python main.py
```

Backend: `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

### Optional

- **User profile** for recommendations: edit `backend/data/user_profile.json` (name, location, etc.).

## Project Structure (high level)

- `backend/` — FastAPI app, `agent_executor.py` (ask + ask-with-voice), `agent.py`, `prompt_builder.py`, `services/` (gemini, speech, maps, storage, image_search), `routes/`, `data/`, `images/`.
- `frontend/` — React app, `App.tsx`, `QuestionInput`, `Sidebar`, `CollectionsPage`, `services/`, `hooks/` (e.g. voice input), schema renderer.

## License

Prototype/research project. See component licenses as needed.
