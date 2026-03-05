import os
import re
import pandas as pd
from model_engine import stream_response
from session_store import get_session

BAKERY_KEYWORDS = [
    "cake", "bread", "pastry", "pastries", "cookie", "cookies", "muffin", "muffins",
    "cupcake", "cupcakes", "pie", "pies", "donut", "donuts", "doughnut",
    "croissant", "baguette", "brownie", "tart", "scone", "roll", "rolls",
    "bakery", "bake", "baking", "order", "menu", "price", "cost", "deliver",
    "pickup", "pick up", "timing", "timings", "hours", "open", "close",
    "location", "address", "phone", "contact", "custom", "flavor", "flavour",
    "chocolate", "vanilla", "strawberry", "red velvet", "cream", "icing",
    "frosting", "layer", "pound", "kilogram", "kg", "slice", "piece",
    "birthday", "wedding", "anniversary", "celebration", "party",
    "hello", "hi", "hey", "thanks", "thank you", "bye", "goodbye",
    "help", "what do you", "what can you", "available", "offer",
    "sweet", "sugar", "gluten", "vegan", "nut", "allergy",
]

REFUSAL = "I'm sorry, I can only help with bakery-related questions. Would you like to order something from our bakery?"


def is_bakery_related(message):
    msg_lower = message.lower()
    return any(keyword in msg_lower for keyword in BAKERY_KEYWORDS)

SYSTEM_PROMPT = """You are a friendly bakery assistant for "Sweet Delights Bakery". Help customers with orders and bakery questions.

BAKERY INFORMATION:
- Hours: Monday to Friday 8:00 AM - 8:00 PM, Saturday 9:00 AM - 6:00 PM, Sunday Closed
- Location: 123 Baker Street
- Phone: (555) 123-4567
- Products: cakes, bread, pastries, cookies, muffins, cupcakes, pies, donuts, and bakery beverages
- Custom orders require 24 hours notice

YOUR TASKS:
1. Answer questions about the bakery: timings, hours, location, menu, products, pricing, delivery, pickup.
2. Help customers place orders by collecting: item, quantity, size/weight, flavor, special requests.
3. Once all details are collected, summarize the order and ask the customer to confirm.
4. When the customer confirms, say the order is placed successfully and ask if they want anything else.
5. Do NOT keep asking for confirmation after the customer already confirmed.
6. Be polite and concise.

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

    # Pre-filter: reject off-topic messages before sending to LLM
    if not is_bakery_related(user_message):
        session["history"].append({"role": "user", "content": user_message})
        session["history"].append({"role": "assistant", "content": REFUSAL})
        yield REFUSAL
        return

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
