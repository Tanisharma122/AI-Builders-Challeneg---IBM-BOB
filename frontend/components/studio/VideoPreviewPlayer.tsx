"use client";

import { useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";

interface Props {
  src: string;
  clipRank: number;
  /** Optional: provide jobId + filename for the download button */
  downloadFilename?: string;
}

export function VideoPreviewPlayer({ src, clipRank, downloadFilename }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const togglePlay = () => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) { v.play(); setPlaying(true); }
    else          { v.pause(); setPlaying(false); }
  };

  const handleScrub = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = videoRef.current;
    if (!v) return;
    const t = Number(e.target.value);
    v.currentTime = t;
    setCurrentTime(t);
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col items-center gap-3">
      {/* 9:16 video container */}
      <div className="relative w-full max-w-[280px]" style={{ aspectRatio: "9/16" }}>
        <video
          ref={videoRef}
          src={src}
          preload="metadata"
          className="w-full h-full rounded-xl object-cover bg-black"
          onTimeUpdate={() => setCurrentTime(videoRef.current?.currentTime ?? 0)}
          onLoadedMetadata={() => setDuration(videoRef.current?.duration ?? 0)}
          onEnded={() => setPlaying(false)}
          onClick={togglePlay}
        />
        {/* Rank badge overlay */}
        <Badge className="absolute top-2 left-2 text-xs">
          #{clipRank}
        </Badge>
        {/* Play overlay when paused */}
        {!playing && (
          <button
            onClick={togglePlay}
            className="absolute inset-0 flex items-center justify-center bg-black/20 rounded-xl"
            aria-label="Play"
          >
            <span className="text-white text-5xl">▶</span>
          </button>
        )}
      </div>

      {/* Controls */}
      <div className="w-full max-w-[280px] space-y-1">
        <input
          type="range"
          min={0}
          max={duration || 1}
          step={0.1}
          value={currentTime}
          onChange={handleScrub}
          className="w-full accent-blue-500 cursor-pointer"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
        <div className="flex justify-center gap-2">
          <button
            onClick={togglePlay}
            className="px-4 py-1.5 rounded-lg bg-secondary hover:bg-secondary/80 text-foreground text-sm font-medium transition-colors"
          >
            {playing ? "⏸ Pause" : "▶ Play"}
          </button>
          <a
            href={src}
            download={downloadFilename ?? `clip_${clipRank}.mp4`}
            className="px-4 py-1.5 rounded-lg bg-brand/10 hover:bg-brand/20 text-brand text-sm font-medium transition-colors flex items-center gap-1"
          >
            ↓ Download
          </a>
        </div>
      </div>
    </div>
  );
}
