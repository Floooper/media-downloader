import { useEffect, useRef, useState, useCallback } from 'react';

type WebSocketData = unknown;
type WebSocketMessage = { type: string; data: WebSocketData };

interface WebSocketOptions<T = WebSocketData> {
  onMessage?: (data: T) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket<T = WebSocketData>(
  url: string,
  {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
  }: WebSocketOptions<T> = {}
) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    wsRef.current = new WebSocket(url);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      setError(null);
      reconnectAttempts.current = 0;
      onOpen?.();
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      onClose?.();

      if (reconnect && reconnectAttempts.current < maxReconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current += 1;
          connect();
        }, reconnectInterval);
      }
    };

    wsRef.current.onerror = (err) => {
      setError(err);
      onError?.(err);
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as T;
        onMessage?.(data);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };
  }, [url, onMessage, onOpen, onClose, onError, reconnect, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttempts.current = 0;
  }, []);

  const send = useCallback(
    (data: WebSocketData) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(data));
      } else {
        console.warn('WebSocket is not connected');
      }
    },
    []
  );

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    send,
    connect,
    disconnect,
  };
}

interface WebSocketSubscriptionOptions<T> extends WebSocketOptions<T> {
  subscriptionKey: string;
}

export function useWebSocketSubscription<T>(
  url: string,
  options: WebSocketSubscriptionOptions<T>
) {
  const [data, setData] = useState<T | null>(null);

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      if (message.type === options.subscriptionKey) {
        const typedData = message.data as T;
        setData(typedData);
        options.onMessage?.(typedData);
      }
    },
    [options]
  );

  const ws = useWebSocket<WebSocketMessage>(url, {
    ...options,
    onMessage: handleMessage,
  });

  const subscribe = useCallback(() => {
    ws.send({
      type: 'subscribe',
      key: options.subscriptionKey,
    });
  }, [ws, options.subscriptionKey]);

  const unsubscribe = useCallback(() => {
    ws.send({
      type: 'unsubscribe',
      key: options.subscriptionKey,
    });
  }, [ws, options.subscriptionKey]);

  useEffect(() => {
    if (ws.isConnected) {
      subscribe();
      return () => unsubscribe();
    }
  }, [ws.isConnected, subscribe, unsubscribe]);

  return {
    data,
    ...ws,
    subscribe,
    unsubscribe,
  };
}
