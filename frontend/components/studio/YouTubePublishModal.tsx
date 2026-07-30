"use client";

/**
 * YouTubePublishModal
 * -------------------
 * Full publish flow in a single modal:
 *  1. Authenticate with Google OAuth (popup window).
 *  2. Load AI-generated title / description / tag suggestions from the backend.
 *  3. Let the user pick or edit title, description, and tags.
 *  4. Upload to YouTube Shorts with live progress feedback.
 *  5. Show the live Shorts URL on success.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  exchangeYouTubeCode,
  getYouTubeAuthUrl,
  getYouTubeSuggestions,
  publishToYouTube,
} from "@/lib/api";
import { ViralClip, YouTubeSuggestions, YouTubeTokenData } from "@/lib/types";

// ── Storage key for persisting token across page reloads ─────────────────────
const TOKEN_STORAGE_KEY = "yt_token_data";

function loadStoredToken(): YouTubeTokenData | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as YouTubeTokenData) : null;
  } catch {
    return null;
  }
}

function saveToken(token: YouTubeTokenData) {
  try {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(token));
  } catch {
    /* storage full — ignore */
  }
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface Props {
  jobId: string;
  clip: ViralClip;
  onClose: () => void;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function YouTubePublishModal({ jobId, clip, onClose }: Props) {
  // ── Auth state ───────────────────────────────────────────────────────────
  const [tokenData, setTokenData] = useState<YouTubeTokenData | null>(
    () => loadStoredToken()
  );
  const [authLoading, setAuthLoading] = useState(false);
  const oauthPopup = useRef<Window | null>(null);

  // ── Suggestions state ────────────────────────────────────────────────────
  const [suggestions, setSuggestions] = useState<YouTubeSuggestions | null>(null);
  const [suggestLoading, setSuggestLoading] = useState(false);

  // ── Form state ───────────────────────────────────────────────────────────
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");

  // ── Upload state ─────────────────────────────────────────────────────────
  const [uploading, setUploading] = useState(false);
  const [shortsUrl, setShortsUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Step tracker ─────────────────────────────────────────────────────────
  // "auth" → "suggest" → "form" → "uploading" → "done"
  const step = shortsUrl
    ? "done"
    : uploading
    ? "uploading"
    : !tokenData
    ? "auth"
    : !suggestions
    ? "suggest"
    : "form";

  // ── Load suggestions once authenticated ──────────────────────────────────
  useEffect(() => {
    if (!tokenData || suggestions) return;
    setSuggestLoading(true);
    setError(null);
    getYouTubeSuggestions(
      clip.hook_text,
      clip.script_commentary,
      clip.virality_score
    )
      .then((s) => {
        setSuggestions(s);
        // Pre-populate form with first suggestion
        setTitle(s.title_suggestions[0] ?? clip.hook_text);
        setDescription(s.description_suggestions[0] ?? "");
        setTags(s.viral_tags.slice(0, 15));
      })
      .catch((e) => setError(`Could not load suggestions: ${e.message}`))
      .finally(() => setSuggestLoading(false));
  }, [tokenData, suggestions, clip]);

  // ── OAuth popup flow ─────────────────────────────────────────────────────
  const handleAuth = useCallback(async () => {
    setAuthLoading(true);
    setError(null);
    try {
      const authUrl = await getYouTubeAuthUrl();

      // Open OAuth consent screen in a popup (600×700)
      const popup = window.open(
        authUrl,
        "youtube_oauth",
        "width=600,height=700,scrollbars=yes,resizable=yes"
      );
      oauthPopup.current = popup;

      // Poll until popup closes or sends message
      const poll = setInterval(() => {
        if (!popup || popup.closed) {
          clearInterval(poll);
          setAuthLoading(false);
        }
      }, 500);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`Auth failed: ${msg}`);
      setAuthLoading(false);
    }
  }, []);

  // Listen for the OAuth callback message posted from the callback page
  useEffect(() => {
    const handler = async (event: MessageEvent) => {
      if (event.data?.type !== "youtube_oauth_callback") return;
      const code: string = event.data.code;
      if (!code) return;
      try {
        const token = await exchangeYouTubeCode(code);
        saveToken(token);
        setTokenData(token);
        oauthPopup.current?.close();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        setError(`Token exchange failed: ${msg}`);
      } finally {
        setAuthLoading(false);
      }
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, []);

  // ── Tag helpers ──────────────────────────────────────────────────────────
  const addTag = () => {
    const t = tagInput.trim().replace(/^#/, "");
    if (t && !tags.includes(t)) setTags((prev) => [...prev, t]);
    setTagInput("");
  };

  const removeTag = (tag: string) =>
    setTags((prev) => prev.filter((t) => t !== tag));

  // ── Upload ───────────────────────────────────────────────────────────────
  const handlePublish = async () => {
    if (!tokenData) return;
    setUploading(true);
    setError(null);
    try {
      const result = await publishToYouTube({
        job_id: jobId,
        clip_rank: clip.rank,
        title,
        description,
        tags,
        token_data: tokenData,
      });
      setShortsUrl(result.shorts_url);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      // Expired token: clear and re-auth
      if (msg.toLowerCase().includes("expired") || msg.includes("401")) {
        sessionStorage.removeItem(TOKEN_STORAGE_KEY);
        setTokenData(null);
        setSuggestions(null);
        setError("Session expired. Please re-authenticate with YouTube.");
      } else {
        setError(`Upload failed: ${msg}`);
      }
    } finally {
      setUploading(false);
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-lg max-h-[92vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            {/* YouTube logo SVG */}
            <svg viewBox="0 0 28 20" className="w-7 h-5" fill="none">
              <rect width="28" height="20" rx="4" fill="#FF0000" />
              <polygon points="11,5 11,15 20,10" fill="white" />
            </svg>
            <span className="font-semibold text-foreground text-sm">
              Publish to YouTube Shorts
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* ── Error banner ─────────────────────────────────────────────── */}
          {error && (
            <Alert variant="destructive" className="py-2">
              <AlertDescription className="text-xs">{error}</AlertDescription>
            </Alert>
          )}

          {/* ── STEP: auth ──────────────────────────────────────────────── */}
          {step === "auth" && (
            <div className="flex flex-col items-center gap-4 py-6 text-center">
              <svg viewBox="0 0 28 20" className="w-16 h-12" fill="none">
                <rect width="28" height="20" rx="4" fill="#FF0000" />
                <polygon points="11,5 11,15 20,10" fill="white" />
              </svg>
              <p className="text-sm text-muted-foreground max-w-xs">
                Connect your YouTube account to publish this clip directly as
                a YouTube Short.
              </p>
              <Button
                onClick={handleAuth}
                disabled={authLoading}
                className="bg-red-600 hover:bg-red-700 text-white px-6"
              >
                {authLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    Opening Google…
                  </span>
                ) : (
                  "Sign in with Google"
                )}
              </Button>
              <p className="text-xs text-muted-foreground">
                A popup will open for Google account selection.
              </p>
            </div>
          )}

          {/* ── STEP: suggest (loading) ──────────────────────────────────── */}
          {step === "suggest" && (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <span className="animate-spin inline-block w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full" />
              <p className="text-sm text-muted-foreground">
                Generating AI title &amp; description suggestions…
              </p>
            </div>
          )}

          {/* ── STEP: form ───────────────────────────────────────────────── */}
          {step === "form" && suggestions && (
            <div className="space-y-5">
              {/* Connected badge */}
              <div className="flex items-center gap-2 text-xs text-green-400 bg-green-950/40 border border-green-800/60 rounded-lg px-3 py-2">
                <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                YouTube account connected
                <button
                  className="ml-auto text-muted-foreground hover:text-foreground underline text-xs"
                  onClick={() => {
                    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
                    setTokenData(null);
                    setSuggestions(null);
                  }}
                >
                  Disconnect
                </button>
              </div>

              {/* Title */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Title <span className="text-muted-foreground font-normal">(max 100 chars)</span>
                </label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  maxLength={100}
                  placeholder="Enter video title…"
                  className="text-sm bg-input text-foreground border-border placeholder:text-muted-foreground"
                />
                <p className="text-xs text-muted-foreground">
                  {100 - title.length} characters left · #Shorts will be appended automatically
                </p>
                {/* Title suggestions */}
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {suggestions.title_suggestions.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => setTitle(s.replace(/ #Shorts$/, ""))}
                      className="text-xs bg-secondary text-foreground hover:bg-brand/20 hover:text-brand border border-border hover:border-brand/50 rounded-full px-2.5 py-1 transition-colors text-left"
                    >
                      {s.length > 55 ? s.slice(0, 52) + "…" : s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Description */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  maxLength={5000}
                  rows={5}
                  placeholder="Write a description…"
                  className="w-full text-sm bg-input text-foreground border border-border rounded-lg px-3 py-2 resize-none placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand/50"
                />
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">AI suggestions — click to use:</p>
                  {suggestions.description_suggestions.map((d, i) => (
                    <button
                      key={i}
                      onClick={() => setDescription(d)}
                      className="w-full text-left text-xs bg-secondary text-foreground hover:bg-brand/20 hover:text-brand border border-border hover:border-brand/50 rounded-lg px-3 py-2 truncate transition-colors"
                    >
                      {d.slice(0, 80).replace(/\n/g, " ")}…
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Tags{" "}
                  <span className="text-muted-foreground font-normal">
                    ({tags.length} added · viral tags pre-loaded)
                  </span>
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {tags.map((t) => (
                    <Badge
                      key={t}
                      variant="secondary"
                      className="text-xs cursor-pointer bg-secondary text-foreground border-border hover:bg-destructive/20 hover:text-destructive"
                      onClick={() => removeTag(t)}
                    >
                      #{t} ×
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addTag(); } }}
                    placeholder="Add a custom tag…"
                    className="text-sm flex-1 bg-input text-foreground border-border placeholder:text-muted-foreground"
                  />
                  <Button variant="outline" size="sm" onClick={addTag}>
                    Add
                  </Button>
                </div>
              </div>

              {/* Publish button */}
              <Button
                onClick={handlePublish}
                disabled={!title.trim() || uploading}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold"
              >
                Publish to YouTube Shorts
              </Button>
            </div>
          )}

          {/* ── STEP: uploading ───────────────────────────────────────────── */}
          {step === "uploading" && (
            <div className="flex flex-col items-center gap-4 py-8 text-center">
              <span className="animate-spin inline-block w-10 h-10 border-4 border-red-500 border-t-transparent rounded-full" />
              <p className="text-sm font-medium text-foreground">
                Uploading to YouTube…
              </p>
              <p className="text-xs text-muted-foreground max-w-xs">
                Large files may take a few minutes. Please keep this window open.
              </p>
            </div>
          )}

          {/* ── STEP: done ───────────────────────────────────────────────── */}
          {step === "done" && shortsUrl && (
            <div className="flex flex-col items-center gap-4 py-6 text-center">
              <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center text-3xl">
                ✓
              </div>
              <p className="text-sm font-semibold text-gray-800">
                Published successfully!
              </p>
              <a
                href={shortsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-red-600 hover:text-red-700 font-medium text-sm underline break-all"
              >
                {shortsUrl}
              </a>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigator.clipboard.writeText(shortsUrl)}
                >
                  Copy Link
                </Button>
                <Button size="sm" onClick={onClose}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
