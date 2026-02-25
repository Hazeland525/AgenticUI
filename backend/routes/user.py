from fastapi import APIRouter, HTTPException
from services.user_profile_service import UserProfileService

router = APIRouter()


@router.get("/user-profile")
async def get_user_profile():
    """Return the pseudo user profile (name, location, profession, etc.)."""
    try:
        service = UserProfileService()
        profile = service.get_profile()
        if profile is None:
            raise HTTPException(status_code=404, detail="User profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
