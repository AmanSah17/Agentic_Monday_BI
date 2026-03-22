/**
 * WebSocket Hook for Real-time Graph Execution
 * Handles connection lifecycle and message streaming
 */

import { useEffect, useRef, useCallback, useState } from 'react';

export interface NodeStartEvent {
  type: 'node_start';
  node_name: string;
  timestamp: string;
  data: {
    event_type: string;
    node_name: string;
    timestamp: string;
    status: string;
    input_data?: Record<string, any>;
    metadata?: Record<string, any>;
  };
}

export interface NodeEndEvent {
  type: 'node_end';
  node_name: string;
  execution_time_ms: number;
  timestamp: string;
  data: {
    event_type: string;
    node_name: string;
    timestamp: string;
    status: string;
    output_data?: Record<string, any>;
    execution_time_ms?: number;
  };
}

export interface NodeErrorEvent {
  type: 'node_error';
  node_name: string;
  error: string;
  timestamp: string;
}

export interface DataFlowEvent {
  type: 'data_flow';
  from: string;
  to: string;
  timestamp: string;
  description?: string;
}

export interface TraceEvent {
  type: string;
  node_name?: string;
  error?: string;
  timestamp: string;
  [key: string]: any;
}

export interface UseWebSocketOptions {
  sessionId: string;
  onNodeStart?: (event: NodeStartEvent) => void;
  onNodeEnd?: (event: NodeEndEvent) => void;
  onNodeError?: (event: NodeErrorEvent) => void;
  onDataFlow?: (event: DataFlowEvent) => void;
  onMessage?: (event: TraceEvent) => void;
  onError?: (error: Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoConnect?: boolean;
}

export interface UseWebSocketReturn {
  connected: boolean;
  error: Error | null;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: Record<string, any>) => void;
  executeQuery: (query: string, context?: Record<string, any>) => void;
  getTrace: () => void;
  cancel: () => void;
}

/**
 * Hook for managing WebSocket connection to graph execution backend
 */
export function useWebSocket({
  sessionId,
  onNodeStart,
  onNodeEnd,
  onNodeError,
  onDataFlow,
  onMessage,
  onError,
  onConnect,
  onDisconnect,
  autoConnect = true,
}: UseWebSocketOptions): UseWebSocketReturn {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as TraceEvent;

        // Dispatch to specific handlers based on message type
        if (data.type === 'node_start' && onNodeStart) {
          onNodeStart(data as NodeStartEvent);
        } else if (data.type === 'node_end' && onNodeEnd) {
          onNodeEnd(data as NodeEndEvent);
        } else if (data.type === 'node_error' && onNodeError) {
          onNodeError(data as NodeErrorEvent);
        } else if (data.type === 'data_flow' && onDataFlow) {
          onDataFlow(data as DataFlowEvent);
        }

        // Generic handler
        if (onMessage) {
          onMessage(data);
        }
      } catch (err) {
        console.error('Failed to parse message:', err);
      }
    },
    [onNodeStart, onNodeEnd, onNodeError, onDataFlow, onMessage]
  );

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/execute/${sessionId}`;

      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setError(null);
        if (onConnect) {
          onConnect();
        }
      };

      socket.onmessage = handleMessage;

      socket.onerror = (event) => {
        const err = new Error(`WebSocket error`);
        setError(err);
        if (onError) {
          onError(err);
        }
      };

      socket.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        if (onDisconnect) {
          onDisconnect();
        }
      };

      socketRef.current = socket;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      if (onError) {
        onError(error);
      }
    }
  }, [sessionId, handleMessage, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const sendMessage = useCallback(
    (message: Record<string, any>) => {
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.send(JSON.stringify(message));
      } else {
        console.warn('WebSocket not connected');
      }
    },
    []
  );

  const executeQuery = useCallback(
    (query: string, context?: Record<string, any>) => {
      sendMessage({
        type: 'execute',
        query,
        context: context || {},
      });
    },
    [sendMessage]
  );

  const getTrace = useCallback(() => {
    sendMessage({
      type: 'get_trace',
    });
  }, [sendMessage]);

  const cancel = useCallback(() => {
    sendMessage({
      type: 'cancel',
    });
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    connected,
    error,
    connect,
    disconnect,
    sendMessage,
    executeQuery,
    getTrace,
    cancel,
  };
}
