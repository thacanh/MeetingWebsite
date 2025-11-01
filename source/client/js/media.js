class MediaClient {
    constructor() {
        this.udpSocket = null;
        this.localStream = null;
        this.localCanvas = null;
        this.localCtx = null;
        this.videoEnabled = true;
        this.audioEnabled = true;
        this.remoteVideos = {};
        this.audioContext = null;
        this.serverHost = null;
        this.serverPort = 8080;
        this.clientId = null;
        this.roomId = null;
        this.streaming = false;
        this.frameCount = 0;
        this.lastFpsUpdate = Date.now();
        this.currentFps = 0;
        this.localVideoElement = null;
        this.renderingStarted = false;
    }

    async initialize(serverHost, clientId, roomId) {
        this.serverHost = serverHost;
        this.clientId = clientId;
        this.roomId = roomId;

        console.log('Initializing media...');

        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 15, max: 30 }
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            console.log('Media devices accessed');
            
            this.setupLocalVideo();
            this.setupAudioContext();
            this.initializeMediaSocket();

            return true;
        } catch (error) {
            console.error('Error accessing media devices:', error);
            alert('Cannot access camera/microphone. Please check permissions.');
            return false;
        }
    }

    setupLocalVideo() {
        console.log('Setting up local video...');
        
        this.localCanvas = document.getElementById('localVideo');
        this.localCtx = this.localCanvas.getContext('2d');

        const video = document.createElement('video');
        video.srcObject = this.localStream;
        video.autoplay = true;
        video.muted = true;
        video.playsInline = true;
        
        this.localVideoElement = video;
        
        this.localCanvas.width = 640;
        this.localCanvas.height = 480;

        video.addEventListener('loadedmetadata', () => {
            console.log('Video metadata loaded');
            if (video.videoWidth > 0 && video.videoHeight > 0) {
                this.localCanvas.width = video.videoWidth;
                this.localCanvas.height = video.videoHeight;
            }
        });

        video.addEventListener('canplay', () => {
            console.log('Video can play');
            this.startVideoRendering();
        });

        video.play().then(() => {
            console.log('Video playing');
            if (video.readyState >= 2) {
                this.startVideoRendering();
            }
        }).catch(error => {
            console.error('Video play failed:', error);
        });
    }

    startVideoRendering() {
        if (this.renderingStarted) return;
        
        this.renderingStarted = true;
        console.log('Starting video render loop');
        
        const video = this.localVideoElement;
        let frameCounter = 0;
        let lastLogTime = Date.now();
        
        const render = () => {
            if (!this.videoEnabled) {
                this.localCtx.fillStyle = '#000';
                this.localCtx.fillRect(0, 0, this.localCanvas.width, this.localCanvas.height);
            } else if (video && video.readyState >= video.HAVE_CURRENT_DATA) {
                try {
                    this.localCtx.drawImage(video, 0, 0, this.localCanvas.width, this.localCanvas.height);
                    
                    frameCounter++;
                    const now = Date.now();
                    if (now - lastLogTime >= 5000) {
                        console.log(`Rendering at ${Math.round(frameCounter / 5)} FPS`);
                        frameCounter = 0;
                        lastLogTime = now;
                    }
                } catch (error) {
                    console.error('Error drawing frame:', error);
                }
            }
            
            requestAnimationFrame(render);
        };
        
        render();
    }

    setupAudioContext() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const audioTrack = this.localStream.getAudioTracks()[0];
        
        if (audioTrack) {
            const source = this.audioContext.createMediaStreamSource(new MediaStream([audioTrack]));
            const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
            
            source.connect(processor);
            processor.connect(this.audioContext.destination);

            processor.onaudioprocess = (e) => {
                if (this.audioEnabled && this.streaming) {
                    const audioData = e.inputBuffer.getChannelData(0);
                    this.sendAudioChunk(audioData);
                }
            };
        }
    }

    initializeMediaSocket() {
        const isSecure = window.location.protocol === 'https:';
        const protocol = isSecure ? 'wss:' : 'ws:';
        const portPart = (this.serverHost.includes('ngrok') || this.serverHost.includes('loca.lt') || this.serverHost.includes('cloudflare')) ? '' : `:${this.serverPort}`;
        
        const wsUrl = `${protocol}//${this.serverHost}${portPart}/media`;
        console.log(`Connecting to media server: ${wsUrl}`);
        
        this.udpSocket = new WebSocket(wsUrl);
        this.udpSocket.binaryType = 'arraybuffer';

        this.udpSocket.onopen = () => {
            console.log('Media channel connected');
        };

        this.udpSocket.onmessage = (event) => {
            this.handleMediaPacket(event.data);
        };

        this.udpSocket.onerror = (error) => {
            console.error('Media channel error:', error);
        };

        this.udpSocket.onclose = () => {
            console.log('Media channel disconnected');
        };
    }

    startStreaming() {
        this.streaming = true;
        
        this.videoStreamInterval = setInterval(() => {
            if (this.videoEnabled && this.localCanvas) {
                this.sendVideoFrame();
                
                this.frameCount++;
                const now = Date.now();
                if (now - this.lastFpsUpdate >= 1000) {
                    this.currentFps = this.frameCount;
                    this.frameCount = 0;
                    this.lastFpsUpdate = now;
                    this.updateFpsDisplay();
                }
            }
        }, 66);

        console.log('Streaming started');
    }

    stopStreaming() {
        this.streaming = false;
        
        if (this.videoStreamInterval) {
            clearInterval(this.videoStreamInterval);
        }

        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
        }

        if (this.udpSocket) {
            this.udpSocket.close();
        }

        console.log('Streaming stopped');
    }

    sendVideoFrame() {
        try {
            this.localCanvas.toBlob((blob) => {
                if (blob && this.udpSocket && this.udpSocket.readyState === WebSocket.OPEN) {
                    const reader = new FileReader();
                    reader.onload = () => {
                        const payload = reader.result;
                        const packet = this.encodePacket(1, payload);
                        this.udpSocket.send(packet);
                    };
                    reader.readAsArrayBuffer(blob);
                }
            }, 'image/jpeg', 0.6);
        } catch (error) {
            console.error('Error sending video frame:', error);
        }
    }

    sendAudioChunk(audioData) {
        try {
            if (this.udpSocket && this.udpSocket.readyState === WebSocket.OPEN) {
                const buffer = new Float32Array(audioData).buffer;
                const packet = this.encodePacket(2, buffer);
                this.udpSocket.send(packet);
            }
        } catch (error) {
            console.error('Error sending audio chunk:', error);
        }
    }

    encodePacket(type, payload) {
        const clientIdBytes = new TextEncoder().encode(this.clientId);
        const roomIdBytes = new TextEncoder().encode(this.roomId);
        
        const headerSize = 1 + 1 + clientIdBytes.length + 1 + roomIdBytes.length;
        const packet = new ArrayBuffer(headerSize + payload.byteLength);
        const view = new DataView(packet);
        const uint8View = new Uint8Array(packet);
        
        let offset = 0;
        
        view.setUint8(offset, type);
        offset += 1;
        
        view.setUint8(offset, clientIdBytes.length);
        offset += 1;
        uint8View.set(clientIdBytes, offset);
        offset += clientIdBytes.length;
        
        view.setUint8(offset, roomIdBytes.length);
        offset += 1;
        uint8View.set(roomIdBytes, offset);
        offset += roomIdBytes.length;
        
        uint8View.set(new Uint8Array(payload), offset);
        
        return packet;
    }

    handleMediaPacket(data) {
        try {
            const view = new DataView(data);
            let offset = 0;
            
            const type = view.getUint8(offset);
            offset += 1;
            
            const senderIdLen = view.getUint8(offset);
            offset += 1;
            
            const senderIdBytes = new Uint8Array(data, offset, senderIdLen);
            const senderId = new TextDecoder().decode(senderIdBytes);
            offset += senderIdLen;
            
            const payload = data.slice(offset);
            
            if (type === 1) {
                this.displayRemoteVideo(senderId, payload);
            } else if (type === 2) {
                this.playRemoteAudio(senderId, payload);
            }
        } catch (error) {
            console.error('Error handling media packet:', error);
        }
    }

    addRemoteVideo(clientId, username) {
        if (this.remoteVideos[clientId]) return;

        const videoGrid = document.getElementById('videoGrid');
        
        const container = document.createElement('div');
        container.className = 'video-container';
        container.id = `video-${clientId}`;

        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;

        const label = document.createElement('div');
        label.className = 'video-label';
        label.innerHTML = `
            <span class="username">${username}</span>
            <span class="indicators">
                <span class="indicator video-on">V</span>
                <span class="indicator audio-on">A</span>
            </span>
        `;

        container.appendChild(canvas);
        container.appendChild(label);
        videoGrid.appendChild(container);

        this.remoteVideos[clientId] = {
            canvas: canvas,
            ctx: canvas.getContext('2d'),
            username: username
        };

        console.log(`Added remote video for ${username}`);
    }

    displayRemoteVideo(clientId, payload) {
        if (!this.remoteVideos[clientId]) return;

        const blob = new Blob([payload], { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);
        
        const img = new Image();
        img.onload = () => {
            const { canvas, ctx } = this.remoteVideos[clientId];
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            URL.revokeObjectURL(url);
        };
        img.src = url;
    }

    playRemoteAudio(clientId, payload) {
        if (!this.audioContext) return;

        try {
            const audioData = new Float32Array(payload);
            const audioBuffer = this.audioContext.createBuffer(1, audioData.length, this.audioContext.sampleRate);
            
            const channelData = audioBuffer.getChannelData(0);
            channelData.set(audioData);

            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start();
        } catch (error) {
            console.error('Error playing remote audio:', error);
        }
    }

    removeRemoteVideo(clientId) {
        const container = document.getElementById(`video-${clientId}`);
        if (container) {
            container.remove();
        }
        delete this.remoteVideos[clientId];
    }

    toggleVideo() {
        this.videoEnabled = !this.videoEnabled;
        
        const overlay = document.getElementById('localOverlay');
        const indicator = document.getElementById('localVideoIndicator');
        const btn = document.getElementById('toggleVideo');
        
        if (this.videoEnabled) {
            overlay.style.display = 'none';
            indicator.classList.remove('video-off');
            indicator.classList.add('video-on');
            btn.textContent = 'Camera OFF';
            btn.classList.remove('off');
        } else {
            overlay.style.display = 'flex';
            indicator.classList.remove('video-on');
            indicator.classList.add('video-off');
            btn.textContent = 'Camera ON';
            btn.classList.add('off');
            
            if (this.localCtx) {
                this.localCtx.fillStyle = '#000';
                this.localCtx.fillRect(0, 0, this.localCanvas.width, this.localCanvas.height);
            }
        }
        
        return this.videoEnabled;
    }

    toggleAudio() {
        this.audioEnabled = !this.audioEnabled;
        
        const indicator = document.getElementById('localAudioIndicator');
        const btn = document.getElementById('toggleAudio');
        
        if (this.audioEnabled) {
            indicator.classList.remove('audio-off');
            indicator.classList.add('audio-on');
            btn.textContent = 'Mic OFF';
            btn.classList.remove('off');
        } else {
            indicator.classList.remove('audio-on');
            indicator.classList.add('audio-off');
            btn.textContent = 'Mic ON';
            btn.classList.add('off');
        }
        
        return this.audioEnabled;
    }

    updateFpsDisplay() {
        const fpsCounter = document.getElementById('fpsCounter');
        if (fpsCounter) {
            fpsCounter.textContent = this.currentFps;
        }
    }
}
