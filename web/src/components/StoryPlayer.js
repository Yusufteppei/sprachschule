"use client";
import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import StoryDisplay from './StoryDisplay';
import FloatingInput from './FloatingInput';
import { getStoryPayload, saveCurrentStory } from '@/lib/storyResponse';

const StoryPlayer = ({ baseUrl = "http://localhost:8000" }) => {
  const router = useRouter();
  const [userPreferences, setUserPreferences] = useState({
    level: 'B1',
    target_language: 'German',
    theme: 'Technology'
  });
  const [input, setInput] = useState('');
  const [story, setStory] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [transcript, setTranscript] = useState('');
  const [responseMessage, setResponseMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  // --- Refs ---
  const mediaRecorderRef = useRef(null);
  const wsRef = useRef(null);

  // --- Auth/token ---
  const [token, setToken] = useState(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
  });

  // --- Load user preferences on mount ---
  useEffect(() => {
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

  useEffect(() => {
    const updateToken = () => setToken(localStorage.getItem('auth_token'));
    updateToken();
    window.addEventListener('storage', updateToken);
    window.addEventListener('visibilitychange', updateToken);
    return () => {
      window.removeEventListener('storage', updateToken);
      window.removeEventListener('visibilitychange', updateToken);
    };
  }, []);

  // --- Recording Logic ---
  const startRecording = async () => {
    try {
      const authToken = token || localStorage.getItem('auth_token');
      if (!authToken) {
        setResponseMessage('Please sign in before recording.');
        return;
      }

      setResponseMessage('Requesting microphone...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Build websocket URL (include token in query)
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

      mr.start(250); // Emit every 250ms
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

  // --- API Interaction ---
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

      // Route based on response type
      const storyPayload = saveCurrentStory(data);
      if (storyPayload) {
        router.push('/story');
      } else {
        const fallbackPayload = getStoryPayload(data);
        setStory(fallbackPayload?.story || null);
        setAudioUrl(fallbackPayload?.audioUrl || '');
        setResponseMessage('Interaction complete.');
      }

      setInput('');
      setTranscript('');

    } catch (err) {
      console.error(err);
      setResponseMessage(err.message || 'Request failed');
    } finally {
      setIsLoading(false);
    }
  };

  // --- Audio Player Controls ---
  if (!token) {
    return (
      <div className="flex flex-col min-h-screen items-center justify-center bg-zinc-50 p-6">
        <div className="w-full max-w-2xl rounded-3xl border border-gray-200 bg-white p-10 shadow-xl text-center">
          <h1 className="text-3xl font-bold mb-4 text-gray-900">Sign in required</h1>
          <p className="mb-6 text-gray-600">
            You must sign in before using the story features.
          </p>
          <Link href="/auth" className="inline-flex items-center justify-center rounded-full bg-blue-600 px-6 py-3 text-white hover:bg-blue-700">
            Go to Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-xl shadow-lg bg-white max-w-3xl mx-auto border border-gray-100">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Story Interaction</h2>

      {story && (
        <div className="mb-6">
          <StoryDisplay
            story={story}
            audioUrl={audioUrl}
            baseUrl={baseUrl}
          />
        </div>
      )}

      <div className="grid gap-4 mb-6">
        <label className="block">
          <span className="block text-sm font-medium text-gray-700 mb-2">Your message</span>
          <textarea 
            value={input} 
            onChange={(e) => setInput(e.target.value)} 
            rows={3} 
            className="mt-1 block w-full rounded-md border-gray-300 border p-3 shadow-sm focus:ring-blue-500 focus:border-blue-500" 
            placeholder={transcript || "Type your request or use the microphone..."}
          />
        </label>
      </div>

      <div className="flex gap-3 mb-6">
        {!isRecording ? (
          <button 
            onClick={startRecording} 
            className="px-6 py-2 rounded-lg bg-red-600 text-white font-medium hover:bg-red-700 transition-colors"
          >
            Start Speaking
          </button>
        ) : (
          <button 
            onClick={stopRecording} 
            className="px-6 py-2 rounded-lg bg-gray-800 text-white font-medium animate-pulse"
          >
            Stop (Recording...)
          </button>
        )}

        <button 
          onClick={handleSubmit} 
          disabled={isLoading} 
          className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
        >
          {isLoading ? 'Processing…' : 'Send to Moderator'}
        </button>
      </div>

      {/* Feedback Messages */}
      {responseMessage && (
        <div className="mb-4 p-3 rounded-md bg-blue-50 text-blue-800 text-sm border border-blue-100">
          {responseMessage}
        </div>
      )}
      
      {transcript && (
        <div className="mb-4 p-3 rounded-md bg-gray-50 text-gray-600 text-sm italic border border-gray-200">
          Transcription: {transcript}
        </div>
      )}

      <FloatingInput
        isMinified={false}
        onStoryReceived={(data) => {
          if (saveCurrentStory(data)) {
            router.push('/story');
          }
        }}
        baseUrl={baseUrl}
      />
    </div>
  );

};

export default StoryPlayer;
