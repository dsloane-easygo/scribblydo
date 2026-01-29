import { useState, useEffect, useCallback, useRef, useContext } from 'react';
import { useAuth } from './useAuth';
import { WebSocketContext } from '../context/WebSocketContext';

const API_BASE = '/api';

/**
 * Custom hook for managing whiteboards state and API integration
 */
export function useWhiteboards() {
  const { getAuthHeaders, user } = useAuth();
  const ws = useContext(WebSocketContext);
  const [whiteboards, setWhiteboards] = useState([]);
  const [selectedWhiteboardId, setSelectedWhiteboardId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  // Subscribe to real-time whiteboard events
  useEffect(() => {
    if (!ws) return;

    const handleWhiteboardCreated = (payload) => {
      // Don't add if it was by current user (already added locally)
      if (user && payload.by_user?.id === user.id) return;

      const whiteboard = payload.whiteboard;
      setWhiteboards((prev) => {
        // Check if already exists
        if (prev.some((wb) => wb.id === whiteboard.id)) return prev;
        return [whiteboard, ...prev];
      });
    };

    const handleWhiteboardUpdated = (payload) => {
      // Don't update if it was by current user (already updated locally)
      if (user && payload.by_user?.id === user.id) return;

      const whiteboard = payload.whiteboard;
      setWhiteboards((prev) =>
        prev.map((wb) => (wb.id === whiteboard.id ? { ...wb, ...whiteboard } : wb))
      );
    };

    const handleWhiteboardDeleted = (payload) => {
      // Don't delete if it was by current user (already deleted locally)
      if (user && payload.by_user?.id === user.id) return;

      const whiteboardId = payload.whiteboard?.id;
      if (whiteboardId) {
        setWhiteboards((prev) => {
          const newList = prev.filter((wb) => wb.id !== whiteboardId);
          // If we were viewing the deleted whiteboard, select another
          if (selectedWhiteboardId === whiteboardId && newList.length > 0) {
            setSelectedWhiteboardId(newList[0].id);
          } else if (newList.length === 0) {
            setSelectedWhiteboardId(null);
          }
          return newList;
        });
      }
    };

    const unsubscribeCreated = ws.subscribe('whiteboard_created', handleWhiteboardCreated);
    const unsubscribeUpdated = ws.subscribe('whiteboard_updated', handleWhiteboardUpdated);
    const unsubscribeDeleted = ws.subscribe('whiteboard_deleted', handleWhiteboardDeleted);

    return () => {
      unsubscribeCreated();
      unsubscribeUpdated();
      unsubscribeDeleted();
    };
  }, [ws, user, selectedWhiteboardId]);

  // Fetch all whiteboards
  const fetchWhiteboards = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE}/whiteboards`, {
        signal: abortControllerRef.current.signal,
        headers: {
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch whiteboards: ${response.statusText}`);
      }

      const data = await response.json();
      const wbs = data.whiteboards || [];
      setWhiteboards(wbs);

      // Auto-select first whiteboard if none selected
      if (wbs.length > 0 && !selectedWhiteboardId) {
        setSelectedWhiteboardId(wbs[0].id);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Error fetching whiteboards:', err);
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [selectedWhiteboardId, getAuthHeaders]);

  // Initial fetch
  useEffect(() => {
    fetchWhiteboards();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Create a new whiteboard
  const createWhiteboard = useCallback(async (name, accessType = 'public', sharedWith = []) => {
    try {
      const response = await fetch(`${API_BASE}/whiteboards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ name, access_type: accessType, shared_with: sharedWith }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create whiteboard: ${response.statusText}`);
      }

      const createdWhiteboard = await response.json();
      setWhiteboards((prev) => [createdWhiteboard, ...prev]);
      setSelectedWhiteboardId(createdWhiteboard.id);
      return createdWhiteboard;
    } catch (err) {
      console.error('Error creating whiteboard:', err);
      throw err;
    }
  }, [getAuthHeaders]);

  // Update a whiteboard
  const updateWhiteboard = useCallback(async (id, updates) => {
    try {
      const response = await fetch(`${API_BASE}/whiteboards/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update whiteboard: ${response.statusText}`);
      }

      const updatedWhiteboard = await response.json();
      setWhiteboards((prev) =>
        prev.map((wb) => (wb.id === id ? updatedWhiteboard : wb))
      );
      return updatedWhiteboard;
    } catch (err) {
      console.error('Error updating whiteboard:', err);
      throw err;
    }
  }, [getAuthHeaders]);

  // Delete a whiteboard
  const deleteWhiteboard = useCallback(async (id) => {
    try {
      const response = await fetch(`${API_BASE}/whiteboards/${id}`, {
        method: 'DELETE',
        headers: {
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete whiteboard: ${response.statusText}`);
      }

      setWhiteboards((prev) => {
        const newList = prev.filter((wb) => wb.id !== id);
        // If we deleted the selected whiteboard, select another
        if (selectedWhiteboardId === id && newList.length > 0) {
          setSelectedWhiteboardId(newList[0].id);
        } else if (newList.length === 0) {
          setSelectedWhiteboardId(null);
        }
        return newList;
      });
    } catch (err) {
      console.error('Error deleting whiteboard:', err);
      throw err;
    }
  }, [selectedWhiteboardId, getAuthHeaders]);

  const selectedWhiteboard = whiteboards.find(
    (wb) => wb.id === selectedWhiteboardId
  );

  // Check if current user owns a whiteboard
  const isOwner = useCallback(
    (whiteboard) => {
      if (!user || !whiteboard) return false;
      return whiteboard.owner_id === user.id;
    },
    [user]
  );

  return {
    whiteboards,
    selectedWhiteboardId,
    selectedWhiteboard,
    setSelectedWhiteboardId,
    loading,
    error,
    fetchWhiteboards,
    createWhiteboard,
    updateWhiteboard,
    deleteWhiteboard,
    isOwner,
    currentUserId: user?.id,
  };
}

export default useWhiteboards;
