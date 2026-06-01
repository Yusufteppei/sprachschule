"use client";

import React, { useEffect, useRef, useState } from "react";

export default function StoryDisplay({ story, audioUrl, baseUrl = "http://localhost:8000" }) {
  const [showText, setShowText] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecordingSpeech, setIsRecordingSpeech] = useState(false);
  const [speechFeedback, setSpeechFeedback] = useState(null);
  const [recordingMessage, setRecordingMessage] = useState('');
  const [recordedChunks, setRecordedChunks] = useState([]);
  const [popoverWord, setPopoverWord] = useState(null);
  const [popoverWordIndex, setPopoverWordIndex] = useState(null);
  const [popoverStyle, setPopoverStyle] = useState({ top: 0, left: 0 });
  const audioRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const speechRecorderRef = useRef(null);
  const hidePopoverTimer = useRef(null);

  const fullAudioUrl = audioUrl
    ? audioUrl.startsWith("http")
      ? audioUrl
      : `${baseUrl.replace(/\/$/, "")}${audioUrl}`
    : null;

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const handleToggleText = () => {
    setShowText((current) => !current);
  };

  const cancelHidePopover = () => {
    if (hidePopoverTimer.current) {
      clearTimeout(hidePopoverTimer.current);
      hidePopoverTimer.current = null;
    }
  };

  const scheduleHidePopover = () => {
    cancelHidePopover();
    hidePopoverTimer.current = window.setTimeout(() => {
      setPopoverWord(null);
      setPopoverWordIndex(null);
    }, 150);
  };

  const showPopoverForWord = (word, index, event) => {
    cancelHidePopover();
    const rect = event.currentTarget.getBoundingClientRect();
    setPopoverWord(word);
    setPopoverWordIndex(index);
    setPopoverStyle({ top: rect.bottom + window.scrollY + 10, left: rect.left + window.scrollX });
  };

  const speakWord = (word) => {
    if (!word || typeof window === 'undefined') return;
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = 'de-DE';
    utterance.rate = 0.95;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  const handlePlay = () => {
    if (!fullAudioUrl) return;

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const audio = new Audio(fullAudioUrl);
    audioRef.current = audio;

    audio.onended = () => {
      setIsPlaying(false);
    };

    audio.play()
      .then(() => setIsPlaying(true))
      .catch((error) => {
        console.error("Story playback failed:", error);
        setIsPlaying(false);
      });
  };

  const startSpeechRecording = async () => {
    try {
      if (!story?.id) {
        setRecordingMessage('Cannot analyze speech without a saved story ID.');
        return;
      }

      setRecordingMessage('Requesting microphone permission...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      recordedChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
          setRecordedChunks([...recordedChunksRef.current]);
        }
      };

      recorder.onstart = () => {
        setIsRecordingSpeech(true);
        setRecordingMessage('Recording your reading...');
      };

      recorder.onstop = () => {
        setIsRecordingSpeech(false);
        setRecordingMessage('Uploading speech for analysis...');
        uploadSpeechFeedback();
      };

      recorder.start();
      speechRecorderRef.current = recorder;
    } catch (error) {
      console.error(error);
      setRecordingMessage('Unable to access microphone.');
    }
  };

  const stopSpeechRecording = () => {
    if (speechRecorderRef.current && speechRecorderRef.current.state !== 'inactive') {
      speechRecorderRef.current.stop();
    }
  };

  const uploadSpeechFeedback = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setSpeechFeedback({ success: false, feedback: 'Please sign in first.' });
        return;
      }

      const blob = new Blob(recordedChunksRef.current, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('story_id', story.id.toString());
      formData.append('audio_file', blob, 'speech.webm');

      const response = await fetch(`${baseUrl}/speech/analyze`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();
      if (!data.success) {
        setSpeechFeedback({ success: false, feedback: data.error || 'Speech analysis failed.' });
      } else {
        setSpeechFeedback({ success: true, feedback: data.data.feedback, issues: data.data.issues || [] });
      }
    } catch (error) {
      console.error(error);
      setSpeechFeedback({ success: false, feedback: 'Speech analysis request failed.' });
    } finally {
      setRecordingMessage('');
      recordedChunksRef.current = [];
      setRecordedChunks([]);
    }
  };

  const handleStop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
    }
  };

  return (
    <div className="mt-8 p-6 rounded-xl border border-gray-200 bg-gray-50 shadow-inner">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-xl font-bold text-gray-900">{story.title}</h3>
          <p className="mt-1 text-sm text-gray-600">
            Theme: {story.theme} · Level: {story.level}
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleToggleText}
            className="rounded-lg border border-blue-600 bg-blue-50 px-4 py-2 text-blue-700 hover:bg-blue-100"
          >
            {showText ? "Hide Text" : "Show Text"}
          </button>
          <button
            type="button"
            onClick={handlePlay}
            disabled={!fullAudioUrl}
            className="rounded-lg bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-green-300"
          >
            {isPlaying ? "Playing…" : "Listen"}
          </button>
          <button
            type="button"
            onClick={handleStop}
            disabled={!isPlaying}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:text-gray-400"
          >
            Stop
          </button>
          <button
            type="button"
            onClick={isRecordingSpeech ? stopSpeechRecording : startSpeechRecording}
            className="rounded-lg border border-purple-600 bg-purple-50 px-4 py-2 text-purple-700 hover:bg-purple-100 disabled:cursor-not-allowed disabled:text-gray-400"
          >
            {isRecordingSpeech ? 'Stop & Analyze' : 'Read Aloud'}
          </button>
        </div>
      </div>

      {showText ? (
        <div className="mt-6 relative">
          <div
            className="whitespace-pre-line text-gray-800 leading-relaxed"
            onMouseLeave={scheduleHidePopover}
          >
            {story.content.split(/(\s+)/).map((token, idx) => {
              if (/^\s+$/.test(token)) {
                return token;
              }
              return (
                <span
                  key={`${token}-${idx}`}
                  className={`relative cursor-pointer rounded transition ${popoverWordIndex === idx ? 'bg-yellow-100' : 'hover:bg-yellow-100'}`}
                  onMouseEnter={(event) => showPopoverForWord(token, idx, event)}
                  onMouseLeave={scheduleHidePopover}
                >
                  {token}
                </span>
              );
            })}
          </div>

          {popoverWord && (
            <div
              className="pointer-events-auto fixed z-50 w-40 rounded-2xl border border-gray-200 bg-white p-3 shadow-xl"
              style={{ top: popoverStyle.top, left: popoverStyle.left }}
              onMouseEnter={cancelHidePopover}
              onMouseLeave={scheduleHidePopover}
            >
              <p className="text-sm font-semibold text-gray-900">{popoverWord}</p>
              <div className="mt-2 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={() => speakWord(popoverWord)}
                  className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Read
                </button>
                <button
                  type="button"
                  disabled
                  className="rounded-lg border border-gray-300 bg-gray-100 px-3 py-2 text-sm font-medium text-gray-500 cursor-not-allowed"
                >
                  Translate
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="mt-6 rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center text-gray-500">
          Text display is hidden. Use Listen to enjoy the story without reading.
        </div>
      )}

      {!fullAudioUrl && (
        <p className="mt-6 text-sm text-gray-500">
          Audio is not available for this story yet.
        </p>
      )}

      {recordingMessage && (
        <div className="mt-4 rounded-lg bg-yellow-50 border border-yellow-200 p-4 text-sm text-yellow-900">
          {recordingMessage}
        </div>
      )}

      {speechFeedback && (
        <div className={`mt-4 rounded-lg p-4 text-sm ${speechFeedback.success ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
          <p>{speechFeedback.feedback}</p>
          {speechFeedback.issues && speechFeedback.issues.length > 0 && (
            <ul className="mt-2 list-disc list-inside">
              {speechFeedback.issues.map((issue) => (
                <li key={issue.word}>
                  {issue.word} ({issue.count} ×)
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
