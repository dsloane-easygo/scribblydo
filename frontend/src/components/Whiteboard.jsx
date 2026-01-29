import React, { forwardRef, useImperativeHandle, useCallback, useRef, useState } from 'react';
import PostItNote from './PostItNote';
import CursorOverlay from './cursors/CursorOverlay';
import ViewersOverlay from './presence/ViewersOverlay';
import { useNotes } from '../hooks/useNotes';
import { useCursors } from '../hooks/useCursors';
import styles from '../styles/Whiteboard.module.css';

// Colors for new notes
const COLORS = ['#FFEB3B', '#FF7EB9', '#7AFCFF', '#98FB98', '#FFB347', '#DDA0DD'];

/**
 * Whiteboard Component
 * Main container for the note interface
 */
const Whiteboard = forwardRef(function Whiteboard({ whiteboardId, rightSidebarOpen }, ref) {
  const {
    notes,
    loading,
    error,
    fetchNotes,
    createNote,
    updateNote,
    deleteNote,
    updateNotePosition,
    streamNotePosition,
  } = useNotes(whiteboardId);

  const { remoteCursors, updateCursorPosition } = useCursors(whiteboardId);
  const whiteboardRef = useRef(null);
  const [selectedNoteId, setSelectedNoteId] = useState(null);

  // Handle mouse movement for cursor tracking
  const handleMouseMove = useCallback((e) => {
    if (!whiteboardRef.current) return;
    const rect = whiteboardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    updateCursorPosition(x, y);
  }, [updateCursorPosition]);

  const handleAddNote = useCallback(async () => {
    if (!whiteboardId) return;

    // Generate random position
    const maxX = Math.max(100, window.innerWidth - 450);
    const maxY = Math.max(120, window.innerHeight - 230);
    const minX = 50;
    const minY = 50;

    const x_position = Math.floor(Math.random() * (maxX - minX) + minX);
    const y_position = Math.floor(Math.random() * (maxY - minY) + minY);
    const color = COLORS[Math.floor(Math.random() * COLORS.length)];

    try {
      await createNote({
        title: '',
        content: '',
        color,
        x_position,
        y_position,
      });
    } catch (err) {
      console.error('Failed to create note:', err);
    }
  }, [whiteboardId, createNote]);

  // Expose addNote method to parent via ref
  useImperativeHandle(ref, () => ({
    addNote: handleAddNote,
  }), [handleAddNote]);

  const handleUpdateNote = useCallback(async (id, updates) => {
    try {
      await updateNote(id, updates);
    } catch (err) {
      console.error('Failed to update note:', err);
    }
  }, [updateNote]);

  const handleDeleteNote = useCallback(async (id) => {
    try {
      await deleteNote(id);
    } catch (err) {
      console.error('Failed to delete note:', err);
    }
  }, [deleteNote]);

  const handlePositionChange = useCallback(async (id, x, y, streaming = false) => {
    try {
      if (streaming) {
        // Stream position update in real-time (broadcast only, no DB save)
        streamNotePosition(id, x, y);
      } else {
        // Final position update (save to DB)
        await updateNotePosition(id, x, y);
      }
    } catch (err) {
      console.error('Failed to update note position:', err);
    }
  }, [updateNotePosition, streamNotePosition]);

  const handleSelectNote = useCallback((id) => {
    setSelectedNoteId(id);
  }, []);

  const handleWhiteboardClick = useCallback((e) => {
    // Deselect note when clicking on whiteboard background
    if (e.target === whiteboardRef.current || e.target.classList.contains(styles.notesArea)) {
      setSelectedNoteId(null);
    }
  }, []);

  if (!whiteboardId) {
    return (
      <div className={styles.whiteboard}>
        <div className={styles.emptyState}>
          <h2>No board selected</h2>
          <p>Create a board to get started</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={styles.whiteboard}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>Loading notes...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.whiteboard}>
        <div className={styles.error}>
          <h3>Oops! Something went wrong</h3>
          <p>{error}</p>
          <button className={styles.retryButton} onClick={fetchNotes}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={whiteboardRef}
      className={styles.whiteboard}
      onMouseMove={handleMouseMove}
      onClick={handleWhiteboardClick}
    >
      <ViewersOverlay rightSidebarOpen={rightSidebarOpen} />
      <CursorOverlay cursors={remoteCursors} />
      <div className={styles.notesArea}>
        {notes.length === 0 && (
          <div className={styles.emptyState}>
            <h2>No notes yet!</h2>
            <p>Click &quot;New Note&quot; in the sidebar to add your first post-it</p>
          </div>
        )}

        {notes.map((note) => (
          <PostItNote
            key={note.id}
            note={note}
            onUpdate={handleUpdateNote}
            onDelete={handleDeleteNote}
            onPositionChange={handlePositionChange}
            isSelected={selectedNoteId === note.id}
            onSelect={handleSelectNote}
          />
        ))}
      </div>
    </div>
  );
});

export default Whiteboard;
