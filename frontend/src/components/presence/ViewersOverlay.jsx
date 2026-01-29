import React from 'react';
import { usePresence } from '../../hooks/usePresence';
import { useAuth } from '../../hooks/useAuth';
import styles from '../../styles/ViewersOverlay.module.css';

/**
 * ViewersOverlay Component
 * Shows viewers as circle avatars in the top-right of the whiteboard
 */
export function ViewersOverlay({ rightSidebarOpen }) {
  const { whiteboardViewers } = usePresence();
  const { user } = useAuth();

  // Filter out current user and limit display
  const otherViewers = whiteboardViewers.filter((v) => v.id !== user?.id);

  if (otherViewers.length === 0) {
    return null;
  }

  // Show max 5 viewers, plus overflow count
  const displayViewers = otherViewers.slice(0, 5);
  const overflowCount = otherViewers.length - 5;

  return (
    <div className={`${styles.overlay} ${rightSidebarOpen ? styles.sidebarOpen : ''}`}>
      <div className={styles.viewersList}>
        {displayViewers.map((viewer, index) => (
          <div
            key={viewer.id}
            className={styles.viewerAvatar}
            style={{ zIndex: displayViewers.length - index }}
            title={viewer.username}
          >
            {viewer.username.charAt(0).toUpperCase()}
          </div>
        ))}
        {overflowCount > 0 && (
          <div className={styles.overflowCount} title={`${overflowCount} more viewers`}>
            +{overflowCount}
          </div>
        )}
      </div>
      <span className={styles.viewingLabel}>viewing</span>
    </div>
  );
}

export default ViewersOverlay;
