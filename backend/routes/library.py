from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.storage import StorageService

router = APIRouter()

class SaveRequest(BaseModel):
    question: str
    uiSchema: dict
    videoTime: Optional[float] = None

class SavedItem(BaseModel):
    id: int
    question: str
    uiSchema: dict
    videoTime: Optional[float]
    timestamp: str

@router.post("/save")
async def save_item(request: SaveRequest):
    try:
        storage = StorageService()
        item_id = await storage.save_item(
            question=request.question,
            ui_schema=request.uiSchema,
            video_time=request.videoTime
        )
        return {"id": item_id, "message": "Item saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/library", response_model=List[SavedItem])
async def get_library():
    try:
        storage = StorageService()
        items = await storage.get_all_items()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/library/{item_id}")
async def delete_item(item_id: int):
    try:
        storage = StorageService()
        await storage.delete_item(item_id)
        return {"message": "Item deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

