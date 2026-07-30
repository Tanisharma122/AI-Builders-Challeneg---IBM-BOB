import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { VideoUploader } from '@/components/upload/VideoUploader'

export default function StudioUploadPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteNav simplified />
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-20 gap-10">
        <div className="text-center max-w-xl">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand mb-3">
            Video Repurposing Engine
          </p>
          <h1 className="text-3xl font-bold text-foreground leading-tight sm:text-4xl">
            Turn any video into viral short-form clips
          </h1>
          <p className="mt-4 text-muted-foreground text-sm leading-relaxed max-w-md mx-auto">
            Upload a video or paste a YouTube URL. IBM Granite 3.0 detects the top 5 viral segments,
            renders 9:16 clips with burned-in captions, and lets you publish to YouTube Shorts in one click.
          </p>
        </div>

        <VideoUploader />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl w-full text-center">
          {[
            { icon: '🎙', title: 'Word-level Transcription', desc: 'Faster-Whisper with karaoke-style captions' },
            { icon: '🧠', title: 'Granite AI Analysis', desc: 'IBM Granite 3.0 scores viral potential 0–100' },
            { icon: '📱', title: '9:16 Smart Reframe', desc: 'FFmpeg crop + subtitle burn-in' },
          ].map((f) => (
            <div key={f.title} className="rounded-xl border border-border bg-card p-4 space-y-1">
              <div className="text-2xl">{f.icon}</div>
              <p className="text-sm font-semibold text-foreground">{f.title}</p>
              <p className="text-xs text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
