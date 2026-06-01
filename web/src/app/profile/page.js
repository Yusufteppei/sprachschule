"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import FloatingInput from "@/components/FloatingInput";
import { saveCurrentStory } from "@/lib/storyResponse";

const baseUrl = "http://localhost:8000";

// Match backend enums
const PROFICIENCY_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const TARGET_LANGUAGES = [
  "French",
  "Spanish",
  "Italian",
  "German",
  "Russian",
  "Japanese",
  "Mandarin",
];
const STORY_THEMES = [
  "Technology",
  "Culture",
  "History",
  "Science",
  "Travel",
  "Food",
  "Sports",
  "Literature",
];

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    if (!token) {
      queueMicrotask(() => setLoading(false));
      return;
    }

    fetch(`${baseUrl}/api/v1/auth/profile`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          const payload = await res.json().catch(() => ({}));
          throw new Error(payload.detail || "Could not load profile.");
        }
        return res.json();
      })
      .then((data) => {
        setProfile(data);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message || "Unable to load profile.");
      })
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (field) => (event) => {
    setProfile({ ...profile, [field]: event.target.value });
    setMessage("");
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    const token = localStorage.getItem("auth_token");
    if (!token) {
      setError("Please sign in to edit your profile.");
      setSaving(false);
      return;
    }

    try {
      const response = await fetch(`${baseUrl}/api/v1/auth/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: profile.full_name,
          level: profile.level,
          target_language: profile.target_language,
          theme: profile.theme,
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Unable to save profile.");
      }

      const updated = await response.json();
      setProfile(updated);
      setMessage("Profile saved successfully.");
    } catch (err) {
      console.error(err);
      setError(err.message || "Error saving profile.");
    } finally {
      setSaving(false);
    }
  };

  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  return (
    <div className="min-h-screen bg-zinc-50 p-6">
      <div className="mx-auto max-w-3xl rounded-3xl border border-gray-200 bg-white p-8 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
            <p className="mt-1 text-sm text-gray-600">Update your name and learning preferences.</p>
          </div>
          <Link href="/" className="rounded-full border border-blue-600 bg-blue-50 px-4 py-2 text-blue-700 hover:bg-blue-100">
            Back to App
          </Link>
        </div>

        {!token && (
          <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4 text-yellow-900">
            You are not signed in. Please <Link href="/auth" className="font-semibold text-blue-600 hover:underline">sign in or sign up</Link> to edit your profile.
          </div>
        )}

        {loading && <div className="text-gray-600">Loading profile…</div>}

        {error && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>}
        {message && <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4 text-green-700">{message}</div>}

        {!loading && token && profile && (
          <form onSubmit={handleSave} className="space-y-5 mt-6">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="text-sm font-medium text-gray-700">Full name</span>
                <input
                  type="text"
                  value={profile.full_name || ""}
                  onChange={handleChange("full_name")}
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Your name"
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-gray-700">Username</span>
                <input
                  type="text"
                  value={profile.username}
                  disabled
                  className="mt-1 block w-full rounded-md border-gray-300 border bg-gray-100 p-2 shadow-sm"
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <label className="block">
                <span className="text-sm font-medium text-gray-700">Level</span>
                <select
                  value={profile.level || ""}
                  onChange={handleChange("level")}
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a level</option>
                  {PROFICIENCY_LEVELS.map((level) => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-medium text-gray-700">Target language</span>
                <select
                  value={profile.target_language || ""}
                  onChange={handleChange("target_language")}
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a language</option>
                  {TARGET_LANGUAGES.map((lang) => (
                    <option key={lang} value={lang}>{lang}</option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-medium text-gray-700">Favorite theme</span>
                <select
                  value={profile.theme || ""}
                  onChange={handleChange("theme")}
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a theme</option>
                  {STORY_THEMES.map((theme) => (
                    <option key={theme} value={theme}>{theme}</option>
                  ))}
                </select>
              </label>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
            >
              {saving ? "Saving…" : "Save Profile"}
            </button>
          </form>
        )}
      </div>

      <FloatingInput
        isMinified={true}
        onStoryReceived={(data) => {
          if (saveCurrentStory(data)) {
            router.push('/story');
          }
        }}
        baseUrl={baseUrl}
      />
    </div>
  );
}
