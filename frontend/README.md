# Todo Whiteboard Frontend

A React-based frontend for the collaborative Todo Whiteboard application with real-time features.

## Features

- **Authentication**: Login and registration with JWT tokens
- **Multiple Whiteboards**: Create, view, and manage whiteboards
- **Draggable Notes**: Post-it style notes with drag-and-drop
- **Real-time Updates**: Instant sync via WebSocket
- **Live Cursors**: See other users' mouse positions
- **User Presence**: See who's online and viewing the same board
- **Responsive Design**: Works on desktop and tablet

## Quick Start

### Prerequisites

- Node.js 18+
- Backend services running (see main README)

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Access Points

| URL | Description |
|-----|-------------|
| http://localhost:5173 | Development server |
| http://localhost:4173 | Production preview |

## Tech Stack

| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| Vite 5 | Build tool |
| react-draggable | Drag-and-drop |
| CSS Modules | Scoped styling |
| WebSocket API | Real-time communication |

## Project Structure

```
frontend/
├── src/
│   ├── main.jsx              # Entry point
│   ├── App.jsx               # Root component
│   ├── components/
│   │   ├── Sidebar.jsx       # Whiteboard navigation
│   │   ├── Whiteboard.jsx    # Main canvas area
│   │   ├── PostItNote.jsx    # Draggable note
│   │   ├── AddNoteButton.jsx # Add note button
│   │   ├── Login.jsx         # Login form
│   │   ├── Register.jsx      # Registration form
│   │   ├── cursors/          # Remote cursor display
│   │   │   ├── CursorOverlay.jsx
│   │   │   └── RemoteCursor.jsx
│   │   └── presence/         # Online users display
│   │       └── RightSidebar.jsx
│   ├── context/
│   │   ├── AuthContext.jsx      # Authentication state
│   │   ├── WebSocketContext.jsx # WebSocket connection
│   │   └── PresenceContext.jsx  # Online users state
│   ├── hooks/
│   │   ├── useAuth.js           # Auth hook
│   │   ├── useWebSocket.js      # WebSocket hook
│   │   ├── useNotes.js          # Notes API
│   │   ├── useWhiteboards.js    # Whiteboards API
│   │   ├── useCursors.js        # Cursor tracking
│   │   └── usePresence.js       # Presence hook
│   └── styles/                  # CSS Modules
├── public/
├── index.html
├── vite.config.js
├── package.json
└── Dockerfile
```

## Key Components

### Contexts

- **AuthContext**: Manages login state, tokens, and user info
- **WebSocketContext**: Handles WebSocket connection, auto-reconnect, and message routing
- **PresenceContext**: Tracks online users and whiteboard viewers

### Hooks

- **useAuth**: Access authentication state and methods
- **useWebSocket**: Access WebSocket connection and subscribe to messages
- **useNotes**: CRUD operations for notes with optimistic updates
- **useWhiteboards**: CRUD operations for whiteboards
- **useCursors**: Real-time cursor tracking (send/receive)
- **usePresence**: Access online users and viewers

## Environment Configuration

The frontend connects to the backend via Vite's proxy configuration:

```javascript
// vite.config.js
proxy: {
  '/api': 'http://localhost:8000',
  '/ws': { target: 'ws://localhost:8000', ws: true }
}
```

## Docker

Build the Docker image:

```bash
docker build -t todo-frontend:local .
```

The image uses:
- Node.js for building
- Nginx for serving static files
