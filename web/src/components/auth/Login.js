"use client";
import React, { useState } from 'react';

const Login = ({ baseUrl = 'http://localhost:8000', onLogin }) => {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('test');
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('test');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let res;
      if (mode === 'signup') {
        res = await fetch(`${baseUrl}/api/v1/auth/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password }),
        });
      } else {
        const form = new URLSearchParams();
        form.append('username', username);
        form.append('password', password);
        res = await fetch(`${baseUrl}/api/v1/auth/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: form.toString(),
        });
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Authentication failed');
      }

      const data = await res.json();
      const token = data.access_token;
      if (!token) throw new Error('No token received');

      localStorage.setItem('auth_token', token);
      window.dispatchEvent(new Event('auth_change'));
      if (typeof onLogin === 'function') onLogin(token);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Authentication error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mb-6 p-4 border rounded-md bg-white">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">{mode === 'signup' ? 'Sign Up' : 'Sign In'}</h3>
        <button
          type="button"
          onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
          className="text-sm text-blue-600 hover:underline"
        >
          {mode === 'login' ? 'Create account' : 'Have an account? Sign in'}
        </button>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3">
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          className="border p-2 rounded"
          required
        />

        {mode === 'signup' && (
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            type="email"
            className="border p-2 rounded"
            required
          />
        )}

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="border p-2 rounded"
          required
        />

        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded"
          disabled={loading}
        >
          {loading ? (mode === 'signup' ? 'Creating account…' : 'Signing in…') : (mode === 'signup' ? 'Sign Up' : 'Sign In')}
        </button>

        {mode === 'login' && (
          <button
            type="button"
            className="px-3 py-2 bg-gray-200 rounded"
            onClick={() => {
              setUsername('test');
              setPassword('test');
              setEmail('test@example.com');
            }}
          >
            Demo
          </button>
        )}

        {error && <div className="text-sm text-red-600">{error}</div>}
      </form>
    </div>
  );
};

export default Login;
