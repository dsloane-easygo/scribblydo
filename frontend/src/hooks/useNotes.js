import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE = '/api';

/**
 * Custom hook for managing notes state and API integration
 * Provides CRUD operations with optimistic updates and error handling
 */
export function useNotes(whiteboardId) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  // Fetch notes for the current whiteboard
  const fetchNotes = useCallback(async () => {
    if (!whiteboardId) {
      setNotes([]);
      setLoading(false);
      return;
    }

    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE}/notes?whiteboard_id=${whiteboardId}`,
        {
          signal: abortControllerRef.current.signal,
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch notes: ${response.statusText}`);
      }

      const data = await response.json();
      // API returns { notes: [...], total: N }
      setNotes(data.notes || []);
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Error fetching notes:', err);
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [whiteboardId]);

  // Fetch when whiteboard changes
  useEffect(() => {
    fetchNotes();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchNotes]);

  // Create a new note
  const createNote = useCallback(async (noteData) => {
    if (!whiteboardId) {
      throw new Error('No whiteboard selected');
    }

    const tempId = `temp-${Date.now()}`;
    const newNote = {
      id: tempId,
      whiteboard_id: whiteboardId,
      title: noteData.title || '',
      content: noteData.content || '',
      color: noteData.color || '#FFEB3B',
      x_position: noteData.x_position ?? 100,
      y_position: noteData.y_position ?? 100,
    };

    // Optimistic update
    setNotes((prev) => [...prev, newNote]);

    try {
      const response = await fetch(`${API_BASE}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          whiteboard_id: whiteboardId,
          title: newNote.title,
          content: newNote.content,
          color: newNote.color,
          x_position: newNote.x_position,
          y_position: newNote.y_position,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create note: ${response.statusText}`);
      }

      const createdNote = await response.json();

      // Replace temp note with server response
      setNotes((prev) =>
        prev.map((note) => (note.id === tempId ? createdNote : note))
      );

      return createdNote;
    } catch (err) {
      console.error('Error creating note:', err);
      // Rollback optimistic update
      setNotes((prev) => prev.filter((note) => note.id !== tempId));
      throw err;
    }
  }, [whiteboardId]);

  // Update an existing note
  const updateNote = useCallback(async (id, updates) => {
    // Store previous state for rollback
    let previousNote = null;

    // Optimistic update
    setNotes((prev) =>
      prev.map((note) => {
        if (note.id === id) {
          previousNote = note;
          return { ...note, ...updates };
        }
        return note;
      })
    );

    try {
      const response = await fetch(`${API_BASE}/notes/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update note: ${response.statusText}`);
      }

      const updatedNote = await response.json();

      // Sync with server response
      setNotes((prev) =>
        prev.map((note) => (note.id === id ? updatedNote : note))
      );

      return updatedNote;
    } catch (err) {
      console.error('Error updating note:', err);
      // Rollback optimistic update
      if (previousNote) {
        setNotes((prev) =>
          prev.map((note) => (note.id === id ? previousNote : note))
        );
      }
      throw err;
    }
  }, []);

  // Delete a note
  const deleteNote = useCallback(async (id) => {
    // Store previous state for rollback
    let deletedNote = null;
    let deletedIndex = -1;

    // Optimistic update
    setNotes((prev) => {
      deletedIndex = prev.findIndex((note) => note.id === id);
      if (deletedIndex !== -1) {
        deletedNote = prev[deletedIndex];
      }
      return prev.filter((note) => note.id !== id);
    });

    try {
      const response = await fetch(`${API_BASE}/notes/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete note: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error deleting note:', err);
      // Rollback optimistic update
      if (deletedNote) {
        setNotes((prev) => {
          const newNotes = [...prev];
          newNotes.splice(deletedIndex, 0, deletedNote);
          return newNotes;
        });
      }
      throw err;
    }
  }, []);

  // Debounced position update for drag operations
  const updateNotePosition = useCallback(
    async (id, x_position, y_position) => {
      // Local update only - no optimistic state since drag already shows position
      try {
        await updateNote(id, { x_position, y_position });
      } catch (err) {
        // Position will be corrected on next fetch
        console.error('Error updating note position:', err);
      }
    },
    [updateNote]
  );

  return {
    notes,
    loading,
    error,
    fetchNotes,
    createNote,
    updateNote,
    deleteNote,
    updateNotePosition,
  };
}

export default useNotes;
