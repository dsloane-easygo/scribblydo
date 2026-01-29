import React, { useState, useCallback } from 'react';
import styles from '../styles/Sidebar.module.css';
import logo from '../../assets/logo.png';

const ACCESS_ICONS = {
  public: '🌐',
  private: '🔒',
  shared: '👥',
};

/**
 * Sidebar Component
 * Collapsible left navigation for whiteboard management
 */
function Sidebar({
  whiteboards,
  selectedWhiteboardId,
  selectedWhiteboard: _selectedWhiteboard,
  onSelectWhiteboard,
  onCreateWhiteboard,
  onUpdateWhiteboard,
  onDeleteWhiteboard,
  onAddNote,
  disabled,
  currentUser,
  onLogout,
  isOwner,
  darkMode,
  onToggleDarkMode,
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newAccessType, setNewAccessType] = useState('public');

  const handleToggle = useCallback(() => {
    setIsCollapsed((prev) => !prev);
  }, []);

  const handleCreateClick = useCallback(() => {
    setIsCreating(true);
    setNewName('');
    setNewAccessType('public');
  }, []);

  const handleCreateSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!newName.trim()) return;

      try {
        await onCreateWhiteboard(newName.trim(), newAccessType);
        setIsCreating(false);
        setNewName('');
        setNewAccessType('public');
      } catch (err) {
        console.error('Failed to create whiteboard:', err);
      }
    },
    [newName, newAccessType, onCreateWhiteboard]
  );

  const handleCreateCancel = useCallback(() => {
    setIsCreating(false);
    setNewName('');
    setNewAccessType('public');
  }, []);

  const handleDelete = useCallback(
    async (id, name) => {
      if (window.confirm(`Delete board "${name}" and all its notes?`)) {
        try {
          await onDeleteWhiteboard(id);
        } catch (err) {
          console.error('Failed to delete whiteboard:', err);
        }
      }
    },
    [onDeleteWhiteboard]
  );

  const cycleAccessType = useCallback(
    async (wb) => {
      const order = ['public', 'shared', 'private'];
      const currentIndex = order.indexOf(wb.access_type);
      const nextIndex = (currentIndex + 1) % order.length;
      const nextType = order[nextIndex];

      try {
        await onUpdateWhiteboard(wb.id, { access_type: nextType });
      } catch (err) {
        console.error('Failed to update whiteboard access:', err);
      }
    },
    [onUpdateWhiteboard]
  );

  const getAccessIcon = (wb) => {
    return ACCESS_ICONS[wb.access_type] || ACCESS_ICONS.public;
  };

  return (
    <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}>
      <button
        className={styles.toggleButton}
        onClick={handleToggle}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? '\u25B6' : '\u25C0'}
      </button>

      {!isCollapsed && (
        <div className={styles.content}>
          <div className={styles.logoSection}>
            <img src={logo} alt="ScribblyDo" className={styles.logo} />
          </div>

          <div className={styles.userSection}>
            <div className={styles.userInfo}>
              <span className={styles.userName}>
                {currentUser?.first_name && currentUser?.last_name
                  ? `${currentUser.first_name} ${currentUser.last_name}`
                  : currentUser?.username}
              </span>
            </div>
          </div>

          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Boards</h2>

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
                    <span className={styles.whiteboardName}>
                      <span className={styles.accessIcon} title={wb.access_type}>
                        {getAccessIcon(wb)}
                      </span>
                      {wb.name}
                    </span>
                    <span className={styles.whiteboardOwner}>
                      {wb.owner_username}
                    </span>
                  </button>
                  {isOwner(wb) && (
                    <div className={styles.whiteboardActions}>
                      <button
                        className={styles.accessButton}
                        onClick={() => cycleAccessType(wb)}
                        aria-label={`Change access (currently ${wb.access_type})`}
                        title={`Click to change access (currently ${wb.access_type})`}
                      >
                        {getAccessIcon(wb)}
                      </button>
                      <button
                        className={styles.deleteButton}
                        onClick={() => handleDelete(wb.id, wb.name)}
                        aria-label={`Delete ${wb.name}`}
                        title="Delete board"
                      >
                        &times;
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>

            {isCreating ? (
              <form onSubmit={handleCreateSubmit} className={styles.createForm}>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Board name..."
                  className={styles.createInput}
                  autoFocus
                />
                <div className={styles.accessSelector}>
                  <label className={styles.accessOption}>
                    <input
                      type="radio"
                      name="accessType"
                      value="public"
                      checked={newAccessType === 'public'}
                      onChange={(e) => setNewAccessType(e.target.value)}
                    />
                    <span>🌐 Public</span>
                  </label>
                  <label className={styles.accessOption}>
                    <input
                      type="radio"
                      name="accessType"
                      value="shared"
                      checked={newAccessType === 'shared'}
                      onChange={(e) => setNewAccessType(e.target.value)}
                    />
                    <span>👥 Shared</span>
                  </label>
                  <label className={styles.accessOption}>
                    <input
                      type="radio"
                      name="accessType"
                      value="private"
                      checked={newAccessType === 'private'}
                      onChange={(e) => setNewAccessType(e.target.value)}
                    />
                    <span>🔒 Private</span>
                  </label>
                </div>
                <div className={styles.createActions}>
                  <button type="submit" className={styles.createSubmit}>
                    Create
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
                + New Board
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

          <div className={styles.bottomSection}>
            <button
              className={styles.themeToggle}
              onClick={onToggleDarkMode}
              title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
            <button
              className={styles.logoutButton}
              onClick={onLogout}
              title="Sign out"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
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
