import React from 'react';
import styles from '../../styles/CursorOverlay.module.css';

// Generate a consistent color from username
function getUserColor(username) {
  let hash = 0;
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash % 360);
  return `hsl(${hue}, 70%, 50%)`;
}

/**
 * RemoteCursor Component
 * Displays another user's cursor position with their username
 */
export function RemoteCursor({ username, x, y }) {
  const color = getUserColor(username);

  return (
    <div
      className={styles.cursor}
      style={{
        left: x,
        top: y,
        '--cursor-color': color,
      }}
    >
      <svg
        className={styles.cursorIcon}
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill={color}
        stroke="white"
        strokeWidth="1.5"
      >
        <path d="M5.5 3.21V20.8c0 .45.54.67.85.35l4.86-4.86a.5.5 0 0 1 .35-.15h6.87c.48 0 .73-.58.39-.92L5.85 2.85a.5.5 0 0 0-.35.36z" />
      </svg>
      <span className={styles.cursorLabel} style={{ backgroundColor: color }}>
        {username}
      </span>
    </div>
  );
}

export default RemoteCursor;
