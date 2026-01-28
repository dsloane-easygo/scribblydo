import React, { useState, useCallback, useRef, useEffect } from 'react';
import Draggable from 'react-draggable';
import styles from '../styles/PostItNote.module.css';

const COLORS = [
  { name: 'yellow', value: '#FFEB3B' },
  { name: 'pink', value: '#FF7EB9' },
  { name: 'blue', value: '#7AFCFF' },
  { name: 'green', value: '#98FB98' },
  { name: 'orange', value: '#FFB347' },
  { name: 'purple', value: '#DDA0DD' },
];

/**
 * PostItNote Component
 * A draggable post-it note with editable title and content
 */
function PostItNote({ note, onUpdate, onDelete, onPositionChange }) {
  const [isDragging, setIsDragging] = useState(false);
  const [localTitle, setLocalTitle] = useState(note.title);
  const [localContent, setLocalContent] = useState(note.content);
  const nodeRef = useRef(null);
  const titleInputRef = useRef(null);
  const updateTimeoutRef = useRef(null);

  // Sync local state with props when note changes externally
  useEffect(() => {
    setLocalTitle(note.title);
    setLocalContent(note.content);
  }, [note.title, note.content]);

  // Focus title input on new notes
  useEffect(() => {
    if (!note.title && !note.content && titleInputRef.current) {
      titleInputRef.current.focus();
    }
  }, []);

  // Debounced update for text changes
  const debouncedUpdate = useCallback(
    (field, value) => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }

      updateTimeoutRef.current = setTimeout(() => {
        onUpdate(note.id, { [field]: value });
      }, 500);
    },
    [note.id, onUpdate]
  );

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    };
  }, []);

  const handleTitleChange = useCallback(
    (e) => {
      const value = e.target.value;
      setLocalTitle(value);
      debouncedUpdate('title', value);
    },
    [debouncedUpdate]
  );

  const handleContentChange = useCallback(
    (e) => {
      const value = e.target.value;
      setLocalContent(value);
      debouncedUpdate('content', value);
    },
    [debouncedUpdate]
  );

  const handleColorChange = useCallback(
    (color) => {
      onUpdate(note.id, { color });
    },
    [note.id, onUpdate]
  );

  const handleDelete = useCallback(() => {
    if (window.confirm('Delete this note?')) {
      onDelete(note.id);
    }
  }, [note.id, onDelete]);

  const handleDragStart = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleDragStop = useCallback(
    (e, data) => {
      setIsDragging(false);
      onPositionChange(note.id, data.x, data.y);  // react-draggable uses x/y, we convert in handler
    },
    [note.id, onPositionChange]
  );

  return (
    <Draggable
      nodeRef={nodeRef}
      position={{ x: note.x_position || 0, y: note.y_position || 0 }}
      onStart={handleDragStart}
      onStop={handleDragStop}
      bounds="parent"
      handle={`.${styles.note}`}
      cancel="input, textarea, button"
    >
      <div
        ref={nodeRef}
        className={`${styles.noteWrapper} ${isDragging ? styles.dragging : ''}`}
      >
        <div className={styles.note} style={{ backgroundColor: note.color }}>
          <div className={styles.pin} />

          <div className={styles.header}>
            <input
              ref={titleInputRef}
              type="text"
              className={styles.titleInput}
              value={localTitle}
              onChange={handleTitleChange}
              placeholder="Title..."
              aria-label="Note title"
            />
          </div>

          <div className={styles.actions}>
            <button
              className={`${styles.actionButton} ${styles.deleteButton}`}
              onClick={handleDelete}
              aria-label="Delete note"
              title="Delete note"
            >
              x
            </button>
          </div>

          <textarea
            className={styles.contentInput}
            value={localContent}
            onChange={handleContentChange}
            placeholder="Write your note..."
            aria-label="Note content"
          />

          <div className={styles.colorPicker}>
            {COLORS.map((color) => (
              <button
                key={color.name}
                className={`${styles.colorOption} ${
                  note.color === color.value ? styles.active : ''
                }`}
                style={{ backgroundColor: color.value }}
                onClick={() => handleColorChange(color.value)}
                aria-label={`Change color to ${color.name}`}
                title={color.name}
              />
            ))}
          </div>
        </div>
      </div>
    </Draggable>
  );
}

export default React.memo(PostItNote);
