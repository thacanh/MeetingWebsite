import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional


SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]


@dataclass
class _ClientState:
    username: str
    joined_at: datetime
    send: SendCallable


class RoomManager:
    def __init__(self):
        self._rooms: Dict[str, Dict[str, _ClientState]] = {}
        self._lock = asyncio.Lock()

    async def add_client(self, room_id: str, client_id: str, username: str, send: SendCallable) -> None:
        async with self._lock:
            room = self._rooms.setdefault(room_id, {})
            room[client_id] = _ClientState(username=username, joined_at=datetime.utcnow(), send=send)

    async def remove_client(self, room_id: str, client_id: str) -> bool:
        async with self._lock:
            room = self._rooms.get(room_id)
            if not room or client_id not in room:
                return False

            del room[client_id]
            if not room:
                del self._rooms[room_id]
            return True

    async def broadcast(self, room_id: str, message: Dict[str, Any], exclude: Optional[str] = None) -> None:
        async with self._lock:
            room = self._rooms.get(room_id)
            if not room:
                return

            targets = [
                (cid, state.send)
                for cid, state in room.items()
                if cid != exclude
            ]

        stale_clients: List[str] = []
        for cid, send in targets:
            try:
                await send(message)
            except Exception:
                stale_clients.append(cid)

        for cid in stale_clients:
            await self.remove_client(room_id, cid)

    async def get_clients_in_room(self, room_id: str) -> List[str]:
        async with self._lock:
            room = self._rooms.get(room_id)
            if not room:
                return []
            return list(room.keys())

    async def get_room_users(self, room_id: str) -> List[Dict[str, Any]]:
        async with self._lock:
            room = self._rooms.get(room_id)
            if not room:
                return []

            return [
                {
                    'client_id': cid,
                    'username': state.username,
                    'joined_at': state.joined_at.isoformat()
                }
                for cid, state in room.items()
            ]

    async def clear(self) -> None:
        async with self._lock:
            self._rooms.clear()
