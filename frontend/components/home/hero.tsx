import Image from 'next/image'
import Link from 'next/link'
import { Play, Sparkles, Crosshair } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* subtle glow */}
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
              render={<Link href="/#suite" />}
              nativeButton={false}
              size="lg"
              variant="outline"
              className="border-border bg-transparent text-foreground hover:bg-secondary"
            >
              <Play className="size-4" aria-hidden="true" />
              Watch Demo
            </Button>
          </div>
        </div>

        {/* Right — video player */}
        <div className="relative">
          <div className="relative overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
            <div className="relative aspect-video">
              <Image
                src="/hero-montage.png"
                alt="Montage of creative work including video editing and digital art"
                fill
                priority
                className="object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/60 via-transparent to-transparent" />

              {/* play button */}
              <button
                type="button"
                aria-label="Play showreel"
                className="absolute left-1/2 top-1/2 flex size-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-brand/90 text-brand-foreground shadow-[0_0_40px_-4px] shadow-brand transition-transform hover:scale-105"
              >
                <Play className="ml-1 size-6" aria-hidden="true" />
              </button>

              {/* target overlay */}
              <div className="absolute right-6 top-6 flex flex-col items-end gap-2">
                <div className="relative flex size-20 items-center justify-center">
                  <div className="absolute inset-0 rounded-md border-2 border-brand/70" />
                  <div className="absolute inset-0 rounded-md border-2 border-brand/70 [clip-path:polygon(0_0,30%_0,30%_8%,8%_8%,8%_30%,0_30%)]" />
                  <Crosshair className="size-6 text-brand" aria-hidden="true" />
                </div>
                <span className="rounded-md bg-background/80 px-2 py-1 font-mono text-[10px] tracking-widest text-brand backdrop-blur">
                  CREATOR INSIGHTS ACTIVE
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
