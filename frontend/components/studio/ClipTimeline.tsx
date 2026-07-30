"use client";

import { ViralClip } from "@/lib/types";

interface Props {
  clips: ViralClip[];
  activeRank: number;
  onSelect: (rank: number) => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function scoreColour(score: number): string {
  if (score > 70) return "bg-green-900/50 text-green-400";
  if (score > 40) return "bg-amber-900/50 text-amber-400";
  return "bg-red-900/50 text-red-400";
}

export function ClipTimeline({ clips, activeRank, onSelect }: Props) {
  return (
    <div className="w-full overflow-x-auto">
      <div className="flex gap-3 pb-2 min-w-max">
        {clips.map((clip) => {
          const isActive = clip.rank === activeRank;
          const duration = (clip.end_time - clip.start_time).toFixed(0);
          return (
            <button
              key={clip.rank}
              onClick={() => onSelect(clip.rank)}
              className={`flex flex-col gap-1.5 p-3 rounded-xl border-2 w-44 text-left transition-all shrink-0 ${
                isActive
                  ? "border-brand bg-brand/10 shadow-[0_0_16px_-6px] shadow-brand/60"
                  : "border-border bg-card hover:border-brand/50 hover:bg-card/80"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-muted-foreground">#{clip.rank}</span>
                <span className="text-xs text-muted-foreground">{duration}s</span>
              </div>

              <p className="text-xs font-medium text-foreground line-clamp-2 leading-tight">
                {clip.hook_text}
              </p>

              <div className="flex items-center justify-between mt-auto pt-1">
                <span className="text-xs text-muted-foreground font-mono">
                  {formatTime(clip.start_time)} – {formatTime(clip.end_time)}
                </span>
                <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full ${scoreColour(clip.virality_score)}`}>
                  {clip.virality_score}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
