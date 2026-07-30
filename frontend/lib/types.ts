/**
 * TypeScript interfaces mirroring the backend Pydantic models exactly.
 * Keep in sync with:
 *   backend/app/models/transcript.py
 *   backend/app/models/granite_output.py
 *   backend/app/models/job.py
 */

// ── Transcript ────────────────────────────────────────────────────────────────

export interface TranscriptWord {
  word: string;
  start_time: number;
  end_time: number;
  probability: number;
}

export interface TranscriptSegment {
  id: number;
  text: string;
  start_time: number;
  end_time: number;
  words: TranscriptWord[];
}

export interface FullTranscript {
  job_id: string;
  language: string;
  duration: number;
  segments: TranscriptSegment[];
}

// ── Granite Analysis ──────────────────────────────────────────────────────────

export interface ViralClip {
  rank: number;
  start_time: number;
  end_time: number;
  hook_text: string;
  script_commentary: string;
  virality_score: number; // 0–100
  virality_reasoning: string;
}

export interface GraniteAnalysis {
  job_id: string;
  clips: ViralClip[];
  model_used: string;
  tokens_used: number;
}

// ── Job ───────────────────────────────────────────────────────────────────────

export type JobStatus =
  | "PENDING"
  | "TRANSCRIBING"
  | "ANALYZING"
  | "PROCESSING"
  | "COMPLETE"
  | "FAILED";

export interface ProcessingJob {
  job_id: string;
  status: JobStatus;
  progress_pct: number;
  error_msg: string | null;
  created_at: string;
  updated_at: string;
  source_filename: string | null;
  youtube_url: string | null;
  clip_paths: string[];
}

// ── API helpers ───────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ── Platform metadata ─────────────────────────────────────────────────────────

export type Platform = "youtube_shorts" | "instagram_reels" | "linkedin" | "x";

export interface PlatformMeta {
  id: Platform;
  label: string;
  aspectRatio: string;
  maxDurationSec: number;
  maxHookChars: number;
  warning?: string;
}

export const PLATFORM_META: PlatformMeta[] = [
  {
    id: "youtube_shorts",
    label: "YouTube Shorts",
    aspectRatio: "9:16",
    maxDurationSec: 60,
    maxHookChars: 100,
  },
  {
    id: "instagram_reels",
    label: "Instagram Reels",
    aspectRatio: "9:16",
    maxDurationSec: 90,
    maxHookChars: 2200,
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    aspectRatio: "1:1 or 16:9",
    maxDurationSec: 600,
    maxHookChars: 700,
    warning: "LinkedIn recommends square or landscape video. Vertical clips may be letter-boxed.",
  },
  {
    id: "x",
    label: "X (Twitter)",
    aspectRatio: "9:16",
    maxDurationSec: 140,
    maxHookChars: 280,
  },
];

// ── YouTube Publishing ────────────────────────────────────────────────────────

/** OAuth token data returned by /api/auth/youtube/callback */
export interface YouTubeTokenData {
  access_token: string;
  refresh_token: string | null;
  token_uri: string;
  client_id: string;
  client_secret: string;
  scopes: string[];
}

/** Body sent to POST /api/publish/youtube */
export interface YouTubePublishRequest {
  job_id: string;
  clip_rank: number;
  title: string;
  description: string;
  tags: string[];
  token_data: YouTubeTokenData;
  category_id?: string;
}

/** Response from POST /api/publish/youtube */
export interface YouTubePublishResult {
  shorts_url: string;
  job_id: string;
  clip_rank: number;
}

/** Response from POST /api/publish/youtube/suggest */
export interface YouTubeSuggestions {
  title_suggestions: string[];
  description_suggestions: string[];
  viral_tags: string[];
}
