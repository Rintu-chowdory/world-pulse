import asyncio
import json
import websockets


async def main():
    async with websockets.connect("ws://127.0.0.1:8001/ws/events") as socket:
        message = json.loads(await socket.recv())
        assert message["type"] == "snapshot"
        assert len(message["events"]) >= 1
        print(f"snapshot events={len(message['events'])}")


if __name__ == "__main__":
    asyncio.run(main())
