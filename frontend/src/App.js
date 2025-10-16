import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import LoadingSpinner from './components/LoadingSpinner';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    // Simulate initial loading
    setTimeout(() => {
      setInitialLoading(false);
    }, 800);
  }, []);

  const handleLogin = (newToken) => {
    setLoading(true);
    setTimeout(() => {
      localStorage.setItem('token', newToken);
      setToken(newToken);
      setLoading(false);
    }, 1000);
  };

  const handleLogout = () => {
    setLoading(true);
    setTimeout(() => {
      localStorage.removeItem('token');
      setToken(null);
      setLoading(false);
    }, 500);
  };

  if (initialLoading) {
    return (
      <div className="app-container">
        <LoadingSpinner message="Loading Package Manager..." />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="app-container">
        <LoadingSpinner message={token ? "Logging out..." : "Logging in..."} />
      </div>
    );
  }

  return (
    <div className="app-container">
      {token ? (
        <Dashboard token={token} onLogout={handleLogout} />
      ) : (
        <Login onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;
