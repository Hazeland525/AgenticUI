# AgenticUI

An interactive AI agent interface that combines multimodal input (voice + text + video) with intelligent, context-aware responses. The system provides structured visual answers and personalized recommendations powered by Google Gemini AI.

## Overview

AgenticUI is a prototype that demonstrates how AI agents can provide rich, visually structured responses to user queries. It goes beyond simple text-based chatbots by:

- Understanding natural language queries (voice or text)
- Analyzing video context when relevant
- Generating structured UI components tailored to the query type
- Providing personalized recommendations based on user preferences
- Building a personal knowledge library of saved answers

## Key Features

### 🎤 Multimodal Input
- **Voice Input**: Press and hold the `S` key to speak your question
- **Text Input**: Type queries directly
- **Video Context**: Questions can reference visual content from embedded videos
- Real-time speech-to-text transcription using Google Cloud Speech API

### 🎨 Structured Visual Responses
The AI doesn't just return text—it generates structured UI components based on query intent:

- **Hero Module**: Large visual presentations with key information and imagery
- **Detail Module**: Comprehensive answers with facts, descriptions, and metadata
- **Step Module**: Sequential instructions with progress tracking (e.g., recipes, tutorials)
- **Simple Identification**: Quick facts with text labels for direct answers

Each response is semantically matched with relevant images from the local library.

### 📚 Collections Library
- Save any answer to your personal library with one click
- Gallery view of all saved items with 16:9 image cards
- Click any card to reload the full answer
- Delete items with hover-triggered trash icons
- Persistent storage using SQLite

### 🗺️ AI-Powered Recommendations
- Ask for personalized recommendations (e.g., "Recommend restaurants for Friday")
- System analyzes your **user profile** (location, profession, preferences)
- Infers preferences from your **saved collections**
- Uses **Google Maps Grounding Lite MCP** for place search
- Enriches results with **Google Places API** (photos, ratings, price levels)
- Displays rich place cards with:
  - High-quality photos
  - Star ratings
  - Price indicators ($, $$, $$$, $$$$)
  - Addresses and Google Maps links
- Voice input supported on Collections page (press `S` key)

### 🧠 Context-Aware Intelligence
- Semantic image matching: AI selects relevant images based on query content
- Intent classification: Automatically determines the best UI format
- Profile-based reasoning: Recommendations cite evidence from your location and saved interests
- Conversation awareness: Maintains context across interactions

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **Styling**: CSS Modules with custom design system
- **HTTP Client**: Axios
- **Media**: Web Audio API for voice recording

### Backend
- **Framework**: FastAPI (Python)
- **AI Model**: Google Gemini 1.5 Flash
- **Database**: SQLite with custom storage service
- **APIs**:
  - Google Cloud Speech-to-Text API
  - Google Maps Grounding Lite MCP
  - Google Places API (New)
- **Architecture**: Modular service-based design

### Key Services

**Backend Services:**
- `GeminiService`: LLM interactions and structured output generation
- `MapsService`: Google Maps MCP integration + Places API enrichment
- `SpeechService`: Audio transcription (REST API mode)
- `StorageService`: SQLite database operations
- `UserProfileService`: User profile management
- `ImageMatchingService`: Semantic image selection

**Frontend Services:**
- `agentService`: Agent communication and session management
- `libraryService`: Collections CRUD operations
- `userProfileService`: Profile data fetching
- `recommendService`: Recommendation requests

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  Main Page  │  │  Collections │  │  PlaceCard    │ │
│  │  (Q&A)      │  │  Gallery     │  │  Component    │ │
│  └─────────────┘  └──────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
                    HTTP/REST API
                           │
┌─────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Agent (Intent Classifier)              │   │
│  │  • Analyzes query                                │   │
│  │  • Determines UI module type                     │   │
│  │  • Generates structured response                 │   │
│  └─────────────────────────────────────────────────┘   │
│                           │                              │
│  ┌──────────────┬────────┴────────┬──────────────┐    │
│  │   Gemini     │   Maps MCP      │   Places     │    │
│  │   Service    │   Service       │   API        │    │
│  └──────────────┴─────────────────┴──────────────┘    │
│                                                          │
│  ┌──────────────┬─────────────────┬──────────────┐    │
│  │   Storage    │   User Profile  │   Speech     │    │
│  │   (SQLite)   │   Service       │   Service    │    │
│  └──────────────┴─────────────────┴──────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 16+
- Google Cloud API Key (for Gemini, Speech, Maps)

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   GEMINI_API_KEY=your_google_api_key_here
   ```

5. Run the backend:
   ```bash
   python main.py
   ```

   Backend runs on `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

   Frontend runs on `http://localhost:5173`

## API Configuration

### Required Google Cloud APIs

Enable these APIs in your Google Cloud Console:

1. **Generative Language API** (Gemini)
2. **Cloud Speech-to-Text API**
3. **Maps Grounding Lite API**
4. **Places API (New)**

### API Key Setup

All services use a single consolidated API key (`GEMINI_API_KEY`) in the backend `.env` file. This key must have permissions for:
- Gemini AI
- Speech-to-Text
- Maps Grounding Lite MCP
- Places API

See `GOOGLE_CLOUD_SPEECH_SETUP.md` for detailed configuration.

## User Profile

The system uses a pseudo user profile (`backend/data/user_profile.json`) for personalized recommendations:

```json
{
  "name": "Anna",
  "avatarUrl": "/icons/profile1.jpg",
  "location": {
    "address": "San Francisco, CA, USA",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "city": "San Francisco",
  "region": "CA",
  "country": "US",
  "profession": "Designer"
}
```

Modify this file to customize the user profile.

## UI Schema System

AgenticUI uses a custom UI schema format to define visual layouts. The agent generates JSON schemas that the frontend renderer converts into React components.

**Example Schema Structure:**
```json
{
  "components": [
    {
      "component": {
        "Text": {
          "text": "Artichoke",
          "usageHint": "h1"
        }
      }
    },
    {
      "component": {
        "Image": {
          "url": "/images/artichoke.jpg",
          "usageHint": "hero"
        }
      }
    }
  ]
}
```

The renderer dynamically selects and renders components like `Text`, `Image`, `Label`, `Chip`, `Card`, etc.

## Project Structure

```
AgenticUI/
├── backend/
│   ├── agent.py                 # Intent classifier & UI generator
│   ├── agent_executor.py        # Request handler
│   ├── main.py                  # FastAPI app entry point
│   ├── services/
│   │   ├── gemini_service.py    # Gemini AI integration
│   │   ├── maps_service.py      # Maps MCP + Places API
│   │   ├── speech_service.py    # Speech-to-text
│   │   ├── storage.py           # SQLite operations
│   │   └── user_profile_service.py
│   ├── routes/
│   │   ├── library.py           # Collections endpoints
│   │   ├── user.py              # Profile endpoint
│   │   └── recommend.py         # Recommendations endpoint
│   ├── data/
│   │   └── user_profile.json    # User profile data
│   └── images/                  # Local image library
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── App.tsx          # Main Q&A interface
│   │   │   ├── Sidebar.tsx      # Answer display
│   │   │   ├── CollectionsPage.tsx  # Gallery page
│   │   │   ├── PlaceCard.tsx    # Recommendation card
│   │   │   └── renderer.tsx     # UI schema renderer
│   │   ├── services/            # API clients
│   │   ├── hooks/               # Custom React hooks
│   │   └── utils/               # Helper functions
│   └── public/
│       ├── icons/               # UI icons
│       └── images/              # Image assets
│
├── README.md                    # This file
├── QUICKSTART.md               # Quick setup guide
└── GOOGLE_CLOUD_SPEECH_SETUP.md # API setup instructions
```

## Usage Examples

### Basic Question
1. Type or say: "What is an artichoke?"
2. System displays a detailed module with description, images, and facts

### Recipe Request
1. Ask: "How do I cook asparagus?"
2. System returns a step module with ingredients and sequential instructions

### Saving Answers
1. Click the save icon (💾) in the sidebar
2. Answer is added to your Collections
3. Access via profile icon → Collections page

### Getting Recommendations
1. Navigate to Collections page
2. Hover over the recommendation box at the bottom
3. Press `S` and say: "Recommend Italian restaurants for date night"
4. OR type your request and click "Get recommendations"
5. View place cards with photos, ratings, and details

## Key Interactions

- **Press `S`**: Activate voice input (hold to record)
- **Click Save Icon**: Add current answer to library
- **Click Profile Icon**: Navigate to Collections gallery
- **Hover Cards**: Reveal delete button
- **Click Card**: Reload saved answer
- **Hover Recommendation Box**: Show input controls

## Future Enhancements

Potential areas for expansion:
- Multi-language support
- Real-time collaboration features
- More UI module types (charts, tables, timelines)
- Integration with additional data sources
- Mobile-responsive design
- User authentication and multi-user support
- Export collections to PDF/markdown

## License

This is a prototype/research project. See individual component licenses for details.

## Contact

For questions or contributions, please reach out to the project maintainers.
