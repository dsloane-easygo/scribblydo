import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE = '/api';

/**
 * Custom hook for managing whiteboards state and API integration
 */
export function useWhiteboards() {
  const [whiteboards, setWhiteboards] = useState([]);
  const [selectedWhiteboardId, setSelectedWhiteboardId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

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
  }, [selectedWhiteboardId]);

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
  const createWhiteboard = useCallback(async (name) => {
    try {
      const response = await fetch(`${API_BASE}/whiteboards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
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
  }, []);

  // Update a whiteboard
  const updateWhiteboard = useCallback(async (id, updates) => {
    try {
      const response = await fetch(`${API_BASE}/whiteboards/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
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
  }, []);

  // Delete a whiteboard
  const deleteWhiteboard = useCallback(async (id) => {
    try {
      const response = await fetch(`${API_BASE}/whiteboards/${id}`, {
        method: 'DELETE',
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
  }, [selectedWhiteboardId]);

  const selectedWhiteboard = whiteboards.find(
    (wb) => wb.id === selectedWhiteboardId
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
  };
}

export default useWhiteboards;
