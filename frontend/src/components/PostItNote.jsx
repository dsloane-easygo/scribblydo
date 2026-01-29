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

// Throttle function for real-time updates
function throttle(func, limit) {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * PostItNote Component
 * A draggable, resizable post-it note with editable title and content
 */
function PostItNote({ note, onUpdate, onDelete, onPositionChange, isSelected, onSelect }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [localTitle, setLocalTitle] = useState(note.title);
  const [localContent, setLocalContent] = useState(note.content);
  const [localWidth, setLocalWidth] = useState(note.width || 200);
  const [localHeight, setLocalHeight] = useState(note.height || 180);
  const nodeRef = useRef(null);
  const titleInputRef = useRef(null);
  const updateTimeoutRef = useRef(null);
  const resizeStartRef = useRef(null);

  // Create throttled position update function
  const throttledPositionUpdate = useRef(
    throttle((id, x, y) => {
      onPositionChange(id, x, y, true); // true = streaming (don't save to DB yet)
    }, 50) // Update every 50ms during drag
  ).current;

  // Sync local state with props when note changes externally
  useEffect(() => {
    setLocalTitle(note.title);
    setLocalContent(note.content);
    setLocalWidth(note.width || 200);
    setLocalHeight(note.height || 180);
  }, [note.title, note.content, note.width, note.height]);

  // Focus title input on new notes (intentionally only on mount)
  useEffect(() => {
    if (!note.title && !note.content && titleInputRef.current) {
      titleInputRef.current.focus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    onSelect?.(note.id);
  }, [note.id, onSelect]);

  const handleDrag = useCallback(
    (e, data) => {
      // Stream position updates in real-time
      throttledPositionUpdate(note.id, data.x, data.y);
    },
    [note.id, throttledPositionUpdate]
  );

  const handleDragStop = useCallback(
    (e, data) => {
      setIsDragging(false);
      // Final position update - save to database
      onPositionChange(note.id, data.x, data.y, false); // false = final (save to DB)
    },
    [note.id, onPositionChange]
  );

  const handleNoteClick = useCallback(
    (e) => {
      // Only select if clicking on the note itself, not inputs
      if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'BUTTON') {
        onSelect?.(note.id);
      }
    },
    [note.id, onSelect]
  );

  // Resize handlers
  const handleResizeStart = useCallback(
    (e, corner) => {
      e.preventDefault();
      e.stopPropagation();
      setIsResizing(true);
      onSelect?.(note.id);

      resizeStartRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        startWidth: localWidth,
        startHeight: localHeight,
        corner,
      };

      const handleResizeMove = (moveEvent) => {
        if (!resizeStartRef.current) return;

        const { startX, startY, startWidth, startHeight, corner: resizeCorner } = resizeStartRef.current;
        const deltaX = moveEvent.clientX - startX;
        const deltaY = moveEvent.clientY - startY;

        let newWidth = startWidth;
        let newHeight = startHeight;

        // Calculate new dimensions based on which corner is being dragged
        if (resizeCorner.includes('e')) {
          newWidth = Math.max(100, Math.min(800, startWidth + deltaX));
        }
        if (resizeCorner.includes('w')) {
          newWidth = Math.max(100, Math.min(800, startWidth - deltaX));
        }
        if (resizeCorner.includes('s')) {
          newHeight = Math.max(100, Math.min(800, startHeight + deltaY));
        }
        if (resizeCorner.includes('n')) {
          newHeight = Math.max(100, Math.min(800, startHeight - deltaY));
        }

        setLocalWidth(newWidth);
        setLocalHeight(newHeight);
      };

      const handleResizeEnd = () => {
        setIsResizing(false);
        document.removeEventListener('mousemove', handleResizeMove);
        document.removeEventListener('mouseup', handleResizeEnd);

        // Save final dimensions to database
        if (resizeStartRef.current) {
          onUpdate(note.id, { width: localWidth, height: localHeight });
        }
        resizeStartRef.current = null;
      };

      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
    },
    [note.id, localWidth, localHeight, onUpdate, onSelect]
  );

  // Update dimensions when resize ends
  useEffect(() => {
    if (!isResizing && resizeStartRef.current === null) {
      // Dimensions already saved in handleResizeEnd
    }
  }, [isResizing]);

  return (
    <Draggable
      nodeRef={nodeRef}
      position={{ x: note.x_position || 0, y: note.y_position || 0 }}
      onStart={handleDragStart}
      onDrag={handleDrag}
      onStop={handleDragStop}
      bounds="parent"
      handle={`.${styles.note}`}
      cancel="input, textarea, button, .resize-handle"
    >
      <div
        ref={nodeRef}
        className={`${styles.noteWrapper} ${isDragging ? styles.dragging : ''} ${isSelected ? styles.selected : ''}`}
        onClick={handleNoteClick}
      >
        <div
          className={styles.note}
          style={{
            backgroundColor: note.color,
            width: `${localWidth}px`,
            minHeight: `${localHeight}px`,
          }}
        >
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

          {/* Resize handles - only visible when selected */}
          {isSelected && (
            <>
              <div
                className={`${styles.resizeHandle} ${styles.resizeN} resize-handle`}
                onMouseDown={(e) => handleResizeStart(e, 'n')}
              />
              <div
                className={`${styles.resizeHandle} ${styles.resizeS} resize-handle`}
                onMouseDown={(e) => handleResizeStart(e, 's')}
              />
              <div
                className={`${styles.resizeHandle} ${styles.resizeE} resize-handle`}
                onMouseDown={(e) => handleResizeStart(e, 'e')}
              />
              <div
                className={`${styles.resizeHandle} ${styles.resizeW} resize-handle`}
                onMouseDown={(e) => handleResizeStart(e, 'w')}
              />
              <div
                className={`${styles.resizeHandle} ${styles.resizeNE} resize-handle`}
                onMouseDown={(e) => handleResizeStart(e, 'ne')}
              />
              <div
                className={`${styles.resizeHandle} ${styles.resizeNW} resize-handle`}
                onMouseDown={(e) => handleResizeStart(e, 'nw')}
              />
              <div
                className={`${styles.resizeHandle} ${styles.resizeSE} resize-handle`}
                onMouseDown={(e) => handleResizeStart(e, 'se')}
              />
              <div
                className={`${styles.resizeHandle} ${styles.resizeSW} resize-handle`}
                onMouseDown={(e) => handleResizeStart(e, 'sw')}
              />
            </>
          )}
        </div>
      </div>
    </Draggable>
  );
}

export default React.memo(PostItNote);
