# server.py
import asyncio
import websockets

async def handler(websocket):
    async for message in websocket:
        await websocket.send(f"Echo: {message}")

async def main():
    async with websockets.serve(handler, "localhost", 8000):
        await asyncio.Future()  # 永久运行

asyncio.run(main())