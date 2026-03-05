import asyncio
import json
import websockets


async def test_message(msg):
    async with websockets.connect("ws://localhost:8000/ws/chat") as ws:
        await ws.send(json.dumps({"message": msg}))
        response = ""
        while True:
            data = await asyncio.wait_for(ws.recv(), timeout=30)
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict) and parsed.get("type") == "end":
                    break
            except json.JSONDecodeError:
                response += data
        return response


async def main():
    tests = [
        ("What is the capital of France?", "SHOULD REFUSE"),
        ("Tell me a joke", "SHOULD REFUSE"),
        ("bakery timings on saturday", "SHOULD ANSWER"),
        ("I want to order a chocolate cake", "SHOULD ANSWER"),
    ]
    for msg, expected in tests:
        resp = await test_message(msg)
        print(f"\nUser: {msg}")
        print(f"Expected: {expected}")
        print(f"Bot: {resp}")


asyncio.run(main())
