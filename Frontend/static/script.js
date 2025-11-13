// File: Frontend/static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const textInput = document.getElementById('text-input');
    const micButton = document.getElementById('mic-button');
    const statusBar = document.getElementById('status-bar');

    let lastMessageCount = 0;

    // Function to add a message to the chat window
    const addMessage = (sender, text) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'You' ? 'user-message' : 'sara-message');
        messageDiv.textContent = text;
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to the bottom
    };

    // Function to send a text query
    const sendQuery = async () => {
        const query = textInput.value.trim();
        if (query) {
            textInput.value = '';
            // No need to add the message here, the poller will get it from the backend
            await fetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query }),
            });
        }
    };

    // Function to request voice input
    const startVoiceInput = async () => {
        statusBar.textContent = 'Status: Listening...';
        micButton.disabled = true; // Disable button while listening
        await fetch('/start_voice', { method: 'POST' });
    };

    // Poll the backend for updates (new messages, status changes)
    const pollForUpdates = async () => {
        try {
            const response = await fetch('/updates');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            // Update status and re-enable mic button if not listening
            statusBar.textContent = `Status: ${data.status}`;
            if (data.status !== 'Listening...') {
                micButton.disabled = false;
            }

            // Update chat messages if there are new ones
            if (data.chat_history.length !== lastMessageCount) {
                chatWindow.innerHTML = ''; // Clear and redraw chat
                data.chat_history.forEach(msg => {
                    const sender = msg.role === 'user' ? 'You' : 'S.A.R.A.';
                    addMessage(sender, msg.content);
                });
                lastMessageCount = data.chat_history.length;
            }
        } catch (error) {
            console.error('Polling error:', error);
            statusBar.textContent = 'Status: Connection error';
            micButton.disabled = false;
        }
    };

    // Event Listeners
    textInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            sendQuery();
        }
    });

    micButton.addEventListener('click', startVoiceInput);
    
    // Start polling every 2 seconds
    setInterval(pollForUpdates, 2000);
    // Initial poll to load history
    pollForUpdates();
});