'use client'

import Link from 'next/link'
import { useRef, useState } from 'react'
import { Play, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

function HeroVideo() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [playing, setPlaying] = useState(false)

  const toggle = () => {
    const v = videoRef.current
    if (!v) return
    if (v.paused) { v.play(); setPlaying(true) }
    else          { v.pause(); setPlaying(false) }
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
      <div className="relative aspect-video bg-black">
        <video
          ref={videoRef}
          src="/intro.mp4"
          className="w-full h-full object-cover rounded-2xl"
          preload="metadata"
          onEnded={() => setPlaying(false)}
          onClick={toggle}
          playsInline
        />

        {/* Gradient overlay — only when paused */}
        {!playing && (
          <div className="absolute inset-0 bg-gradient-to-t from-background/60 via-transparent to-transparent rounded-2xl pointer-events-none" />
        )}

        {/* Play / Pause button */}
        <button
          type="button"
          onClick={toggle}
          aria-label={playing ? 'Pause intro video' : 'Play intro video'}
          className={`absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex size-16 items-center justify-center rounded-full bg-brand/90 text-brand-foreground shadow-[0_0_40px_-4px] shadow-brand transition-all hover:scale-105 ${
            playing ? 'opacity-0 hover:opacity-100' : 'opacity-100'
          }`}
        >
          {playing
            ? <span className="text-2xl leading-none">⏸</span>
            : <Play className="ml-1 size-6" aria-hidden="true" />
          }
        </button>

        {/* Badge */}
        <div className="absolute bottom-4 left-4 rounded-lg border border-brand/40 bg-background/80 px-3 py-1.5 backdrop-blur-md">
          <span className="font-mono text-[10px] tracking-widest text-brand">CREATECT AI — INTRO</span>
        </div>
      </div>
    </div>
  )
}

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-40 left-1/2 h-96 w-[42rem] -translate-x-1/2 rounded-full bg-brand/20 blur-[120px]"
      />
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-20 lg:grid-cols-2 lg:py-28">
        {/* Left */}
        <div className="flex flex-col gap-6">
          <span className="inline-flex w-fit items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-1.5 text-xs font-medium text-muted-foreground">
            <Sparkles className="size-3.5 text-brand" aria-hidden="true" />
            Agentic content orchestration
          </span>
          <h1 className="text-balance text-4xl font-bold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Empowering Next-Gen Creators with Agentic Content Orchestration.
          </h1>
          <p className="max-w-lg text-pretty text-lg leading-relaxed text-muted-foreground">
            One platform to accelerate your ideation, production, and distribution by 80%.
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <Button
              render={<Link href="/#suite" />}
              nativeButton={false}
              size="lg"
              className="bg-brand text-brand-foreground shadow-[0_0_28px_-6px] shadow-brand/70 hover:bg-brand/90"
            >
              Start Creating
            </Button>
            <Button
              render={<Link href="/studio-upload" />}
              nativeButton={false}
              size="lg"
              variant="outline"
              className="border-border bg-transparent text-foreground hover:bg-secondary"
            >
              <Play className="size-4" aria-hidden="true" />
              Try It Now
            </Button>
          </div>
        </div>

        {/* Right — intro video */}
        <div className="relative">
          <HeroVideo />
        </div>
      </div>
    </section>
  )
}
