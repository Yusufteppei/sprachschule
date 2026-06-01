"use client";
import Login from "@/components/auth/Login";
import { useRouter } from "next/navigation";
import FloatingInput from "@/components/FloatingInput";
import { saveCurrentStory } from "@/lib/storyResponse";

export default function AuthPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-3xl border border-gray-200 bg-white p-8 shadow-xl">
        <h1 className="text-3xl font-bold mb-4 text-gray-900">Sign In / Sign Up</h1>
        <p className="text-sm text-gray-600 mb-6">
          Use the form below to create an account or sign in, then return to the main app.
        </p>
        <Login baseUrl="http://localhost:8000" onLogin={() => router.push("/")} />
      </div>

      <FloatingInput
        isMinified={true}
        onStoryReceived={(data) => {
          if (saveCurrentStory(data)) {
            router.push('/story');
          }
        }}
        baseUrl="http://localhost:8000"
      />
    </div>
  );
}
