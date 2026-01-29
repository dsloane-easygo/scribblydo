import React from 'react';
import { usePresence } from '../../hooks/usePresence';
import { useAuth } from '../../hooks/useAuth';
import styles from '../../styles/RightSidebar.module.css';

/**
 * RightSidebar Component
 * Displays online users
 */
export function RightSidebar({ isOpen, onToggle }) {
  const { onlineUsers } = usePresence();
  const { user } = useAuth();

  return (
    <>
      <button
        className={`${styles.toggleButton} ${isOpen ? styles.open : ''}`}
        onClick={onToggle}
        aria-label={isOpen ? 'Hide users panel' : 'Show users panel'}
      >
        <span className={styles.toggleIcon}>{isOpen ? '>' : '<'}</span>
        {!isOpen && onlineUsers.length > 0 && (
          <span className={styles.userCount}>{onlineUsers.length}</span>
        )}
      </button>

      <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
        <div className={styles.content}>
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>
              Online Users ({onlineUsers.length})
            </h3>
            <ul className={styles.userList}>
              {onlineUsers.map((u) => (
                <li
                  key={u.id}
                  className={`${styles.userItem} ${u.id === user?.id ? styles.currentUser : ''}`}
                >
                  <span className={styles.userAvatar}>
                    {u.username.charAt(0).toUpperCase()}
                  </span>
                  <span className={styles.userName}>
                    {u.username}
                    {u.id === user?.id && ' (you)'}
                  </span>
                  <span className={styles.onlineIndicator} />
                </li>
              ))}
              {onlineUsers.length === 0 && (
                <li className={styles.emptyMessage}>No users online</li>
              )}
            </ul>
          </section>
        </div>
      </aside>
    </>
  );
}

export default RightSidebar;
