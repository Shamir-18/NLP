import os
import pandas as pd
from model_engine import stream_response
from session_store import get_session

SYSTEM_PROMPT = """You are a bakery order assistant for "Sweet Delights Bakery". Your job is to help customers with bakery orders and bakery-related inquiries.

BAKERY INFORMATION:
- Hours: Monday to Friday 8:00 AM - 8:00 PM, Saturday 9:00 AM - 6:00 PM, Sunday Closed
- Location: 123 Baker Street
- Phone: (555) 123-4567
- Products: cakes, bread, pastries, cookies, muffins, cupcakes, pies, donuts, and bakery beverages
- Custom orders require 24 hours notice

STRICT RULES YOU MUST ALWAYS FOLLOW:
1. You can talk about bakery products, bakery timings/hours, bakery location, bakery menu, pricing, delivery, and anything related to the bakery business.
2. If a customer asks ANYTHING completely outside bakery topics (e.g. general knowledge, math, science, geography, coding, weather, politics, sports, or any non-bakery subject), you MUST respond ONLY with: "I'm sorry, I can only help with bakery-related questions. Would you like to order something from our bakery?"
3. NEVER answer general knowledge questions. NEVER. Even if the user insists.
4. Collect order details: item, quantity, size/weight, flavor, and any special requests.
5. Once you have all details, summarize the order and ask the customer to confirm.
6. When the customer confirms (says yes, confirm, proceed, etc.), respond with: "Your order has been placed successfully! Thank you for choosing Sweet Delights Bakery. Is there anything else you'd like to order?"
7. Do NOT keep asking for confirmation after the customer already said yes. Once confirmed, the order is DONE.
8. Be polite and concise.

ORDER FLOW:
- Greet → Collect details → Summarize order → Ask to confirm → Customer says yes → Order placed → Ask if they want anything else
- NEVER repeat the confirmation question after the customer already confirmed.

EXAMPLES OF QUESTIONS YOU MUST REFUSE:
- "What is the capital of France?" → REFUSE
- "Tell me a joke" → REFUSE
- "What is 2+2?" → REFUSE
- "Who is the president?" → REFUSE

For ALL such questions, reply: "I'm sorry, I can only help with bakery-related questions. Would you like to order something from our bakery?"

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


def is_confirmation(user_message, history):
    """Check if user is confirming a pending order."""
    confirm_words = ["yes", "yess", "yeah", "yep", "sure", "confirm", "proceed", "place the order", "go ahead", "ok", "okay", "do it"]
    msg_lower = user_message.lower().strip()
    if any(word in msg_lower for word in confirm_words):
        if len(history) >= 2:
            last_assistant = history[-1].get("content", "").lower() if history[-1].get("role") == "assistant" else ""
            if any(phrase in last_assistant for phrase in ["confirm", "proceed", "would you like", "shall i", "ready to"]):
                return True
    return False


async def handle_message(session_id, user_message):
    session = get_session(session_id)

    confirming = is_confirmation(user_message, session["history"])

    session["history"].append({
        "role": "user",
        "content": user_message
    })

    messages = build_messages(session)

    if confirming:
        messages.append({
            "role": "system",
            "content": "The customer has confirmed the order. Respond by saying the order has been placed successfully. Thank them. Ask if they want anything else. Do NOT ask for confirmation again."
        })

    full_response = ""
    async for chunk in stream_response(messages):
        full_response += chunk
        yield chunk

    session["history"].append({
        "role": "assistant",
        "content": full_response
    })

    if confirming:
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
