import { Play, Camera, Music2, Briefcase, AtSign, Ghost } from 'lucide-react'

const platforms = [
  { label: 'YouTube', icon: Play },
  { label: 'Instagram', icon: Camera },
  { label: 'TikTok', icon: Music2 },
  { label: 'LinkedIn', icon: Briefcase },
  { label: 'X', icon: AtSign },
  { label: 'Snapchat', icon: Ghost },
]

const metrics = [
  { value: '10x', label: 'Faster Production' },
  { value: '3.5x', label: 'CTR Lift' },
  { value: '50M+', label: 'Clips Repurposed' },
]

export function SocialProof() {
  return (
    <section className="border-y border-border/60 bg-card/30">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <p className="text-center text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
          Publish everywhere your audience is
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-10 gap-y-6">
          {platforms.map((platform) => {
            const Icon = platform.icon
            return (
              <div
                key={platform.label}
                className="flex items-center gap-2 text-muted-foreground transition-colors hover:text-foreground"
              >
                <Icon className="size-5" aria-hidden="true" />
                <span className="text-sm font-medium">{platform.label}</span>
              </div>
            )
          })}
        </div>

        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="flex flex-col items-center gap-1 rounded-2xl border border-border bg-background/50 py-8"
            >
              <span className="text-4xl font-bold tracking-tight text-brand">{metric.value}</span>
              <span className="text-sm text-muted-foreground">{metric.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
