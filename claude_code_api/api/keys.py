"""API key management endpoints."""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

from ..core.auth import extract_api_key, validate_api_key
from ..core.key_manager import create_key_manager_from_config
import structlog

logger = structlog.get_logger()
router = APIRouter()


async def get_api_key_dependency(request: Request) -> str:
    """Dependency to extract and validate API key."""
    api_key = extract_api_key(request)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide it via Authorization header (Bearer token) or x-api-key header."
        )
    
    if not validate_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return api_key


@router.get("/keys/status")
async def get_keys_status(request: Request) -> Dict[str, Any]:
    """Get the status of API key rotation."""
    api_key = await get_api_key_dependency(request)
    
    try:
        key_manager = create_key_manager_from_config()
        if not key_manager:
            return {
                "enabled": False,
                "message": "Key rotation not configured"
            }
        
        status = key_manager.get_status()
        status["enabled"] = True
        return status
        
    except Exception as e:
        logger.error("Error getting key status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/keys/rotate")
async def rotate_key(request: Request) -> Dict[str, Any]:
    """Manually rotate to the next API key."""
    api_key = await get_api_key_dependency(request)
    
    try:
        key_manager = create_key_manager_from_config()
        if not key_manager:
            raise HTTPException(
                status_code=400, 
                detail="Key rotation not configured"
            )
        
        if key_manager.rotate_key():
            # Apply the new key
            key_manager.apply_current_key()
            return {
                "success": True,
                "message": "Key rotated successfully",
                "status": key_manager.get_status()
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail="No available keys for rotation"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error rotating key", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")