from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Tạo bản copy của list để duyệt an toàn, tránh lỗi khi có client ngắt kết nối đột ngột
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Lỗi khi gửi WS: {e}")
                self.disconnect(connection)

# Khởi tạo một biến toàn cục dùng chung cho toàn bộ App
ws_manager = ConnectionManager()