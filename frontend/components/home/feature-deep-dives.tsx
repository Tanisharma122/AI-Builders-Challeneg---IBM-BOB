import Image from 'next/image'
import Link from 'next/link'
import { Scissors, ImageIcon, LayoutTemplate, ArrowRight, Check } from 'lucide-react'

const features = [
  {
    eyebrow: 'Video Repurposing Engine',
    icon: Scissors,
    title: 'AI Video Clipping & social distribution.',
    desc: 'Auto-detect high-engagement hooks, generate contextual metadata, and post to every platform in one click.',
    points: ['Auto hook detection', 'Titles, tags & hashtags', 'One-click multi-platform posting'],
    href: '/features/video-clipping',
    image: '/podcast-host.png',
    imageAlt: 'Podcast host speaking at a desk with virality metrics overlay',
  },
  {
    eyebrow: 'Contextual Asset Engine',
    icon: ImageIcon,
    title: 'Dynamic in-video text-to-image assets.',
    desc: 'Turn a simple prompt into high-resolution B-roll and overlays with LLM-refined style, lighting, and camera direction.',
    points: ['LLM prompt refinement', 'High-resolution output', 'Seamless timeline B-roll'],
    href: '/features/text-to-image',
    image: '/futuristic-city-rain.png',
    imageAlt: 'Generated concept art of a futuristic city in the rain',
  },
  {
    eyebrow: 'High-CTR Design Suite',
    icon: LayoutTemplate,
    title: 'Content-aware YouTube thumbnails.',
    desc: 'Transcript-driven multi-variant thumbnails with predictive CTR scoring so you can A/B test winners instantly.',
    points: ['Transcript-driven themes', 'Multiple variants at once', 'Predictive CTR scoring'],
    href: '/features/thumbnail-generator',
    image: '/thumb-face.png',
    imageAlt: 'High-contrast YouTube thumbnail variant',
  },
]

export function FeatureDeepDives() {
  return (
    <section id="features" className="mx-auto max-w-7xl px-6 py-20 lg:py-28">
      <div className="mx-auto max-w-3xl text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Feature deep dives</p>
        <h2 className="mt-4 text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Every stage of your workflow, orchestrated by AI.
        </h2>
      </div>

      <div className="mt-16 flex flex-col gap-20 lg:gap-28">
        {features.map((feature, index) => {
          const Icon = feature.icon
          const reversed = index % 2 === 1
          return (
            <div
              key={feature.title}
              className="grid items-center gap-10 lg:grid-cols-2 lg:gap-16"
            >
              {/* Text */}
              <div className={reversed ? 'lg:order-2' : ''}>
                <span className="inline-flex items-center gap-2 rounded-full border border-brand/40 bg-brand/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-brand">
                  <Icon className="size-3.5" aria-hidden="true" />
                  {feature.eyebrow}
                </span>
                <h3 className="mt-5 text-balance text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                  {feature.title}
                </h3>
                <p className="mt-4 text-pretty leading-relaxed text-muted-foreground">{feature.desc}</p>
                <ul className="mt-6 flex flex-col gap-3">
                  {feature.points.map((point) => (
                    <li key={point} className="flex items-center gap-3 text-sm text-foreground">
                      <span className="flex size-5 items-center justify-center rounded-full bg-brand/15 text-brand">
                        <Check className="size-3" aria-hidden="true" />
                      </span>
                      {point}
                    </li>
                  ))}
                </ul>
                <Link
                  href={feature.href}
                  className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-brand transition-colors hover:text-brand/80"
                >
                  Explore feature
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </div>

              {/* Visual */}
              <div className={reversed ? 'lg:order-1' : ''}>
                <div className="relative overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
                  <div className="relative aspect-video">
                    <Image src={feature.image} alt={feature.imageAlt} fill className="object-cover" />
                    <div className="absolute inset-0 bg-gradient-to-t from-background/50 to-transparent" />
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
