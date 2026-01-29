import React, { useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { APP_CONFIG } from '../config/app';
import logo from '../../assets/logo.png';
import styles from '../styles/Auth.module.css';

/**
 * Login Component
 * Handles user authentication
 */
function Login({ onSwitchToRegister }) {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      setError('');
      setLoading(true);

      try {
        await login(username, password);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [username, password, login]
  );

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <img src={logo} alt={APP_CONFIG.name} className={styles.logo} />
        <h2 className={styles.subtitle}>Sign In</h2>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              autoFocus
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          <button type="submit" className={styles.submitButton} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className={styles.switchText}>
          Don't have an account?{' '}
          <button
            type="button"
            className={styles.switchButton}
            onClick={onSwitchToRegister}
          >
            Register
          </button>
        </p>
      </div>
    </div>
  );
}

export default Login;
