import aiosqlite
import os

async def init_db():
    """Initialize the SQLite database"""
    # Get the backend directory path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(backend_dir, "database", "app.db")
    db_dir = os.path.dirname(db_path)
    
    # Create directory if it doesn't exist
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = await aiosqlite.connect(db_path)
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                ui_schema TEXT NOT NULL,
                video_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.commit()
    finally:
        await conn.close()

