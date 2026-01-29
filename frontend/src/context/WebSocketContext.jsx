import React, { createContext, useState, useEffect, useCallback, useRef, useMemo, useContext } from 'react';
import { AuthContext } from './AuthContext';

export const WebSocketContext = createContext(null);

// Use relative path for WebSocket to work with Vite proxy
const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;
const RECONNECT_DELAY = 3000;
const PING_INTERVAL = 30000;

/**
 * WebSocketProvider Component
 * Manages WebSocket connection for real-time collaboration
 */
export function WebSocketProvider({ children }) {
  const { token, isAuthenticated } = useContext(AuthContext);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const subscribersRef = useRef(new Map());
  const isAuthenticatedRef = useRef(false);

  // Clear reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Clear ping interval
  const clearPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Start ping interval to keep connection alive
  const startPingInterval = useCallback(() => {
    clearPingInterval();
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping', payload: {} }));
      }
    }, PING_INTERVAL);
  }, [clearPingInterval]);

  // Handle incoming messages
  const handleMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);
      const { type, payload } = data;

      if (type === 'auth_success') {
        isAuthenticatedRef.current = true;
        setIsConnected(true);
        setConnectionError(null);
        startPingInterval();
        return;
      }

      if (type === 'error') {
        console.error('WebSocket error:', payload);
        setConnectionError(payload.message || 'Unknown error');
        return;
      }

      // Dispatch to subscribers
      const handlers = subscribersRef.current.get(type) || new Set();
      handlers.forEach((handler) => {
        try {
          handler(payload);
        } catch (err) {
          console.error(`Handler error for ${type}:`, err);
        }
      });
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
    }
  }, [startPingInterval]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!token || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    clearReconnectTimeout();

    try {
      const ws = new WebSocket(WS_BASE);
      wsRef.current = ws;

      ws.onopen = () => {
        // Send auth message
        ws.send(JSON.stringify({
          type: 'auth',
          payload: { token },
        }));
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        setIsConnected(false);
        isAuthenticatedRef.current = false;
        wsRef.current = null;

        // Auto-reconnect if authenticated and not a clean close
        if (isAuthenticated && event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('Connection failed');
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setConnectionError(err.message);
    }
  }, [token, isAuthenticated, handleMessage, clearReconnectTimeout]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    clearPingInterval();
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnect');
      wsRef.current = null;
    }
    setIsConnected(false);
    isAuthenticatedRef.current = false;
  }, [clearReconnectTimeout, clearPingInterval]);

  // Connect when authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, token, connect, disconnect]);

  // Send a message
  const send = useCallback((type, payload = {}) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return false;
    }

    try {
      wsRef.current.send(JSON.stringify({ type, payload }));
      return true;
    } catch (err) {
      console.error('Failed to send WebSocket message:', err);
      return false;
    }
  }, []);

  // Subscribe to a message type
  const subscribe = useCallback((type, handler) => {
    if (!subscribersRef.current.has(type)) {
      subscribersRef.current.set(type, new Set());
    }
    subscribersRef.current.get(type).add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = subscribersRef.current.get(type);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          subscribersRef.current.delete(type);
        }
      }
    };
  }, []);

  // Join a whiteboard room
  const joinWhiteboard = useCallback((whiteboardId) => {
    return send('join_whiteboard', { whiteboard_id: whiteboardId });
  }, [send]);

  // Leave current whiteboard room
  const leaveWhiteboard = useCallback(() => {
    return send('leave_whiteboard', {});
  }, [send]);

  // Send cursor position
  const sendCursorPosition = useCallback((x, y) => {
    return send('cursor_move', { x, y });
  }, [send]);

  // Send ping for keep-alive
  const sendPing = useCallback(() => {
    return send('ping', {});
  }, [send]);

  const value = useMemo(
    () => ({
      isConnected,
      connectionError,
      send,
      subscribe,
      joinWhiteboard,
      leaveWhiteboard,
      sendCursorPosition,
      sendPing,
    }),
    [isConnected, connectionError, send, subscribe, joinWhiteboard, leaveWhiteboard, sendCursorPosition, sendPing]
  );

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export default WebSocketContext;
