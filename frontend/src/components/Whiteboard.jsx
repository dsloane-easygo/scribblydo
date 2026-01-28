import React, { forwardRef, useImperativeHandle, useCallback } from 'react';
import PostItNote from './PostItNote';
import { useNotes } from '../hooks/useNotes';
import styles from '../styles/Whiteboard.module.css';

// Colors for new notes
const COLORS = ['#FFEB3B', '#FF7EB9', '#7AFCFF', '#98FB98', '#FFB347', '#DDA0DD'];

/**
 * Whiteboard Component
 * Main container for the note interface
 */
const Whiteboard = forwardRef(function Whiteboard({ whiteboardId }, ref) {
  const {
    notes,
    loading,
    error,
    fetchNotes,
    createNote,
    updateNote,
    deleteNote,
    updateNotePosition,
  } = useNotes(whiteboardId);

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

  const handlePositionChange = useCallback(async (id, x, y) => {
    try {
      await updateNotePosition(id, x, y);
    } catch (err) {
      console.error('Failed to update note position:', err);
    }
  }, [updateNotePosition]);

  if (!whiteboardId) {
    return (
      <div className={styles.whiteboard}>
        <div className={styles.emptyState}>
          <h2>No whiteboard selected</h2>
          <p>Create a whiteboard to get started</p>
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
    <div className={styles.whiteboard}>
      <div className={styles.notesArea}>
        {notes.length === 0 && (
          <div className={styles.emptyState}>
            <h2>No notes yet!</h2>
            <p>Click "New Note" in the sidebar to add your first post-it</p>
          </div>
        )}

        {notes.map((note) => (
          <PostItNote
            key={note.id}
            note={note}
            onUpdate={handleUpdateNote}
            onDelete={handleDeleteNote}
            onPositionChange={handlePositionChange}
          />
        ))}
      </div>
    </div>
  );
});

export default Whiteboard;
