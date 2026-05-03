
import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token, get_current_user, get_settings, require_admin
from app.db.session import AsyncSessionLocal, get_db
from app.models.user import User
from app.services import chat_service
from app.services.chat_service import manager

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatMessageResponse(BaseModel):
    id: str
    room_id: str
    sender_id: str
    is_admin: bool
    content: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class ChatRoomResponse(BaseModel):
    id: str
    user_id: str
    user_email: str
    user_name: str
    updated_at: datetime

@router.get("/history", response_model=List[ChatMessageResponse])
async def get_history(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    room = await chat_service.get_or_create_room(db, current_user.id)
    return await chat_service.get_room_messages(db, room.id)

@router.get("/admin/rooms", response_model=List[ChatRoomResponse])
async def get_admin_rooms(
    current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    rooms = await chat_service.get_all_rooms(db)
    return [
        ChatRoomResponse(
            id=r.id,
            user_id=r.user_id,
            user_email=r.user.email if r.user else "",
            user_name=r.user.full_name if r.user else "",
            updated_at=r.updated_at,
        )
        for r in rooms
    ]

@router.get("/admin/rooms/{room_id}/messages", response_model=List[ChatMessageResponse])
async def get_admin_room_messages(
    room_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.get_room_messages(db, room_id)

@router.post("/read")
async def mark_user_read(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    room = await chat_service.get_or_create_room(db, current_user.id)
    await chat_service.mark_messages_read(db, room.id, is_admin=False)
    return {"status": "ok"}

@router.post("/admin/rooms/{room_id}/read")
async def mark_admin_read(
    room_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await chat_service.mark_messages_read(db, room_id, is_admin=True)
    return {"status": "ok"}

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    await websocket.accept()
    settings = get_settings()
    try:
        payload = decode_access_token(token, settings)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=1008)
        return

    async with AsyncSessionLocal() as db:
        from app.repositories.user_repo import UserRepository
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)

    if not user:
        await websocket.close(code=1008)
        return

    is_admin = user.role == "admin"
    await manager.connect(websocket, user.id, is_admin)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            content = payload.get("content")
            room_id = payload.get("room_id")

            if not content:
                continue

            async with AsyncSessionLocal() as db:
                if is_admin:
                    if not room_id:
                        continue
                    target_room_id = room_id
                else:
                    room = await chat_service.get_or_create_room(db, user.id)
                    target_room_id = room.id

                msg = await chat_service.save_message(
                    db, target_room_id, user.id, is_admin, content
                )

            msg_dict = {
                "id": msg.id,
                "room_id": msg.room_id,
                "sender_id": msg.sender_id,
                "is_admin": msg.is_admin,
                "content": msg.content,
                "is_read": msg.is_read,
                "created_at": msg.created_at.isoformat(),
            }

            await manager.send_to_user(msg.room_user_id, msg_dict)
            await manager.broadcast_to_admins(msg_dict)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id, is_admin)