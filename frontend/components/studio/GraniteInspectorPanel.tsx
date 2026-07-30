"use client";

import { useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { ScoreGauge } from "@/components/shared/ScoreGauge";
import { ViralClip } from "@/lib/types";

interface Props {
  clip: ViralClip;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function GraniteInspectorPanel({ clip }: Props) {
  const [copied, setCopied] = useState(false);

  const copyHook = async () => {
    await navigator.clipboard.writeText(clip.hook_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-5 w-full">

      {/* Hook Text */}
      <div className="rounded-xl border border-border bg-card p-4 space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Hook Text</p>
        <p className="text-lg font-bold leading-tight text-foreground">{clip.hook_text}</p>
        <button
          onClick={copyHook}
          className="text-xs text-brand hover:text-brand/80 hover:underline transition"
        >
          {copied ? "✓ Copied!" : "Copy to clipboard"}
        </button>
      </div>

      {/* Script Commentary */}
      <div className="rounded-xl border border-border bg-card p-4 space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Script Commentary</p>
        <ScrollArea className="h-28">
          <p className="text-sm text-foreground leading-relaxed pr-3">{clip.script_commentary}</p>
        </ScrollArea>
      </div>

      {/* Virality Score */}
      <div className="rounded-xl border border-border bg-card p-4 space-y-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Virality Score</p>
        <div className="flex items-start gap-4">
          <ScoreGauge score={clip.virality_score} />
          <p className="text-xs text-muted-foreground leading-relaxed flex-1">{clip.virality_reasoning}</p>
        </div>
      </div>

      {/* Timestamps */}
      <div className="rounded-xl border border-border bg-card p-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Timestamps</p>
          <p className="mt-1 text-sm font-mono text-foreground">
            {formatTime(clip.start_time)} → {formatTime(clip.end_time)}
          </p>
        </div>
        <Badge variant="secondary" className="bg-secondary text-foreground border-border">
          {(clip.end_time - clip.start_time).toFixed(0)}s
        </Badge>
      </div>
    </div>
  );
}
