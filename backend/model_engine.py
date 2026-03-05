import ollama


async def stream_response(messages):
    stream = ollama.chat(
        model="qwen2.5:1.5b",
        messages=messages,
        stream=True
    )

    for chunk in stream:
        yield chunk["message"]["content"]
