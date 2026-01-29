import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuthProvider } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { PresenceProvider } from './context/PresenceContext';
import { APP_CONFIG } from './config/app';
import './styles/global.css';

// Set document title from config
document.title = APP_CONFIG.name;

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <WebSocketProvider>
        <PresenceProvider>
          <App />
        </PresenceProvider>
      </WebSocketProvider>
    </AuthProvider>
  </React.StrictMode>
);
