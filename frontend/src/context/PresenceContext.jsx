import React, { createContext, useState, useEffect, useMemo, useContext } from 'react';
import { WebSocketContext } from './WebSocketContext';

export const PresenceContext = createContext(null);

/**
 * PresenceProvider Component
 * Tracks online users and whiteboard viewers
 */
export function PresenceProvider({ children }) {
  const ws = useContext(WebSocketContext);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [whiteboardViewers, setWhiteboardViewers] = useState([]);

  // Subscribe to presence updates
  useEffect(() => {
    if (!ws) return;

    const unsubscribePresence = ws.subscribe('presence_update', (payload) => {
      setOnlineUsers(payload.online_users || []);
    });

    const unsubscribeJoined = ws.subscribe('whiteboard_joined', (payload) => {
      setWhiteboardViewers(payload.viewers || []);
    });

    const unsubscribeUserJoined = ws.subscribe('user_joined', (payload) => {
      setWhiteboardViewers(payload.viewers || []);
    });

    const unsubscribeUserLeft = ws.subscribe('user_left', (payload) => {
      setWhiteboardViewers(payload.viewers || []);
    });

    const unsubscribeLeft = ws.subscribe('whiteboard_left', () => {
      setWhiteboardViewers([]);
    });

    return () => {
      unsubscribePresence();
      unsubscribeJoined();
      unsubscribeUserJoined();
      unsubscribeUserLeft();
      unsubscribeLeft();
    };
  }, [ws]);

  const value = useMemo(
    () => ({
      onlineUsers,
      whiteboardViewers,
    }),
    [onlineUsers, whiteboardViewers]
  );

  return (
    <PresenceContext.Provider value={value}>
      {children}
    </PresenceContext.Provider>
  );
}

export default PresenceContext;
