import { useContext } from 'react';
import { PresenceContext } from '../context/PresenceContext';

/**
 * Custom hook for accessing presence context
 */
export function usePresence() {
  const context = useContext(PresenceContext);

  if (!context) {
    throw new Error('usePresence must be used within a PresenceProvider');
  }

  return context;
}

export default usePresence;
