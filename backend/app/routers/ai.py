from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.database import get_db
from app.services.ai_service import ai_service

router = APIRouter()

class ChatMessage(BaseModel):
    role: str # 'user' or 'model'
    parts: List[str] # Simplified for our API

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = None # Gemini history format

# More standard chat format
class MessagePart(BaseModel):
    text: str

class ContentPart(BaseModel):
    role: str
    parts: List[MessagePart]

class ChatInput(BaseModel):
    message: str
    history: Optional[List[ContentPart]] = None

@router.post("/chat")
async def chat_endpoint(
    payload: ChatInput,
    db: AsyncSession = Depends(get_db)
):
    """
    AI Chatbot bilan muloqot qilish.
    """
    try:
        # Convert history to Gemini format if provided
        history = []
        if payload.history:
            for h in payload.history:
                history.append({
                    "role": h.role,
                    "parts": [p.text for p in h.parts]
                })
        
        ai_result = await ai_service.chat(payload.message, db, history)
        
        return {
            "success": True,
            "response": ai_result["text"],
            "listings": ai_result.get("listings", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
