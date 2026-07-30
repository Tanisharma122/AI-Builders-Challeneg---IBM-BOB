"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { uploadVideo } from "@/lib/api";
import { ApiError } from "@/lib/types";

export function VideoUploader() {
  const router = useRouter();
  const [tab, setTab] = useState<"file" | "url">("file");
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith("video/")) setSelectedFile(file);
    else setError("Please drop a valid video file.");
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    if (file) setSelectedFile(file);
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      const job = await uploadVideo(
        tab === "file" ? selectedFile : null,
        tab === "url" ? youtubeUrl.trim() : null
      );
      router.push(`/studio/${job.job_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const canSubmit =
    !loading && (tab === "file" ? !!selectedFile : youtubeUrl.trim().length > 0);

  return (
    <Card className="w-full max-w-xl mx-auto bg-card border-border">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-foreground">Add Your Video</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={tab} onValueChange={(v) => { setTab(v as "file" | "url"); setError(null); }}>
          <TabsList className="w-full bg-secondary">
            <TabsTrigger value="file" className="flex-1 text-foreground data-[state=active]:bg-background data-[state=active]:text-foreground">Upload File</TabsTrigger>
            <TabsTrigger value="url" className="flex-1 text-foreground data-[state=active]:bg-background data-[state=active]:text-foreground">YouTube URL</TabsTrigger>
          </TabsList>

          {/* File tab */}
          <TabsContent value="file">
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`mt-3 flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-10 cursor-pointer transition-colors ${
                dragOver
                  ? "border-brand bg-brand/10"
                  : "border-border hover:border-brand/60 hover:bg-brand/5"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                className="hidden"
                onChange={handleFileSelect}
              />
              {selectedFile ? (
                <div className="text-center">
                  <p className="font-medium text-sm text-foreground break-all">{selectedFile.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">{formatBytes(selectedFile.size)}</p>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-sm text-foreground">Drag &amp; drop a video file here</p>
                  <p className="text-xs text-muted-foreground mt-1">or click to browse · MP4, MOV, WebM · max 500 MB</p>
                </div>
              )}
            </div>
          </TabsContent>

          {/* URL tab */}
          <TabsContent value="url">
            <div className="mt-3 space-y-2">
              <Input
                type="url"
                placeholder="https://youtube.com/watch?v=..."
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                disabled={loading}
                className="bg-input text-foreground placeholder:text-muted-foreground border-border"
              />
              <p className="text-xs text-muted-foreground">
                Supports youtube.com/watch, youtu.be, and youtube.com/shorts URLs.
              </p>
            </div>
          </TabsContent>
        </Tabs>

        {error && (
          <Alert variant="destructive">
            <AlertDescription className="text-destructive-foreground">{error}</AlertDescription>
          </Alert>
        )}

        <Button
          className="w-full bg-brand text-brand-foreground hover:bg-brand/90 font-semibold"
          disabled={!canSubmit}
          onClick={handleSubmit}
        >
          {loading ? "Uploading…" : "Generate Viral Clips"}
        </Button>
      </CardContent>
    </Card>
  );
}
