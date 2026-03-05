import os
import pandas as pd
from model_engine import stream_response
from session_store import get_session

SYSTEM_PROMPT = """You are a bakery order assistant for "Sweet Delights Bakery". Your ONLY job is to help customers place bakery orders.

STRICT RULES YOU MUST ALWAYS FOLLOW:
1. You can ONLY talk about bakery products: cakes, bread, pastries, cookies, muffins, cupcakes, pies, donuts, and bakery beverages.
2. If a customer asks ANYTHING outside bakery topics (e.g. general knowledge, math, science, geography, coding, weather, politics, sports, or any non-bakery subject), you MUST respond ONLY with: "I'm sorry, I can only help with bakery orders. Would you like to order something from our bakery?"
3. NEVER answer general knowledge questions. NEVER. Even if the user insists.
4. Collect order details: item, quantity, size/weight, flavor, and any special requests.
5. Always confirm the full order before finalizing.
6. Be polite and concise.

EXAMPLES OF QUESTIONS YOU MUST REFUSE:
- "What is the capital of France?" → REFUSE
- "Tell me a joke" → REFUSE
- "What is 2+2?" → REFUSE
- "Who is the president?" → REFUSE

For ALL such questions, reply: "I'm sorry, I can only help with bakery orders. Would you like to order something from our bakery?"

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
