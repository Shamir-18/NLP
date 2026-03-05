from fastapi import FastAPI, WebSocket
import uuid
from conversation_manager import handle_message

app = FastAPI()


@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())

    while True:
        data = await websocket.receive_json()
        user_message = data["message"]

        async for token in handle_message(session_id, user_message):
            await websocket.send_text(token)
