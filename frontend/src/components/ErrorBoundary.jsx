import React from 'react';

/**
 * ErrorBoundary Component
 * Catches JavaScript errors in child components and displays a fallback UI.
 * Prevents the entire app from crashing due to errors in individual components.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render shows the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to console (could also send to error reporting service)
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Render fallback UI
      return (
        <div style={styles.container}>
          <div style={styles.card}>
            <h1 style={styles.title}>Something went wrong</h1>
            <p style={styles.message}>
              We apologize for the inconvenience. An unexpected error has occurred.
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details style={styles.details}>
                <summary style={styles.summary}>Error Details</summary>
                <pre style={styles.errorText}>
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            <div style={styles.buttons}>
              <button onClick={this.handleReset} style={styles.button}>
                Try Again
              </button>
              <button onClick={this.handleReload} style={styles.buttonSecondary}>
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '20px',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    padding: '40px',
    maxWidth: '500px',
    width: '100%',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
  },
  title: {
    color: '#e53935',
    fontSize: '24px',
    marginBottom: '16px',
    fontWeight: '600',
  },
  message: {
    color: '#666666',
    fontSize: '16px',
    marginBottom: '24px',
    lineHeight: '1.5',
  },
  details: {
    textAlign: 'left',
    marginBottom: '24px',
    backgroundColor: '#fff3f3',
    padding: '16px',
    borderRadius: '4px',
    border: '1px solid #ffcdd2',
  },
  summary: {
    cursor: 'pointer',
    color: '#c62828',
    fontWeight: '500',
    marginBottom: '8px',
  },
  errorText: {
    fontSize: '12px',
    color: '#b71c1c',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    marginTop: '8px',
    maxHeight: '200px',
    overflow: 'auto',
  },
  buttons: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
  },
  button: {
    backgroundColor: '#1976d2',
    color: '#ffffff',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
  },
  buttonSecondary: {
    backgroundColor: '#ffffff',
    color: '#1976d2',
    border: '1px solid #1976d2',
    padding: '12px 24px',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
  },
};

export default ErrorBoundary;
