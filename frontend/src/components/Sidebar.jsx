import React, { useState, useCallback } from 'react';
import styles from '../styles/Sidebar.module.css';

/**
 * Sidebar Component
 * Collapsible left navigation for whiteboard management
 */
function Sidebar({
  whiteboards,
  selectedWhiteboardId,
  onSelectWhiteboard,
  onCreateWhiteboard,
  onDeleteWhiteboard,
  onAddNote,
  disabled,
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');

  const handleToggle = useCallback(() => {
    setIsCollapsed((prev) => !prev);
  }, []);

  const handleCreateClick = useCallback(() => {
    setIsCreating(true);
    setNewName('');
  }, []);

  const handleCreateSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!newName.trim()) return;

      try {
        await onCreateWhiteboard(newName.trim());
        setIsCreating(false);
        setNewName('');
      } catch (err) {
        console.error('Failed to create whiteboard:', err);
      }
    },
    [newName, onCreateWhiteboard]
  );

  const handleCreateCancel = useCallback(() => {
    setIsCreating(false);
    setNewName('');
  }, []);

  const handleDelete = useCallback(
    async (id, name) => {
      if (window.confirm(`Delete whiteboard "${name}" and all its notes?`)) {
        try {
          await onDeleteWhiteboard(id);
        } catch (err) {
          console.error('Failed to delete whiteboard:', err);
        }
      }
    },
    [onDeleteWhiteboard]
  );

  return (
    <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}>
      <button
        className={styles.toggleButton}
        onClick={handleToggle}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? '▶' : '◀'}
      </button>

      {!isCollapsed && (
        <div className={styles.content}>
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Whiteboards</h2>

            <ul className={styles.whiteboardList}>
              {whiteboards.map((wb) => (
                <li
                  key={wb.id}
                  className={`${styles.whiteboardItem} ${
                    wb.id === selectedWhiteboardId ? styles.selected : ''
                  }`}
                >
                  <button
                    className={styles.whiteboardButton}
                    onClick={() => onSelectWhiteboard(wb.id)}
                  >
                    {wb.name}
                  </button>
                  <button
                    className={styles.deleteButton}
                    onClick={() => handleDelete(wb.id, wb.name)}
                    aria-label={`Delete ${wb.name}`}
                    title="Delete whiteboard"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>

            {isCreating ? (
              <form onSubmit={handleCreateSubmit} className={styles.createForm}>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Whiteboard name..."
                  className={styles.createInput}
                  autoFocus
                />
                <div className={styles.createActions}>
                  <button type="submit" className={styles.createSubmit}>
                    Add
                  </button>
                  <button
                    type="button"
                    className={styles.createCancel}
                    onClick={handleCreateCancel}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <button
                className={styles.addWhiteboardButton}
                onClick={handleCreateClick}
              >
                + New Whiteboard
              </button>
            )}
          </div>

          <div className={styles.section}>
            <button
              className={styles.addNoteButton}
              onClick={onAddNote}
              disabled={disabled || !selectedWhiteboardId}
            >
              + New Note
            </button>
          </div>
        </div>
      )}

      {isCollapsed && (
        <div className={styles.collapsedContent}>
          <button
            className={styles.collapsedButton}
            onClick={onAddNote}
            disabled={disabled || !selectedWhiteboardId}
            title="New Note"
          >
            +
          </button>
        </div>
      )}
    </aside>
  );
}

export default React.memo(Sidebar);
