import React, { useCallback } from 'react';
import styles from '../styles/AddNoteButton.module.css';

/**
 * AddNoteButton Component
 * Button to create new post-it notes at random positions
 */
function AddNoteButton({ onAdd, disabled }) {
  const handleClick = useCallback(() => {
    // Generate random position within visible area
    // Accounting for header (80px) and note size (200x180)
    const maxX = Math.max(100, window.innerWidth - 250);
    const maxY = Math.max(120, window.innerHeight - 230);
    const minX = 50;
    const minY = 100;

    const x_position = Math.floor(Math.random() * (maxX - minX) + minX);
    const y_position = Math.floor(Math.random() * (maxY - minY) + minY);

    // Cycle through colors for variety (hex codes matching backend)
    const colors = ['#FFEB3B', '#FF7EB9', '#7AFCFF', '#98FB98', '#FFB347', '#DDA0DD'];
    const color = colors[Math.floor(Math.random() * colors.length)];

    onAdd({
      title: '',
      content: '',
      color,
      x_position,
      y_position,
    });
  }, [onAdd]);

  return (
    <button
      className={styles.button}
      onClick={handleClick}
      disabled={disabled}
      aria-label="Add new note"
    >
      <span className={styles.icon}>+</span>
      <span className={styles.buttonText}>New Note</span>
    </button>
  );
}

export default React.memo(AddNoteButton);
