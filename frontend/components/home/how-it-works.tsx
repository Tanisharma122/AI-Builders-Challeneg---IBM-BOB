import { Upload, Wand2, Send } from 'lucide-react'

const steps = [
  {
    step: '01',
    icon: Upload,
    title: 'Upload & Connect',
    desc: 'Import long-form videos or scripts and connect your social channels in seconds.',
  },
  {
    step: '02',
    icon: Wand2,
    title: 'Orchestrate & Refine',
    desc: 'AI agents extract highlights, refine visual prompts, and render on-brand variants.',
  },
  {
    step: '03',
    icon: Send,
    title: 'Publish & Scale',
    desc: 'Export high-res assets or schedule automated cross-platform distribution.',
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-y border-border/60 bg-card/30">
      <div className="mx-auto max-w-7xl px-6 py-20 lg:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">How it works</p>
          <h2 className="mt-4 text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            From raw footage to published in three steps.
          </h2>
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-3">
          {steps.map((item) => {
            const Icon = item.icon
            return (
              <div
                key={item.step}
                className="relative flex flex-col gap-4 rounded-2xl border border-border bg-background/60 p-8"
              >
                <span className="absolute right-6 top-6 font-mono text-4xl font-bold text-brand/20">
                  {item.step}
                </span>
                <span className="flex size-12 items-center justify-center rounded-xl border border-brand/40 bg-brand/10 text-brand">
                  <Icon className="size-6" aria-hidden="true" />
                </span>
                <h3 className="text-xl font-semibold text-foreground">{item.title}</h3>
                <p className="text-pretty leading-relaxed text-muted-foreground">{item.desc}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
