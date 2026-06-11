"use client";

import { useEffect, useState } from "react";
import StoryPlayer from "@/components/StoryPlayer";
import Link from "next/link";

const getAuthToken = () => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
};

export default function Home() {
  const [token, setToken] = useState(getAuthToken);
  const signedIn = Boolean(token);

  useEffect(() => {
    const handleAuthChange = () => setToken(getAuthToken());
    window.addEventListener("storage", handleAuthChange);
    window.addEventListener("auth_change", handleAuthChange);
    return () => {
      window.removeEventListener("storage", handleAuthChange);
      window.removeEventListener("auth_change", handleAuthChange);
    };
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem("auth_token");
    window.dispatchEvent(new Event("auth_change"));
    setToken(null);
  };

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black min-h-screen p-6">
      <div className="w-full max-w-4xl">
        <div className="flex justify-end gap-3 mb-4">
          {signedIn ? (
            <>
              <Link href="/profile" className="rounded-full border border-blue-600 bg-blue-50 px-4 py-2 text-blue-700 hover:bg-blue-100">
                Profile
              </Link>
              <button
                type="button"
                onClick={handleSignOut}
                className="rounded-full border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-100"
              >
                Sign Out
              </button>
            </>
          ) : (
            <Link href="/auth" className="rounded-full border border-blue-600 bg-blue-50 px-4 py-2 text-blue-700 hover:bg-blue-100">
              Sign In / Sign Up
            </Link>
          )}
        </div>
        <StoryPlayer />
      </div>
    </div>
  );
}
