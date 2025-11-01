class WebSocketClient {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.clientId = null;
        this.messageHandlers = {};
    }

    connect(host, port) {
        return new Promise((resolve, reject) => {
            try {
                // Auto-detect protocol
                const isSecure = window.location.protocol === 'https:';
                const protocol = isSecure ? 'wss:' : 'ws:';
                
                // Remove port if using ngrok or similar
                const portPart = (host.includes('ngrok') || host.includes('loca.lt') || host.includes('cloudflare')) ? '' : `:${port}`;
                
                const wsUrl = `${protocol}//${host}${portPart}/signaling`;
                console.log(`Connecting to WebSocket: ${wsUrl}`);
                
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.connected = true;
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Error parsing message:', error);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.connected = false;
                };

            } catch (error) {
                console.error('Connection error:', error);
                reject(error);
            }
        });
    }

    handleMessage(message) {
        const type = message.type;
        
        if (type === 'connected') {
            this.clientId = message.client_id;
            console.log(`Client ID: ${this.clientId}`);
        }

        if (this.messageHandlers[type]) {
            this.messageHandlers[type].forEach(handler => {
                try {
                    handler(message);
                } catch (error) {
                    console.error(`Error in handler for ${type}:`, error);
                }
            });
        }
    }

    on(messageType, handler) {
        if (!this.messageHandlers[messageType]) {
            this.messageHandlers[messageType] = [];
        }
        this.messageHandlers[messageType].push(handler);
    }

    send(message) {
        if (this.connected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket not connected');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
    }
}
