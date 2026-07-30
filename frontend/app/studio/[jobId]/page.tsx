"use client";

import { use, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useJobPolling } from "@/hooks/useJobPolling";
import {
  analyzeVideo,
  processClips,
  getAnalysis,
  getClipStreamUrl,
} from "@/lib/api";
import { GraniteAnalysis, ViralClip } from "@/lib/types";
import { ProcessingProgress } from "@/components/upload/ProcessingProgress";
import { VideoPreviewPlayer } from "@/components/studio/VideoPreviewPlayer";
import { GraniteInspectorPanel } from "@/components/studio/GraniteInspectorPanel";
import { ClipTimeline } from "@/components/studio/ClipTimeline";
import { PlatformOutputTabs } from "@/components/studio/PlatformOutputTabs";
import { YouTubePublishModal } from "@/components/studio/YouTubePublishModal";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface Props {
  params: Promise<{ jobId: string }>;
}

export default function StudioPage({ params }: Props) {
  const { jobId } = use(params);
  const router = useRouter();

  const { job, error: pollError } = useJobPolling(jobId);

  const [analysis, setAnalysis] = useState<GraniteAnalysis | null>(null);
  const [activeRank, setActiveRank] = useState(1);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [showPublishModal, setShowPublishModal] = useState(false);

  // Refs prevent double-firing in React strict mode / re-renders
  const analyzeStarted   = useRef(false);
  const processStarted   = useRef(false);
  const analysisLoaded   = useRef(false);

  // ── Stage 1 → 2: Transcription done → kick off Granite analysis ───────────
  useEffect(() => {
    if (job?.status !== "ANALYZING") return;
    if (analyzeStarted.current) return;
    analyzeStarted.current = true;
    analyzeVideo(jobId).catch((e) => {
      setPipelineError(`Analysis failed: ${e.message}`);
    });
  }, [job, jobId]);

  // ── Stage 2 → 3: Analysis done → fetch analysis JSON + kick off FFmpeg ────
  useEffect(() => {
    if (job?.status !== "PROCESSING") return;

    if (!analysisLoaded.current) {
      analysisLoaded.current = true;
      getAnalysis(jobId)
        .then((a) => setAnalysis(a))
        .catch(() => {
          setTimeout(() => {
            getAnalysis(jobId)
              .then((a) => setAnalysis(a))
              .catch((e) => setPipelineError(`Could not load analysis: ${e.message}`));
          }, 2000);
        });
    }

    if (!processStarted.current) {
      processStarted.current = true;
      processClips(jobId, []).catch((e) => {
        setPipelineError(`Clip rendering failed: ${e.message}`);
      });
    }
  }, [job, jobId]);

  // ── Stage 3 done: Load analysis if not loaded yet ─────────────────────────
  useEffect(() => {
    if (job?.status !== "COMPLETE") return;
    if (analysisLoaded.current) return;
    analysisLoaded.current = true;
    getAnalysis(jobId)
      .then((a) => setAnalysis(a))
      .catch((e) => setPipelineError(`Could not load analysis: ${e.message}`));
  }, [job, jobId]);

  // ── Derived state ─────────────────────────────────────────────────────────
  const activeClip: ViralClip | undefined =
    analysis?.clips.find((c) => c.rank === activeRank);

  const showStudio =
    job?.status === "COMPLETE" &&
    (job.clip_paths?.length ?? 0) > 0 &&
    analysis !== null &&
    activeClip !== undefined;

  // ── Not found ─────────────────────────────────────────────────────────────
  if (!job && !pollError) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-brand border-t-transparent" />
        <p className="text-sm text-muted-foreground">Loading job…</p>
      </div>
    );
  }

  if (!job && pollError) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">Job not found or server unreachable.</p>
        <Button onClick={() => router.push("/")}>Go Home</Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl px-6 py-3 flex items-center justify-between">
        <button
          onClick={() => router.push("/")}
          className="text-sm text-muted-foreground hover:text-foreground transition"
        >
          ← Back
        </button>
        <h1 className="text-sm font-semibold text-foreground truncate max-w-xs">
          Studio · <span className="font-mono text-xs text-muted-foreground">{jobId.slice(0, 8)}…</span>
        </h1>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">

        {/* Pipeline / API error */}
        {(pipelineError || pollError) && (
          <Alert variant="destructive">
            <AlertDescription>
              {pipelineError ?? pollError}
              <Button variant="ghost" size="sm" className="ml-4" onClick={() => router.push("/")}>
                Start over
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Job failed */}
        {job?.status === "FAILED" && (
          <Alert variant="destructive">
            <AlertDescription>
              Processing failed: {job.error_msg ?? "Unknown error"}
              <Button variant="ghost" size="sm" className="ml-4" onClick={() => router.push("/")}>
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* ── IN-PROGRESS: show pipeline steps ── */}
        {!showStudio && job && job.status !== "FAILED" && (
          <div className="flex flex-col items-center gap-6 py-12">
            <h2 className="text-xl font-semibold text-foreground">
              {job.status === "TRANSCRIBING" && "Transcribing your video…"}
              {job.status === "ANALYZING"    && "Analysing with IBM Granite 3.0…"}
              {job.status === "PROCESSING"   && "Rendering 9:16 clips with FFmpeg…"}
              {job.status === "COMPLETE"     && "Finalising…"}
              {job.status === "PENDING"      && "Starting up…"}
            </h2>
            <ProcessingProgress job={job} />
            <p className="text-xs text-muted-foreground">
              This takes 1–3 min depending on video length. Stay on this page.
            </p>
          </div>
        )}

        {/* ── STUDIO: clips ready ── */}
        {showStudio && analysis && activeClip && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-foreground">
              🎬 Your Viral Clips
            </h2>

            {/* Clip selector row */}
            <ClipTimeline
              clips={analysis.clips}
              activeRank={activeRank}
              onSelect={setActiveRank}
            />

            {/* 2-column studio layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
              {/* Left: video + platform tabs */}
              <div className="space-y-4">
                <VideoPreviewPlayer
                  src={getClipStreamUrl(jobId, activeClip.rank)}
                  clipRank={activeClip.rank}
                  downloadFilename={`clip_${activeClip.rank}_${jobId.slice(0, 8)}.mp4`}
                />

                {/* Publish to YouTube Shorts button */}
                <button
                  onClick={() => setShowPublishModal(true)}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 border-red-500 bg-white hover:bg-red-50 transition-colors group"
                >
                  <svg viewBox="0 0 28 20" className="w-5 h-4 flex-shrink-0" fill="none">
                    <rect width="28" height="20" rx="4" fill="#FF0000" />
                    <polygon points="11,5 11,15 20,10" fill="white" />
                  </svg>
                  <span className="text-sm font-semibold text-red-600 group-hover:text-red-700">
                    Publish to YouTube Shorts
                  </span>
                </button>

                <PlatformOutputTabs jobId={jobId} clip={activeClip} />
              </div>

              {/* Right: Granite inspector */}
              <GraniteInspectorPanel clip={activeClip} />
            </div>
          </div>
        )}

        {/* YouTube Publish Modal */}
        {showPublishModal && activeClip && (
          <YouTubePublishModal
            jobId={jobId}
            clip={activeClip}
            onClose={() => setShowPublishModal(false)}
          />
        )}

        {/* Clips rendered but analysis JSON not loaded yet */}
        {job?.status === "COMPLETE" &&
          (job.clip_paths?.length ?? 0) > 0 &&
          !analysis && !pipelineError && (
            <div className="flex flex-col items-center gap-3 py-12 text-muted-foreground">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-brand border-t-transparent" />
              <p className="text-sm text-muted-foreground">Loading analysis results…</p>
            </div>
          )}
      </main>
    </div>
  );
}
