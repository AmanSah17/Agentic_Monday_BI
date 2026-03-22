/**
 * WebSocket Service for real-time graph execution updates
 */

export type WSEventType = 
  | "execution_start" 
  | "node_start" 
  | "node_end" 
  | "node_error" 
  | "data_flow" 
  | "execution_complete" 
  | "execution_error";

export interface WSEvent {
  type: WSEventType;
  session_id?: string;
  node_name?: string;
  timestamp: string;
  data?: any;
  error?: string;
  execution_time_ms?: number;
  from?: string;
  to?: string;
  description?: string;
}

class WebSocketService {
  private socket: WebSocket | null = null;
  private handlers: Set<(event: WSEvent) => void> = new Set();

  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = import.meta.env.VITE_BACKEND_WS_URL || window.location.host;
      const url = `${protocol}//${host}/ws/execute/${sessionId}`;

      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        console.log("WebSocket connected");
        resolve();
      };

      this.socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        reject(error);
      };

      this.socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data) as WSEvent;
          this.handlers.forEach(handler => handler(event));
        } catch (e) {
          console.error("Failed to parse WS message:", e);
        }
      };

      this.socket.onclose = () => {
        console.log("WebSocket disconnected");
        this.socket = null;
      };
    });
  }

  subscribe(handler: (event: WSEvent) => void) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  send(data: any) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.error("WebSocket is not open");
    }
  }

  execute(query: string, history: any[] = []) {
    this.send({
      type: "execute",
      query,
      conversation_history: history
    });
  }

  disconnect() {
    this.socket?.close();
    this.socket = null;
  }
}

export const wsService = new WebSocketService();
