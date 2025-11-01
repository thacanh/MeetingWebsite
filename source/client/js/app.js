let wsClient = null;
let mediaClient = null;
let chatClient = null;

let currentRoom = null;
let currentUsername = null;
let currentClientId = null;
let serverHost = null;

window.addEventListener('DOMContentLoaded', () => {
    console.log('Application loaded');
    
    wsClient = new WebSocketClient();
    mediaClient = new MediaClient();
    chatClient = new ChatClient();
    
    chatClient.initialize();
    setupWebSocketHandlers();
    
    // Expose for debugging
    window.wsClient = wsClient;
    window.mediaClient = mediaClient;
    window.chatClient = chatClient;
});

function setupWebSocketHandlers() {
    wsClient.on('connected', (data) => {
        currentClientId = data.client_id;
        console.log(`Connected with client ID: ${currentClientId}`);
    });

    wsClient.on('room_users', (data) => {
        console.log('Users in room:', data.users);
        updateUserCount(data.users.length + 1);
        
        data.users.forEach(user => {
            if (user.client_id !== currentClientId) {
                mediaClient.addRemoteVideo(user.client_id, user.username);
            }
        });
    });

    wsClient.on('user_joined', (data) => {
        console.log(`${data.username} joined`);
        updateStatus(`${data.username} joined`);
        
        mediaClient.addRemoteVideo(data.client_id, data.username);
        updateUserCount(Object.keys(mediaClient.remoteVideos).length + 1);
        
        chatClient.addMessage('system', 'System', `${data.username} joined the room`, new Date().toISOString(), false);
    });

    wsClient.on('user_left', (data) => {
        console.log(`User left: ${data.client_id}`);
        updateStatus('A user left');
        
        mediaClient.removeRemoteVideo(data.client_id);
        updateUserCount(Object.keys(mediaClient.remoteVideos).length + 1);
        
        if (data.username) {
            chatClient.addMessage('system', 'System', `${data.username} left the room`, new Date().toISOString(), false);
        }
    });

    wsClient.on('chat', (data) => {
        chatClient.addMessage(data.client_id, data.username, data.text, data.timestamp, data.client_id === currentClientId);
    });
}

async function joinRoom() {
    try {
        currentUsername = document.getElementById('username').value.trim() || 'User';
        currentRoom = document.getElementById('roomId').value.trim() || 'room1';
        serverHost = document.getElementById('serverHost').value.trim() || 'localhost';

        if (!currentUsername || !currentRoom) {
            alert('Please enter name and room code');
            return;
        }

        updateStatus('Connecting...');

        const serverPort = 8080;

        await wsClient.connect(serverHost, serverPort);
        
        await new Promise(resolve => setTimeout(resolve, 500));
        
        if (!currentClientId) {
            throw new Error('Client ID not received');
        }

        const mediaInitialized = await mediaClient.initialize(serverHost, currentClientId, currentRoom);
        mediaClient.serverPort = serverPort;

        if (!mediaInitialized) {
            throw new Error('Cannot initialize media');
        }

        wsClient.send({
            type: 'join',
            room: currentRoom,
            username: currentUsername
        });

        mediaClient.startStreaming();

        document.getElementById('joinSection').style.display = 'none';
        document.getElementById('mainContent').style.display = 'block';
        
        updateStatus(`Joined room: ${currentRoom}`);
        updateStatusBar('connected');

        console.log('Successfully joined room');

    } catch (error) {
        console.error('Error joining room:', error);
        alert(`Cannot join room: ${error.message}`);
        updateStatus('Connection error');
        updateStatusBar('error');
    }
}

function leaveRoom() {
    if (!currentRoom) return;

    wsClient.send({
        type: 'leave',
        room: currentRoom
    });

    mediaClient.stopStreaming();
    wsClient.disconnect();

    Object.keys(mediaClient.remoteVideos).forEach(clientId => {
        mediaClient.removeRemoteVideo(clientId);
    });

    chatClient.clear();

    currentRoom = null;
    currentUsername = null;
    currentClientId = null;

    document.getElementById('joinSection').style.display = 'block';
    document.getElementById('mainContent').style.display = 'none';
    document.getElementById('chatPanel').style.display = 'none';
    
    updateStatus('Left room');
    updateStatusBar('disconnected');

    console.log('Left room');
}

function toggleVideo() {
    const enabled = mediaClient.toggleVideo();
    console.log(`Video ${enabled ? 'enabled' : 'disabled'}`);
}

function toggleAudio() {
    const enabled = mediaClient.toggleAudio();
    console.log(`Audio ${enabled ? 'enabled' : 'disabled'}`);
}

function toggleChat() {
    const visible = chatClient.toggleVisibility();
    console.log(`Chat ${visible ? 'shown' : 'hidden'}`);
}

function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();

    if (!text || !currentRoom) return;

    wsClient.send({
        type: 'chat',
        room: currentRoom,
        text: text
    });

    input.value = '';
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function updateStatus(message) {
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = message;
    }
}

function updateStatusBar(status) {
    const statusBar = document.getElementById('statusBar');
    if (statusBar) {
        statusBar.className = `status-bar ${status}`;
    }
}

function updateUserCount(count) {
    const userCount = document.getElementById('userCount');
    if (userCount) {
        userCount.textContent = count;
    }
}

window.addEventListener('beforeunload', () => {
    if (currentRoom) {
        leaveRoom();
    }
});
