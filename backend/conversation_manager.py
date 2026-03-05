import os
import pandas as pd
from model_engine import stream_response
from session_store import get_session

SYSTEM_PROMPT = """You are a professional bakery order assistant.

Rules:
- Only discuss bakery products.
- Collect complete order details.
- Be polite and concise.
- Refuse unrelated questions.
- Always confirm order before finalizing.

Current Order State:
{order_state}

Conversation History:
{history}"""


def trim_history(history, max_messages=8, keep_last=6):
    if len(history) > max_messages:
        return history[-keep_last:]
    return history


def update_order_state(order_state, key, value):
    order_state[key] = value


def build_messages(session):
    history = trim_history(session["history"])
    order_state = session["order_state"]

    history_text = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}" for msg in history
    )
    order_state_text = str(order_state) if order_state else "No order yet."

    system_message = SYSTEM_PROMPT.format(
        order_state=order_state_text,
        history=history_text
    )

    messages = [{"role": "system", "content": system_message}]
    messages.extend(history)
    return messages


async def handle_message(session_id, user_message):
    session = get_session(session_id)

    session["history"].append({
        "role": "user",
        "content": user_message
    })

    messages = build_messages(session)

    full_response = ""
    async for chunk in stream_response(messages):
        full_response += chunk
        yield chunk

    session["history"].append({
        "role": "assistant",
        "content": full_response
    })

    if "confirm" in user_message.lower() or "yes" in user_message.lower():
        export_order(session["order_state"])


def export_order(order_state):
    if not order_state:
        return
    filepath = "orders.xlsx"
    df = pd.DataFrame([order_state])
    if os.path.exists(filepath):
        existing = pd.read_excel(filepath)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(filepath, index=False)
