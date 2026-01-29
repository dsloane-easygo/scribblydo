import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { useAuth } from './useAuth';

const CURSOR_THROTTLE_MS = 16; // ~60fps

/**
 * Custom hook for cursor tracking on whiteboards
 * @param {string} whiteboardId - Current whiteboard ID
 * @returns {Object} Cursor state and handlers
 */
export function useCursors(whiteboardId) {
  const { subscribe, sendCursorPosition, joinWhiteboard, leaveWhiteboard, isConnected } = useWebSocket();
  const { user } = useAuth();
  const [remoteCursors, setRemoteCursors] = useState({});
  const lastSendRef = useRef(0);

  // Join whiteboard room when component mounts/whiteboard changes
  useEffect(() => {
    if (!whiteboardId || !isConnected) return;

    joinWhiteboard(whiteboardId);

    return () => {
      leaveWhiteboard();
    };
  }, [whiteboardId, isConnected, joinWhiteboard, leaveWhiteboard]);

  // Subscribe to cursor updates
  useEffect(() => {
    if (!whiteboardId) return;

    const unsubscribeCursor = subscribe('cursor_update', (payload) => {
      const { user_id, username, x, y } = payload;

      // Don't track our own cursor
      if (user && user_id === user.id) return;

      setRemoteCursors((prev) => ({
        ...prev,
        [user_id]: { username, x, y, lastUpdate: Date.now() },
      }));
    });

    const unsubscribeJoined = subscribe('whiteboard_joined', (payload) => {
      // Initialize cursors from viewers list when joining
      const cursors = {};
      payload.viewers.forEach((viewer) => {
        if (user && viewer.id !== user.id) {
          cursors[viewer.id] = {
            username: viewer.username,
            x: viewer.cursor_x,
            y: viewer.cursor_y,
            lastUpdate: Date.now(),
          };
        }
      });
      setRemoteCursors(cursors);
    });

    const unsubscribeUserJoined = subscribe('user_joined', (payload) => {
      const { user: joinedUser } = payload;
      if (user && joinedUser.id !== user.id) {
        setRemoteCursors((prev) => ({
          ...prev,
          [joinedUser.id]: {
            username: joinedUser.username,
            x: 0,
            y: 0,
            lastUpdate: Date.now(),
          },
        }));
      }
    });

    const unsubscribeUserLeft = subscribe('user_left', (payload) => {
      const { user_id } = payload;
      setRemoteCursors((prev) => {
        const next = { ...prev };
        delete next[user_id];
        return next;
      });
    });

    return () => {
      unsubscribeCursor();
      unsubscribeJoined();
      unsubscribeUserJoined();
      unsubscribeUserLeft();
      setRemoteCursors({});
    };
  }, [whiteboardId, subscribe, user]);

  // Remove stale cursors (inactive for more than 10 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setRemoteCursors((prev) => {
        const next = {};
        Object.entries(prev).forEach(([id, cursor]) => {
          if (now - cursor.lastUpdate < 10000) {
            next[id] = cursor;
          }
        });
        return next;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Throttled cursor position sender
  const updateCursorPosition = useCallback((x, y) => {
    const now = Date.now();
    if (now - lastSendRef.current >= CURSOR_THROTTLE_MS) {
      sendCursorPosition(x, y);
      lastSendRef.current = now;
    }
  }, [sendCursorPosition]);

  return {
    remoteCursors,
    updateCursorPosition,
  };
}

export default useCursors;
