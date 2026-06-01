"use client";
import { useMemo, useState, useSyncExternalStore } from 'react';
import Link from 'next/link';
import StoryDisplay from '@/components/StoryDisplay';
import FloatingInput from '@/components/FloatingInput';
import { getStoryPayload } from '@/lib/storyResponse';

const subscribeToStorage = (callback) => {
  window.addEventListener('storage', callback);
  return () => window.removeEventListener('storage', callback);
};

const getAuthTokenSnapshot = () => localStorage.getItem('auth_token');
const getCurrentStorySnapshot = () => sessionStorage.getItem('currentStory');
const getServerSnapshot = () => null;

export default function StoryPage() {
  const [story, setStory] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  const baseUrl = "http://localhost:8000";
  const token = useSyncExternalStore(subscribeToStorage, getAuthTokenSnapshot, getServerSnapshot);
  const savedStory = useSyncExternalStore(subscribeToStorage, getCurrentStorySnapshot, getServerSnapshot);
  const savedPayload = useMemo(() => {
    if (!savedStory) return null;
    try {
      return JSON.parse(savedStory);
    } catch (e) {
      console.error('Failed to parse saved story:', e);
      return null;
    }
  }, [savedStory]);

  const displayStory = story || savedPayload?.story || null;
  const displayAudioUrl = audioUrl || savedPayload?.audioUrl || '';

  const handleStoryReceived = (data) => {
    const storyPayload = getStoryPayload(data);
    if (storyPayload) {
      setStory(storyPayload.story);
      setAudioUrl(storyPayload.audioUrl);
    }
  };

  if (!token) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-50 p-6">
        <div className="text-center">
          <p className="mb-4 text-gray-600">Please <Link href="/auth" className="text-blue-600 font-semibold hover:underline">sign in</Link> to view stories.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-zinc-50 p-6">
      <div className="w-full max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Story</h1>
          <div className="flex gap-3">
            <Link href="/" className="rounded-full border border-blue-600 bg-blue-50 px-4 py-2 text-blue-700 hover:bg-blue-100">
              Home
            </Link>
            <Link href="/profile" className="rounded-full border border-blue-600 bg-blue-50 px-4 py-2 text-blue-700 hover:bg-blue-100">
              Profile
            </Link>
          </div>
        </div>

        {displayStory ? (
          <StoryDisplay
            story={displayStory}
            audioUrl={displayAudioUrl}
            baseUrl={baseUrl}
          />
        ) : (
          <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm text-center">
            <p className="text-gray-500">Send a request to generate a story.</p>
          </div>
        )}
      </div>

      <FloatingInput
        isMinified={true}
        onStoryReceived={handleStoryReceived}
        baseUrl={baseUrl}
      />
    </div>
  );
}
