import asyncio
import ollama


async def stream_response(messages):
    loop = asyncio.get_event_loop()
    stream = await loop.run_in_executor(
        None,
        lambda: ollama.chat(
            model="qwen2.5:1.5b",
            messages=messages,
            stream=True
        )
    )

    for chunk in stream:
        yield chunk["message"]["content"]
        await asyncio.sleep(0)
