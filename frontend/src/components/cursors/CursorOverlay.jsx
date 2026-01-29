import React from 'react';
import RemoteCursor from './RemoteCursor';
import styles from '../../styles/CursorOverlay.module.css';

/**
 * CursorOverlay Component
 * Renders all remote user cursors on top of the whiteboard
 */
export function CursorOverlay({ cursors }) {
  return (
    <div className={styles.overlay}>
      {Object.entries(cursors).map(([userId, cursor]) => (
        <RemoteCursor
          key={userId}
          username={cursor.username}
          x={cursor.x}
          y={cursor.y}
        />
      ))}
    </div>
  );
}

export default CursorOverlay;
