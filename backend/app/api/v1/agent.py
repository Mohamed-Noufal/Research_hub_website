"""
Agent API endpoints
Provides chat interface, conversation management, and WebSocket support
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
from app.services.agent_service import AgentService
from app.core.database import get_db
import logging
import json

router = APIRouter(prefix="/agent")
logger = logging.getLogger(__name__)

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str
    user_id: str
    project_id: Optional[int] = None

class CreateConversationRequest(BaseModel):
    user_id: str
    title: Optional[str] = "New Conversation"
    project_id: Optional[int] = None

class ChatResponse(BaseModel):
    conversation_id: str
    role: str
    content: str
    steps: Optional[int] = 0
    status: str

# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    conversation_id: Optional[str] = Body(None),
    service: AgentService = Depends(AgentService.get_instance)
):
    """
    Send a message to the AI agent
    """
    # Create conversation if not provided
    if not conversation_id:
        conversation_id = await service.create_conversation(
            user_id=request.user_id, 
            project_id=request.project_id
        )
    
    # Process message
    # For REST, we collect all yielded items and return the final answer
    # Ideally, use WebSocket for streaming
    final_response = None
    
    async for update in service.process_message(
        user_id=request.user_id,
        conversation_id=conversation_id,
        message=request.message,
        project_id=request.project_id
    ):
        if update['type'] == 'message' and update.get('role') == 'assistant':
            final_response = update

    if not final_response:
        raise HTTPException(status_code=500, detail="Agent failed to generate response")

    return {
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": final_response['content'],
        "status": "completed" # simplified for REST
    }

@router.post("/conversations", response_model=Dict)
async def create_conversation(
    request: CreateConversationRequest,
    service: AgentService = Depends(AgentService.get_instance)
):
    """Create a new conversation"""
    conv_id = await service.create_conversation(
        user_id=request.user_id,
        title=request.title,
        project_id=request.project_id
    )
    return {"id": conv_id, "status": "created"}

@router.get("/conversations/{conversation_id}/history")
async def get_history(
    conversation_id: str,
    limit: int = 50,
    service: AgentService = Depends(AgentService.get_instance)
):
    """Get conversation history"""
    return await service.get_conversation_history(conversation_id, limit)

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    conversation_id: str,
    user_id: str, # passed as query param ?user_id=...
    service: AgentService = Depends(AgentService.get_instance)
):
    """
    WebSocket endpoint for real-time chat with streaming steps
    """
    await websocket.accept()
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_text = message_data.get('message')
            project_id = message_data.get('project_id')
            scope = message_data.get('scope', 'project')
            selected_paper_ids = message_data.get('selected_paper_ids', [])
            
            if not message_text:
                continue
                
            # Stream response
            async for update in service.process_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message_text,
                project_id=project_id,
                scope=scope,
                selected_paper_ids=selected_paper_ids
            ):
                await websocket.send_json(update)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
