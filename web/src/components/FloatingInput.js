"use client";
import React, { useState, useRef } from 'react';

export default function FloatingInput({
  isMinified = false,
  onSubmit,
  onStoryReceived,
  baseUrl = "http://localhost:8000"
}) {
  const [minimized, setMinimized] = useState(isMinified);
  const [input, setInput] = useState('');
  const [transcript, setTranscript] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [responseMessage, setResponseMessage] = useState('');
  const [userPreferences, setUserPreferences] = useState({
    level: 'B1',
    target_language: 'German',
    theme: 'Technology'
  });

  const mediaRecorderRef = useRef(null);
  const wsRef = useRef(null);
  const [token, setToken] = useState(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
  });

  const isAuthenticated = Boolean(token);

  // Load user preferences
  React.useEffect(() => {
    const loadUserPreferences = async () => {
      const authToken = localStorage.getItem('auth_token');
      if (!authToken) return;

      try {
        const response = await fetch(`${baseUrl}/api/v1/auth/profile`, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        if (!response.ok) return;
        
        const profile = await response.json();
        setUserPreferences({
          level: profile.level || 'B1',
          target_language: profile.target_language || 'German',
          theme: profile.theme || 'Technology'
        });
      } catch (err) {
        console.error('Failed to load user preferences:', err);
      }
    };

    loadUserPreferences();
  }, [baseUrl]);

  React.useEffect(() => {
    const updateToken = () => setToken(localStorage.getItem('auth_token'));
    updateToken();
    window.addEventListener('storage', updateToken);
    window.addEventListener('visibilitychange', updateToken);
    return () => {
      window.removeEventListener('storage', updateToken);
      window.removeEventListener('visibilitychange', updateToken);
    };
  }, []);

  const startRecording = async () => {
    try {
      const authToken = token || localStorage.getItem('auth_token');
      if (!authToken) {
        setResponseMessage('Please sign in before recording.');
        return;
      }

      setResponseMessage('Requesting microphone...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const base = new URL(baseUrl);
      const wsProto = base.protocol === 'https:' ? 'wss:' : 'ws:';
      const tokenQuery = `?token=${encodeURIComponent(authToken)}`;
      const wsUrl = `${wsProto}//${base.host}/story/ws/listen${tokenQuery}`;

      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        setResponseMessage('Recording and streaming...');
        setIsRecording(true);
      };

      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.partial) setTranscript(msg.partial);
          if (msg.final) {
            setTranscript(msg.final);
            setResponseMessage('Final transcription received.');
          }
        } catch (e) {
          // Ignore non-json messages
        }
      };

      ws.onerror = (e) => {
        console.error('WebSocket error', e);
        setResponseMessage('WebSocket error. See console.');
      };

      wsRef.current = ws;

      const options = { mimeType: 'audio/webm' };
      const mr = new MediaRecorder(stream, options);

      mr.ondataavailable = async (event) => {
        if (!event.data || event.data.size === 0) return;
        const buffer = await event.data.arrayBuffer();
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(buffer);
        }
      };

      mr.onstop = () => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send('DONE');
        }
        setIsRecording(false);
      };

      mr.start(250);
      mediaRecorderRef.current = mr;

    } catch (err) {
      console.error(err);
      setResponseMessage('Unable to access microphone.');
    }
  };

  const stopRecording = () => {
    try {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmit = async () => {
    const authToken = token || localStorage.getItem('auth_token');
    if (!authToken) {
      setResponseMessage('Please sign in before sending to the moderator.');
      return;
    }

    const userInput = input || transcript;
    if (!userInput) {
      setResponseMessage('Please enter text or speak first.');
      return;
    }

    setIsLoading(true);
    setResponseMessage('Sending to moderator...');

    const formData = new FormData();
    formData.append('input_text', userInput);
    formData.append('level', userPreferences.level);
    formData.append('theme', userPreferences.theme);

    try {
      const response = await fetch(`${baseUrl}/interaction/`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        body: formData,
      });

      const data = await response.json();
      if (!data.success) throw new Error(data.error || 'Interaction failed');

      setResponseMessage('Response received.');
      setInput('');
      setTranscript('');

      // Callback to parent with response
      if (onStoryReceived) {
        onStoryReceived(data);
      }

    } catch (err) {
      console.error(err);
      setResponseMessage(err.message || 'Request failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (minimized) {
    return (
      <button
        type="button"
        onClick={() => setMinimized(false)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 flex items-center justify-center text-xl font-bold z-50"
        title="Open input"
      >
        +
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 bg-white rounded-2xl shadow-2xl p-6 border border-gray-200 z-50 max-h-96 overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-900">Input</h3>
        <button
          type="button"
          onClick={() => setMinimized(true)}
          className="text-gray-400 hover:text-gray-600 text-xl font-bold"
        >
          −
        </button>
      </div>

      {!isAuthenticated && (
        <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-900">
          Please sign in on the main app or <a href="/auth" className="font-semibold text-blue-600 hover:underline">Sign In</a> to enable story requests.
        </div>
      )}

      <div className="grid gap-3 mb-4">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={3}
          disabled={!isAuthenticated}
          className="mt-1 block w-full rounded-md border-gray-300 border p-2 text-sm shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:cursor-not-allowed disabled:bg-gray-100"
          placeholder={isAuthenticated ? transcript || "Type your request..." : "Sign in to enable story requests..."}
        />
      </div>

      <div className="flex gap-2 mb-3">
        {!isRecording ? (
          <button
            onClick={startRecording}
            disabled={!isAuthenticated}
            className="flex-1 px-3 py-2 rounded-lg bg-red-600 text-white font-medium text-sm hover:bg-red-700 disabled:bg-red-300 disabled:cursor-not-allowed transition-colors"
          >
            Record
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="flex-1 px-3 py-2 rounded-lg bg-gray-800 text-white font-medium text-sm animate-pulse"
          >
            Stop
          </button>
        )}

        <button
          onClick={handleSubmit}
          disabled={!isAuthenticated || isLoading}
          className="flex-1 px-3 py-2 rounded-lg bg-blue-600 text-white font-medium text-sm hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Sending…' : 'Send'}
        </button>
      </div>

      {responseMessage && (
        <div className="mb-3 p-2 rounded-md bg-blue-50 text-blue-800 text-xs border border-blue-100">
          {responseMessage}
        </div>
      )}

      {transcript && (
        <div className="p-2 rounded-md bg-gray-50 text-gray-600 text-xs italic border border-gray-200">
          Transcript: {transcript}
        </div>
      )}
    </div>
  );
}
