import Link from 'next/link'
import { Logo } from '@/components/site-nav'

const columns = [
  {
    title: 'Products',
    links: [
      { label: 'Video Clipping', href: '/features/video-clipping' },
      { label: 'Text-to-Image', href: '/features/text-to-image' },
      { label: 'Thumbnail Gen', href: '/features/thumbnail-generator' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '/#suite' },
      { label: 'Blog', href: '/#suite' },
      { label: 'Contact', href: '/#suite' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Docs', href: '/#suite' },
      { label: 'Community', href: '/#suite' },
      { label: 'Support', href: '/#suite' },
    ],
  },
]

export function SiteFooter() {
  return (
    <footer className="border-t border-border/60 bg-background">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-14 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
        <div className="space-y-4">
          <Logo />
          <p className="max-w-xs text-sm leading-relaxed text-muted-foreground">
            Agentic content orchestration for next-gen creators. Ideate, produce, and distribute in one flow.
          </p>
        </div>
        {columns.map((col) => (
          <div key={col.title}>
            <h3 className="mb-4 text-sm font-semibold text-foreground">{col.title}</h3>
            <ul className="space-y-3">
              {col.links.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-border/60">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 px-6 py-6 text-sm text-muted-foreground sm:flex-row">
          <p>Â© {new Date().getFullYear()} TANI. All rights reserved.</p>
          <p>Made with IBM Bob</p>
        </div>
      </div>
    </footer>
  )
}

