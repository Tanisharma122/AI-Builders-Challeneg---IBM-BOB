/**
 * Typed fetch wrappers for all FastAPI backend endpoints.
 *
 * All calls use relative paths (/api/...) so they are routed through the
 * Next.js rewrite proxy defined in next.config.ts.  This avoids CORS issues
 * because the browser only sees one origin (the Next.js dev server on :3000).
 *
 * The NEXT_PUBLIC_API_URL variable is only used server-side (SSR) or in
 * contexts where an absolute URL is genuinely required (e.g. download links
 * opened in a new tab from a server-rendered page).
 */

import {
  ApiError,
  GraniteAnalysis,
  Platform,
  ProcessingJob,
  YouTubePublishRequest,
  YouTubePublishResult,
  YouTubeSuggestions,
} from "./types";

// ── Internal helpers ──────────────────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.ok) return res.json() as Promise<T>;
  let message = `HTTP ${res.status}`;
  try {
    const body = await res.json();
    message = body?.detail ?? body?.message ?? message;
  } catch {
    // ignore parse error; keep generic message
  }
  throw new ApiError(res.status, message);
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Upload a video file OR submit a YouTube URL to start the transcription job.
 * Exactly one of `file` / `youtubeUrl` must be non-null.
 */
export async function uploadVideo(
  file: File | null,
  youtubeUrl: string | null
): Promise<ProcessingJob> {
  const form = new FormData();
  if (file) form.append("file", file);
  if (youtubeUrl) form.append("youtube_url", youtubeUrl);

  const res = await fetch("/api/video/transcribe", {
    method: "POST",
    body: form,
  });
  return handleResponse<ProcessingJob>(res);
}

/** Trigger Granite LLM analysis on a completed transcript. */
export async function analyzeVideo(jobId: string): Promise<ProcessingJob> {
  const res = await fetch("/api/video/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });
  return handleResponse<ProcessingJob>(res);
}

/** Trigger FFmpeg clip rendering (optionally for a subset of ranks). */
export async function processClips(
  jobId: string,
  clipRanks: number[] = []
): Promise<ProcessingJob> {
  const res = await fetch("/api/video/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, clip_ranks: clipRanks }),
  });
  return handleResponse<ProcessingJob>(res);
}

/** Poll the current state of a job. */
export async function getJobStatus(jobId: string): Promise<ProcessingJob> {
  const res = await fetch(`/api/video/status/${jobId}`);
  return handleResponse<ProcessingJob>(res);
}

/** Fetch the Granite analysis result for a job (once PROCESSING or COMPLETE). */
export async function getAnalysis(jobId: string): Promise<GraniteAnalysis> {
  const res = await fetch(`/api/video/analysis/${jobId}`);
  return handleResponse<GraniteAnalysis>(res);
}

/** Build the download URL for a rendered clip. */
export function getClipDownloadUrl(
  jobId: string,
  clipRank: number,
  platform: Platform = "youtube_shorts"
): string {
  return `/api/output/export?job_id=${jobId}&clip=${clipRank}&platform=${platform}`;
}

/** Build a streaming URL for the rendered clip video element. */
export function getClipStreamUrl(jobId: string, clipRank: number): string {
  return `/outputs/${jobId}/clip_${clipRank}.mp4`;
}

// ── YouTube OAuth ─────────────────────────────────────────────────────────────

/** Fetch the Google OAuth consent URL from the backend. */
export async function getYouTubeAuthUrl(): Promise<string> {
  const res = await fetch("/api/auth/youtube/login");
  const data = await handleResponse<{ auth_url: string }>(res);
  return data.auth_url;
}

/**
 * Exchange an OAuth code for tokens.
 * Called automatically when the OAuth popup/redirect lands on the callback URL.
 */
export async function exchangeYouTubeCode(code: string): Promise<import("./types").YouTubeTokenData> {
  const res = await fetch(`/api/auth/youtube/callback?code=${encodeURIComponent(code)}`);
  const data = await handleResponse<{ token_data: import("./types").YouTubeTokenData }>(res);
  return data.token_data;
}

// ── YouTube Publishing ────────────────────────────────────────────────────────

/** Upload a rendered clip to YouTube Shorts. */
export async function publishToYouTube(
  payload: YouTubePublishRequest
): Promise<YouTubePublishResult> {
  const res = await fetch("/api/publish/youtube", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<YouTubePublishResult>(res);
}

/** Generate AI title / description / tag suggestions for a clip. */
export async function getYouTubeSuggestions(
  hookText: string,
  scriptCommentary: string,
  viralityScore: number,
  count: number = 5
): Promise<YouTubeSuggestions> {
  const res = await fetch("/api/publish/youtube/suggest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      hook_text: hookText,
      script_commentary: scriptCommentary,
      virality_score: viralityScore,
      count,
    }),
  });
  return handleResponse<YouTubeSuggestions>(res);
}
