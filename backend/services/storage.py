import aiosqlite
import json
from datetime import datetime
from typing import List, Optional
from models.database import init_db

class StorageService:
    def __init__(self):
        import os
        # Get the backend directory path
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(backend_dir, "database", "app.db")
    
    async def _get_connection(self):
        """Get database connection"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn
    
    async def save_item(self, question: str, ui_schema: dict, video_time: Optional[float] = None) -> int:
        """Save an item to the database"""
        await init_db()  # Ensure database is initialized
        
        conn = await self._get_connection()
        try:
            ui_schema_json = json.dumps(ui_schema)
            cursor = await conn.execute(
                "INSERT INTO saved_items (question, ui_schema, video_time, timestamp) VALUES (?, ?, ?, ?)",
                (question, ui_schema_json, video_time, datetime.now().isoformat())
            )
            await conn.commit()
            item_id = cursor.lastrowid
            return item_id
        finally:
            await conn.close()
    
    async def get_all_items(self) -> List[dict]:
        """Get all saved items"""
        await init_db()  # Ensure database is initialized
        
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                "SELECT id, question, ui_schema, video_time, timestamp FROM saved_items ORDER BY timestamp DESC"
            )
            rows = await cursor.fetchall()
            items = []
            for row in rows:
                items.append({
                    "id": row["id"],
                    "question": row["question"],
                    "uiSchema": json.loads(row["ui_schema"]),
                    "videoTime": row["video_time"],
                    "timestamp": row["timestamp"]
                })
            return items
        finally:
            await conn.close()
    
    async def delete_item(self, item_id: int) -> None:
        """Delete an item by ID"""
        await init_db()  # Ensure database is initialized
        
        conn = await self._get_connection()
        try:
            await conn.execute("DELETE FROM saved_items WHERE id = ?", (item_id,))
            await conn.commit()
        finally:
            await conn.close()

