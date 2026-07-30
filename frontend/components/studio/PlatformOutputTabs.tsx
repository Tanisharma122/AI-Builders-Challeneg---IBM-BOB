"use client";

import { useCallback, useRef } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getClipDownloadUrl } from "@/lib/api";
import { PLATFORM_META, Platform, ViralClip } from "@/lib/types";

interface Props {
  jobId: string;
  clip: ViralClip;
}

export function PlatformOutputTabs({ jobId, clip }: Props) {
  // Debounce map: platformId → last-clicked timestamp
  const lastClick = useRef<Record<string, number>>({});

  const handleDownload = useCallback((platform: Platform) => {
    const now = Date.now();
    if (now - (lastClick.current[platform] ?? 0) < 500) return; // debounce 500ms
    lastClick.current[platform] = now;
    const url = getClipDownloadUrl(jobId, clip.rank, platform);
    window.open(url, "_blank");
  }, [jobId, clip.rank]);

  const hookOver = (limit: number) => clip.hook_text.length > limit;

  return (
    <Tabs defaultValue="youtube_shorts">
      <TabsList className="w-full grid grid-cols-4 h-auto">
        {PLATFORM_META.map((p) => (
          <TabsTrigger key={p.id} value={p.id} className="text-xs py-1.5 px-1">
            {p.label.split(" ")[0]}
          </TabsTrigger>
        ))}
      </TabsList>

      {PLATFORM_META.map((p) => (
        <TabsContent key={p.id} value={p.id}>
          <div className="mt-3 rounded-xl border p-4 space-y-3">
            {/* Metadata row */}
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">{p.aspectRatio}</Badge>
              <Badge variant="secondary">Max {p.maxDurationSec}s</Badge>
              <Badge variant="secondary">{p.maxHookChars} chars</Badge>
            </div>

            {/* Duration warning */}
            {clip.end_time - clip.start_time > p.maxDurationSec && (
              <Alert variant="destructive" className="py-2">
                <AlertDescription className="text-xs">
                  Clip duration ({(clip.end_time - clip.start_time).toFixed(0)}s) exceeds {p.label}&apos;s {p.maxDurationSec}s limit.
                </AlertDescription>
              </Alert>
            )}

            {/* Hook length warning */}
            {hookOver(p.maxHookChars) && (
              <Alert variant="destructive" className="py-2">
                <AlertDescription className="text-xs">
                  Hook text ({clip.hook_text.length} chars) exceeds {p.label}&apos;s {p.maxHookChars}-char limit.
                </AlertDescription>
              </Alert>
            )}

            {/* Platform-specific advisory */}
            {p.warning && (
              <Alert className="py-2">
                <AlertDescription className="text-xs text-amber-700">{p.warning}</AlertDescription>
              </Alert>
            )}

            {/* Download button */}
            <Button
              className="w-full"
              variant="outline"
              onClick={() => handleDownload(p.id)}
            >
              Download for {p.label}
            </Button>
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
