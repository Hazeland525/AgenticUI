# Quick Start Guide

## Running Your AgenticUI Project

### Step 1: Start the Backend (Terminal 1)

```bash
cd backend

# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Make sure .env has your API key
# GEMINI_API_KEY=your_actual_api_key_here

# Run the backend
python main.py
```

Backend will run on: **http://localhost:8000**

### Step 2: Start the Frontend (Terminal 2)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Run the frontend
npm run dev
```

Frontend will run on: **http://localhost:5173**

### Step 3: Use the Application

1. Open **http://localhost:5173** in your browser
2. Click "Select Video" to upload a video file
3. Ask questions in the sidebar (e.g., "What product is shown?", "Who is the actor?")
4. View the AI-generated UI components in the sidebar
5. Save interesting responses to the library

## Troubleshooting

- **Backend won't start**: Make sure `.env` has `GEMINI_API_KEY` set
- **Frontend can't connect**: Make sure backend is running on port 8000
- **No search results**: Check that both servers are running and API key is valid





