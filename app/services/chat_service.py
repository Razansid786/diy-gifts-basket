
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatRoom, ChatMessage
from app.models.user import User

class ConnectionManager:
    def __init__(self):

        self.active_connections: Dict[str, List[WebSocket]] = {}

        self.admin_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: str, is_admin: bool):
        if is_admin:
            self.admin_connections.append(websocket)
        else:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str, is_admin: bool):
        if is_admin:
            if websocket in self.admin_connections:
                self.admin_connections.remove(websocket)
        else:
            if user_id in self.active_connections and websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):

        connections = self.active_connections.get(user_id, [])
        for conn in connections:
            try:
                await conn.send_json(message)
            except Exception:
                pass

    async def broadcast_to_admins(self, message: dict):

        for conn in self.admin_connections:
            try:
                await conn.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

async def get_or_create_room(db: AsyncSession, user_id: str) -> ChatRoom:

    result = await db.execute(select(ChatRoom).where(ChatRoom.user_id == user_id))
    room = result.scalars().first()

    if not room:
        room = ChatRoom(user_id=user_id)
        db.add(room)
        await db.commit()
        await db.refresh(room)

    return room

async def get_room_by_id(db: AsyncSession, room_id: str) -> Optional[ChatRoom]:
    result = await db.execute(
        select(ChatRoom)
        .options(selectinload(ChatRoom.user))
        .where(ChatRoom.id == room_id)
    )
    return result.scalars().first()

async def get_all_rooms(db: AsyncSession) -> List[ChatRoom]:

    result = await db.execute(
        select(ChatRoom)
        .options(selectinload(ChatRoom.user))
        .order_by(ChatRoom.updated_at.desc())
    )
    return list(result.scalars().all())

async def get_room_messages(db: AsyncSession, room_id: str) -> List[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())

from sqlalchemy import text
import uuid

async def save_message(
    db: AsyncSession, room_id: str, sender_id: str, is_admin: bool, content: str
) -> ChatMessage:
    msg_id = str(uuid.uuid4())

    query = text()

    result = await db.execute(query, {
        "id": msg_id,
        "room_id": room_id,
        "sender_id": sender_id,
        "is_admin": is_admin,
        "content": content
    })
    row = result.fetchone()
    await db.commit()

    class MockMessage:
        pass
    msg = MockMessage()
    msg.id = row.id
    msg.room_id = row.room_id
    msg.sender_id = row.sender_id
    msg.is_admin = row.is_admin
    msg.content = row.content
    msg.is_read = row.is_read
    msg.created_at = row.created_at
    msg.room_user_id = row.room_user_id
    return msg

async def mark_messages_read(db: AsyncSession, room_id: str, is_admin: bool):

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.room_id == room_id)
        .where(ChatMessage.is_admin != is_admin)
        .where(ChatMessage.is_read == False)
    )
    messages = result.scalars().all()
    for msg in messages:
        msg.is_read = True
    if messages:
        await db.commit()