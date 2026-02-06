import React, { useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { APP_CONFIG } from '../config/app';
import logo from '../../assets/logo.png';
import styles from '../styles/Auth.module.css';

/**
 * Register Component
 * Handles new user registration
 */
function Register({ onSwitchToLogin }) {
  const { register } = useAuth();
  const [username, setUsername] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      setError('');

      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }

      if (password.length < 8) {
        setError('Password must be at least 8 characters');
        return;
      }

      if (username.length < 3) {
        setError('Username must be at least 3 characters');
        return;
      }

      setLoading(true);

      try {
        await register(username, password, firstName, lastName);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [username, password, confirmPassword, firstName, lastName, register]
  );

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <img src={logo} alt={APP_CONFIG.name} className={styles.logo} />
        <h2 className={styles.subtitle}>Create Account</h2>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <input
              id="firstName"
              type="text"
              placeholder="First Name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              maxLength={100}
              autoComplete="given-name"
              autoFocus
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <input
              id="lastName"
              type="text"
              placeholder="Last Name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              maxLength={100}
              autoComplete="family-name"
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <input
              id="username"
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={50}
              autoComplete="username"
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <input
              id="password"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <input
              id="confirmPassword"
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
              disabled={loading}
            />
          </div>

          <button type="submit" className={styles.submitButton} disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className={styles.switchText}>
          Already have an account?{' '}
          <button
            type="button"
            className={styles.switchButton}
            onClick={onSwitchToLogin}
          >
            Sign In
          </button>
        </p>
      </div>
    </div>
  );
}

export default Register;
