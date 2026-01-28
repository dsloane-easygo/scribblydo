import React, { useCallback, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Whiteboard from './components/Whiteboard';
import { useWhiteboards } from './hooks/useWhiteboards';
import './styles/global.css';

/**
 * App Component
 * Root component for the Todo Whiteboard application
 */
function App() {
  const {
    whiteboards,
    selectedWhiteboardId,
    setSelectedWhiteboardId,
    loading,
    createWhiteboard,
    deleteWhiteboard,
  } = useWhiteboards();

  // Ref to call addNote from Whiteboard
  const whiteboardRef = useRef(null);

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
    <div className="app">
      <Sidebar
        whiteboards={whiteboards}
        selectedWhiteboardId={selectedWhiteboardId}
        onSelectWhiteboard={setSelectedWhiteboardId}
        onCreateWhiteboard={createWhiteboard}
        onDeleteWhiteboard={deleteWhiteboard}
        onAddNote={handleAddNote}
        disabled={!selectedWhiteboardId}
      />
      <main className="main-content">
        <Whiteboard
          ref={whiteboardRef}
          whiteboardId={selectedWhiteboardId}
        />
      </main>
    </div>
  );
}

export default App;
