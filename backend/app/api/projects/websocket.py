"""
WebSocket连接管理模块

该模块包含WebSocket连接管理的相关功能。
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        # 项目ID到WebSocket连接集合的映射
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: int):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: int):
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
    
    async def broadcast_to_project(self, project_id: int, message: dict):
        if project_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except WebSocketDisconnect:
                    disconnected.add(connection)
            
            # 移除断开的连接
            for connection in disconnected:
                self.disconnect(connection, project_id)

# 创建连接管理器实例
manager = ConnectionManager() 