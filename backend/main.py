from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent_executor import router as agent_router
from routes import library, user, recommend, tts
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="AgenticUI Backend API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router, prefix="/api", tags=["agent"])
app.include_router(library.router, prefix="/api", tags=["library"])
app.include_router(user.router, prefix="/api", tags=["user"])
app.include_router(recommend.router, prefix="/api", tags=["recommend"])
app.include_router(tts.router, prefix="/api", tags=["tts"])

@app.get("/")
async def root():
    return {"message": "AgenticUI Backend API"}

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("Error: uvicorn is not installed. Please run: pip install -r requirements.txt")
        exit(1)

