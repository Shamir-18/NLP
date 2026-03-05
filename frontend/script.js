const chatMessages = document.getElementById("chat-messages");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const resetBtn = document.getElementById("reset-btn");

let ws = null;
let currentAssistantBubble = null;

function connectWebSocket() {
    ws = new WebSocket("ws://localhost:8000/ws/chat");

    ws.onopen = () => {
        addMessage("assistant", "Welcome! How can I help you with your bakery order today?");
    };

    ws.onmessage = (event) => {
        if (!currentAssistantBubble) {
            currentAssistantBubble = addMessage("assistant", "");
        }
        currentAssistantBubble.textContent += event.data;
        scrollToBottom();
    };

    ws.onclose = () => {
        addMessage("assistant", "Connection closed. Please reset to reconnect.");
    };
}

function addMessage(role, content) {
    const bubble = document.createElement("div");
    bubble.classList.add("message", role);
    bubble.textContent = content;
    chatMessages.appendChild(bubble);
    scrollToBottom();
    return bubble;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !ws || ws.readyState !== WebSocket.OPEN) return;

    addMessage("user", message);
    currentAssistantBubble = null;

    ws.send(JSON.stringify({ message: message }));
    messageInput.value = "";
}

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});

resetBtn.addEventListener("click", () => {
    if (ws) ws.close();
    chatMessages.innerHTML = "";
    currentAssistantBubble = null;
    connectWebSocket();
});

connectWebSocket();
