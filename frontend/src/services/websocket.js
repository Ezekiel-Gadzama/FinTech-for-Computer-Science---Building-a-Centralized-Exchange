import io from "socket.io-client";

const WS_URL = process.env.REACT_APP_WS_URL || "http://localhost:5000";

class WebSocketService {
  constructor() {
    this.socket = null;
  }

  connect(token) {
    if (this.socket) {
      this.socket.disconnect();
    }

    this.socket = io(WS_URL, {
      transports: ["websocket"],
      path: "/socket.io/",
      withCredentials: true,
      autoConnect: true
    });

    this.socket.on("connect", () => {
      console.log("Connected:", this.socket.id);
      if (token) {
        this.socket.emit("authenticate", { token });
      }
    });
  }

  on(event, callback) {
    if (!this.socket) return;
    this.socket.on(event, callback);
  }

  off(event, callback) {
    if (!this.socket) return;
    this.socket.off(event, callback);
  }

  subscribe(pair) {
    if (!this.socket) return;
    this.socket.emit("subscribe", { pair });
  }

  unsubscribe(pair) {
    if (!this.socket) return;
    this.socket.emit("unsubscribe", { pair });
  }
}

export default new WebSocketService();
