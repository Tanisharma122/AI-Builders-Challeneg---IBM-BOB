import type { ReactNode } from 'react'
import Link from 'next/link'
import type { LucideIcon } from 'lucide-react'

interface FeatureSectionProps {
  eyebrow: string
  eyebrowIcon: LucideIcon
  headline: string
  subtext: string
  ctaLabel: string
  ctaHref?: string
  visual: ReactNode
  reversed?: boolean
}

export function FeatureSection({
  eyebrow,
  eyebrowIcon: EyebrowIcon,
  headline,
  subtext,
  ctaLabel,
  ctaHref = '/#suite',
  visual,
  reversed = false,
}: FeatureSectionProps) {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden="true"
        className={`pointer-events-none absolute top-10 h-80 w-80 rounded-full bg-brand/15 blur-[120px] ${
          reversed ? 'left-0' : 'right-0'
        }`}
      />
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-24">
        <div className={`flex flex-col gap-6 ${reversed ? 'lg:order-2' : 'lg:order-1'}`}>
          <span className="inline-flex w-fit items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-brand">
            <EyebrowIcon className="size-4" aria-hidden="true" />
            {eyebrow}
          </span>
          <h1 className="text-balance text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl lg:text-[2.75rem]">
            {headline}
          </h1>
          <p className="max-w-lg text-pretty text-lg leading-relaxed text-muted-foreground">{subtext}</p>
          <Link
            href={ctaHref}
            className="inline-flex w-fit items-center justify-center rounded-lg border border-border bg-transparent px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
          >
            {ctaLabel}
          </Link>
        </div>
        <div className={reversed ? 'lg:order-1' : 'lg:order-2'}>{visual}</div>
      </div>
    </section>
  )
}
