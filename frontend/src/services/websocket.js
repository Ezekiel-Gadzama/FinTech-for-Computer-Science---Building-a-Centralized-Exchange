import io from 'socket.io-client';

// Use the nginx proxy URL (port 80)
const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = {};
  }

  connect(token) {
    this.socket = io(WS_URL, {
      path: '/socket.io/' // Important: match nginx configuration
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      if (token) {
        this.socket.emit('authenticate', { token });
      }
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
    }
  }

  subscribe(pair) {
    if (this.socket) {
      this.socket.emit('subscribe', { pair });
    }
  }

  unsubscribe(pair) {
    if (this.socket) {
      this.socket.emit('unsubscribe', { pair });
    }
  }

  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }
}

export default new WebSocketService();