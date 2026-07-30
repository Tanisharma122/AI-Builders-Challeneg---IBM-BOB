import Link from 'next/link'
import { Scissors, ImageIcon, LayoutTemplate } from 'lucide-react'

const nodes = [
  {
    label: 'Video Clipping',
    desc: 'Turn long-form into viral shorts.',
    href: '/features/video-clipping',
    icon: Scissors,
  },
  {
    label: 'Text-to-Image',
    desc: 'Generate B-roll assets on the fly.',
    href: '/features/text-to-image',
    icon: ImageIcon,
  },
  {
    label: 'Thumbnail Gen',
    desc: 'High-CTR thumbnails, instantly.',
    href: '/features/thumbnail-generator',
    icon: LayoutTemplate,
  },
]

export function FeatureSuite() {
  return (
    <section id="suite" className="mx-auto max-w-7xl px-6 py-20 lg:py-28">
      <div className="mx-auto max-w-3xl text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">
          Integrated Creative Platform
        </p>
        <h2 className="mt-4 text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-5xl">
          A fully integrated suite of products, powered by AI.
        </h2>
      </div>

      <div className="relative mt-16 overflow-hidden rounded-3xl border border-border bg-card px-6 py-16 sm:px-12">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute left-1/2 top-10 h-64 w-64 -translate-x-1/2 rounded-full bg-brand/15 blur-[100px]"
        />

        {/* Central hub */}
        <div className="relative flex flex-col items-center">
          <div className="relative flex size-24 items-center justify-center rounded-2xl bg-brand text-4xl font-bold text-brand-foreground shadow-[0_0_50px_-6px] shadow-brand">
            C
          </div>

          {/* connector lines */}
          <div className="relative mt-0 hidden h-16 w-full max-w-3xl md:block">
            <svg className="h-full w-full" viewBox="0 0 600 64" fill="none" preserveAspectRatio="none">
              <path d="M300 0 L300 20 L110 20 L110 64" stroke="currentColor" className="text-brand/50" strokeWidth="1.5" />
              <path d="M300 0 L300 64" stroke="currentColor" className="text-brand/50" strokeWidth="1.5" />
              <path d="M300 0 L300 20 L490 20 L490 64" stroke="currentColor" className="text-brand/50" strokeWidth="1.5" />
            </svg>
          </div>

          {/* Nodes */}
          <div className="mt-8 grid w-full max-w-3xl gap-6 md:mt-0 md:grid-cols-3">
            {nodes.map((node) => {
              const Icon = node.icon
              return (
                <Link
                  key={node.label}
                  href={node.href}
                  className="group flex flex-col items-center gap-3 rounded-xl border border-brand/40 bg-background/60 p-6 text-center shadow-[0_0_24px_-10px] shadow-brand/50 transition-all hover:border-brand hover:shadow-brand/70"
                >
                  <span className="flex size-12 items-center justify-center rounded-lg border border-brand/50 bg-brand/10 text-brand transition-colors group-hover:bg-brand/20">
                    <Icon className="size-6" aria-hidden="true" />
                  </span>
                  <span className="font-semibold text-foreground">{node.label}</span>
                  <span className="text-sm text-muted-foreground">{node.desc}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
