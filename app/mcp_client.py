import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """
    Titan-Lite MCP 客户端
    负责管理与金融数据 MCP 服务端的连接与通信
    """
    def __init__(self, server_script_path=None):
        if server_script_path is None:
            # 默认指向项目内的金融 MCP 服务端
            base_path = os.path.dirname(os.path.abspath(__file__))
            server_script_path = os.path.join(base_path, "mcp_server_financial.py")
        
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script_path],
            env=os.environ.copy()
        )
        self.session = None
        self._exit_stack = None

    async def connect(self):
        """建立 stdio 连接并初始化 Session"""
        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        
        # 启动服务端进程并建立管道
        read, write = await self._exit_stack.enter_async_context(stdio_client(self.server_params))
        self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        
        # 初始化协议握手
        await self.session.initialize()
        print(">>> [MCP Client] 已成功连接至金融数据服务端")

    async def call_tool(self, tool_name, arguments=None):
        """调用 MCP 服务端定义的工具"""
        if not self.session:
            await self.connect()
        
        try:
            result = await self.session.call_tool(tool_name, arguments or {})
            # 假设返回的是文本内容
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return None
        except Exception as e:
            print(f">>> [MCP Client] 调用工具 {tool_name} 失败: {e}")
            return None

    async def disconnect(self):
        """关闭连接"""
        if self._exit_stack:
            await self._exit_stack.aclose()
            print(">>> [MCP Client] 连接已断开")

# 单例辅助
_client_instance = None

async def get_mcp_client():
    global _client_instance
    if _client_instance is None:
        _client_instance = MCPClient()
        await _client_instance.connect()
    return _client_instance
