"use client";

/**
 * YouTube OAuth Callback Page
 * ---------------------------
 * Google redirects here after the user grants (or denies) permission.
 * This page runs inside the OAuth popup window opened by YouTubePublishModal.
 *
 * Flow:
 *  1. Extract the `code` (or `error`) from the URL search params.
 *  2. Post a message to the opener (the main app window).
 *  3. The YouTubePublishModal listener picks it up, exchanges the code,
 *     and closes this popup.
 *
 * NOTE: In Google Cloud Console → OAuth Credentials → Authorised redirect URIs
 * add:  http://localhost:3000/auth/youtube/callback
 */

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

// ── Inner component (needs useSearchParams — wrapped in Suspense below) ───────

function CallbackInner() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"processing" | "success" | "error">(
    "processing"
  );
  const [message, setMessage] = useState("Processing authentication…");

  useEffect(() => {
    const code = searchParams.get("code");
    const error = searchParams.get("error");

    if (error) {
      setStatus("error");
      setMessage(`Google denied access: ${error}`);
      if (window.opener) {
        window.opener.postMessage(
          { type: "youtube_oauth_callback", error },
          window.location.origin
        );
      }
      return;
    }

    if (code) {
      setStatus("success");
      setMessage("Authentication successful! You can close this window.");
      if (window.opener) {
        window.opener.postMessage(
          { type: "youtube_oauth_callback", code },
          window.location.origin
        );
        setTimeout(() => window.close(), 1500);
      }
      return;
    }

    setStatus("error");
    setMessage("No authorization code received from Google.");
  }, [searchParams]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white gap-6 px-6">
      {/* YouTube logo */}
      <svg viewBox="0 0 90 64" className="w-20 h-14" fill="none">
        <rect width="90" height="64" rx="12" fill="#FF0000" />
        <polygon points="36,16 36,48 64,32" fill="white" />
      </svg>

      {status === "processing" && (
        <div className="flex flex-col items-center gap-3">
          <span className="animate-spin inline-block w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full" />
          <p className="text-sm text-gray-600">{message}</p>
        </div>
      )}

      {status === "success" && (
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center text-2xl text-green-600 font-bold">
            ✓
          </div>
          <p className="text-sm font-semibold text-gray-800">
            Connected to YouTube!
          </p>
          <p className="text-xs text-gray-400">{message}</p>
        </div>
      )}

      {status === "error" && (
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center text-2xl text-red-600 font-bold">
            ✕
          </div>
          <p className="text-sm font-semibold text-gray-800">
            Authentication failed
          </p>
          <p className="text-xs text-gray-500 max-w-xs">{message}</p>
          <button
            onClick={() => window.close()}
            className="text-xs text-gray-400 underline hover:text-gray-600"
          >
            Close this window
          </button>
        </div>
      )}

      <p className="text-xs text-gray-300 mt-auto pb-4">Made with IBM Bob</p>
    </div>
  );
}

// ── Page export (Suspense boundary required by Next.js for useSearchParams) ───

export default function YouTubeCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <span className="animate-spin inline-block w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full" />
        </div>
      }
    >
      <CallbackInner />
    </Suspense>
  );
}
