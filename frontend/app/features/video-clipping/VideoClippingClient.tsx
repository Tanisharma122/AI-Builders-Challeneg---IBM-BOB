'use client'

import Image from 'next/image'
import Link from 'next/link'
import { Play, Repeat, TrendingUp, Flame } from 'lucide-react'
import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { FeatureSubmenu } from '@/components/feature-submenu'
import { FeatureSection } from '@/components/features/feature-section'

function VideoClippingVisual() {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
      <div className="relative aspect-video bg-card">
        {/* Gradient background fallback — no onError handler needed */}
        <div className="absolute inset-0 bg-gradient-to-br from-brand/20 via-card to-background" />

        {/* Play button */}
        <button
          type="button"
          aria-label="Play clip"
          className="absolute left-1/2 top-1/2 flex size-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-brand/90 text-brand-foreground shadow-[0_0_36px_-4px] shadow-brand transition-transform hover:scale-105"
        >
          <Play className="ml-1 size-5" aria-hidden="true" />
        </button>

        {/* Host badge */}
        <div className="absolute left-4 top-4 flex items-center gap-3 rounded-xl border border-border bg-background/70 px-3 py-2 backdrop-blur-md">
          <span className="flex size-9 items-center justify-center rounded-full bg-brand text-sm font-semibold text-brand-foreground">
            JB
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-foreground">John Bright</p>
            <p className="text-xs text-muted-foreground">Host</p>
          </div>
        </div>

        {/* Virality card */}
        <div className="absolute bottom-4 left-4 w-56 space-y-3 rounded-xl border border-brand/40 bg-background/80 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-xs text-muted-foreground">
              <TrendingUp className="size-4 text-brand" aria-hidden="true" />
              Virality Score
            </span>
            <span className="text-sm font-bold text-brand">88%</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
            <div className="h-full w-[88%] rounded-full bg-brand" />
          </div>
          <div className="flex items-center justify-between border-t border-border pt-3">
            <span className="flex items-center gap-2 text-xs text-muted-foreground">
              <Flame className="size-4 text-brand" aria-hidden="true" />
              Viral Hooks
            </span>
            <span className="text-sm font-bold text-foreground">5</span>
          </div>
        </div>

        {/* Clip badges */}
        <div className="absolute right-4 top-4 flex flex-col gap-2">
          {['Hook #1', 'Hook #2', 'Hook #3'].map((label, i) => (
            <span
              key={label}
              className="rounded-lg border border-brand/40 bg-background/80 px-2 py-1 text-xs font-semibold text-brand backdrop-blur-md"
              style={{ opacity: 1 - i * 0.2 }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function VideoClippingClient() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteNav simplified />
      <FeatureSubmenu active="/features/video-clipping" />
      <main className="flex-1">
        <FeatureSection
          eyebrow="Video Repurposing Engine"
          eyebrowIcon={Repeat}
          headline="Identify high-engagement segments to create viral shorts and reels."
          subtext="Analyze long-form video, generate metadata (titles, tags, descriptions), and distribute to YouTube, Instagram, TikTok, and LinkedIn in one click."
          ctaLabel="Launch Studio →"
          ctaHref="/studio-upload"
          visual={<VideoClippingVisual />}
        />

        {/* Feature pills */}
        <div className="mx-auto max-w-7xl px-6 pb-12">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 mb-12">
            {[
              { icon: '🎙', label: 'Word-level Transcription' },
              { icon: '🧠', label: 'IBM Granite 3.0 Analysis' },
              { icon: '📱', label: '9:16 Smart Reframe' },
              { icon: '▶', label: 'YouTube Shorts Publish' },
            ].map((f) => (
              <div key={f.label} className="flex items-center gap-2 rounded-xl border border-border bg-card/60 px-3 py-3 text-sm text-muted-foreground">
                <span>{f.icon}</span>
                <span>{f.label}</span>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="rounded-2xl border border-brand/30 bg-card/60 p-8 text-center">
            <p className="text-xs font-semibold uppercase tracking-widest text-brand mb-3">Ready to clip?</p>
            <h2 className="text-2xl font-bold text-foreground mb-4">Upload your video and get viral clips in minutes</h2>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto text-sm">
              IBM Granite 3.0 detects the top 5 viral moments, renders 9:16 clips with burned-in captions,
              and lets you publish to YouTube Shorts in one click.
            </p>
            <Link
              href="/studio-upload"
              className="inline-flex items-center justify-center rounded-lg bg-brand px-6 py-3 text-sm font-semibold text-brand-foreground shadow-[0_0_24px_-6px] shadow-brand/70 transition-colors hover:bg-brand/90"
            >
              Start Clipping →
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
