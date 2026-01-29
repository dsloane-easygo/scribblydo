import React, { useCallback, useEffect, useRef, useState } from 'react';
import Login from './components/Login';
import Register from './components/Register';
import Sidebar from './components/Sidebar';
import Whiteboard from './components/Whiteboard';
import RightSidebar from './components/presence/RightSidebar';
import { useAuth } from './hooks/useAuth';
import { useWhiteboards } from './hooks/useWhiteboards';
import './styles/global.css';

/**
 * MainApp Component
 * Main application content shown when authenticated
 */
function MainApp() {
  const { user, logout } = useAuth();
  const {
    whiteboards,
    selectedWhiteboardId,
    selectedWhiteboard,
    setSelectedWhiteboardId,
    loading,
    createWhiteboard,
    updateWhiteboard,
    deleteWhiteboard,
    isOwner,
  } = useWhiteboards();

  // Ref to call addNote from Whiteboard
  const whiteboardRef = useRef(null);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);

  // Dark mode state - persist per user
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem(`darkMode_${user?.id}`);
    return saved === 'true';
  });

  // Update body class and localStorage when dark mode changes
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    if (user?.id) {
      localStorage.setItem(`darkMode_${user.id}`, darkMode.toString());
    }
  }, [darkMode, user?.id]);

  const handleToggleDarkMode = useCallback(() => {
    setDarkMode((prev) => !prev);
  }, []);

  const handleAddNote = useCallback(() => {
    if (whiteboardRef.current) {
      whiteboardRef.current.addNote();
    }
  }, []);

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className={`app ${darkMode ? 'dark-mode' : ''}`}>
      <Sidebar
        whiteboards={whiteboards}
        selectedWhiteboardId={selectedWhiteboardId}
        selectedWhiteboard={selectedWhiteboard}
        onSelectWhiteboard={setSelectedWhiteboardId}
        onCreateWhiteboard={createWhiteboard}
        onUpdateWhiteboard={updateWhiteboard}
        onDeleteWhiteboard={deleteWhiteboard}
        onAddNote={handleAddNote}
        disabled={!selectedWhiteboardId}
        currentUser={user}
        onLogout={logout}
        isOwner={isOwner}
        darkMode={darkMode}
        onToggleDarkMode={handleToggleDarkMode}
      />
      <main className="main-content">
        <Whiteboard
          ref={whiteboardRef}
          whiteboardId={selectedWhiteboardId}
          rightSidebarOpen={rightSidebarOpen}
        />
      </main>
      <RightSidebar
        isOpen={rightSidebarOpen}
        onToggle={() => setRightSidebarOpen(!rightSidebarOpen)}
      />
    </div>
  );
}

/**
 * App Component
 * Root component handling authentication flow
 */
function App() {
  const { isAuthenticated, loading } = useAuth();
  const [showRegister, setShowRegister] = useState(false);

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (showRegister) {
      return <Register onSwitchToLogin={() => setShowRegister(false)} />;
    }
    return <Login onSwitchToRegister={() => setShowRegister(true)} />;
  }

  return <MainApp />;
}

export default App;
