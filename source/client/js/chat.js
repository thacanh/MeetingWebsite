class ChatClient {
    constructor() {
        this.messages = [];
        this.chatVisible = false;
    }

    initialize() {
        console.log('Chat initialized');
    }

    addMessage(clientId, username, text, timestamp, isOwn = false) {
        const message = { clientId, username, text, timestamp, isOwn };
        this.messages.push(message);
        this.renderMessage(message);

        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    renderMessage(message) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${message.isOwn ? 'own' : ''}`;

        const time = new Date(message.timestamp).toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageDiv.innerHTML = `
            ${!message.isOwn ? `<div class="message-header">${this.escapeHtml(message.username)}</div>` : ''}
            <div class="message-content">${this.escapeHtml(message.text)}</div>
            <div class="message-time">${time}</div>
        `;

        chatMessages.appendChild(messageDiv);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    toggleVisibility() {
        this.chatVisible = !this.chatVisible;
        const chatPanel = document.getElementById('chatPanel');
        
        if (chatPanel) {
            chatPanel.style.display = this.chatVisible ? 'flex' : 'none';
        }

        if (this.chatVisible) {
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.focus();
            }
        }

        return this.chatVisible;
    }

    clear() {
        this.messages = [];
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
    }
}
