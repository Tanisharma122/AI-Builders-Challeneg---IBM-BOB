const testimonials = [
  {
    quote:
      'CreaTect cut my editing time from a full day to under an hour. The auto-clipping just knows which moments will pop.',
    name: 'Sarah L.',
    role: 'YouTube Creator',
    stat: '1.2M subscribers',
    initials: 'SL',
  },
  {
    quote:
      'The thumbnail A/B scoring is unreal. My average CTR jumped from 6% to over 11% in three weeks.',
    name: 'Marcus D.',
    role: 'Short-form Strategist',
    stat: '3.5x CTR lift',
    initials: 'MD',
  },
  {
    quote:
      'Generating B-roll straight in the timeline changed everything. No more stock footage hunting.',
    name: 'Priya N.',
    role: 'Video Producer',
    stat: '10x faster output',
    initials: 'PN',
  },
]

export function Testimonials() {
  return (
    <section id="testimonials" className="border-y border-border/60 bg-card/30">
      <div className="mx-auto max-w-7xl px-6 py-20 lg:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Creator case studies</p>
          <h2 className="mt-4 text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Loved by creators scaling across platforms.
          </h2>
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-3">
          {testimonials.map((item) => (
            <figure
              key={item.name}
              className="flex flex-col gap-6 rounded-2xl border border-border bg-background/60 p-8"
            >
              <blockquote className="text-pretty leading-relaxed text-foreground">
                {`"${item.quote}"`}
              </blockquote>
              <figcaption className="mt-auto flex items-center gap-3">
                <span className="flex size-11 items-center justify-center rounded-full bg-brand/15 text-sm font-semibold text-brand">
                  {item.initials}
                </span>
                <div>
                  <p className="font-semibold text-foreground">{item.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.role} · {item.stat}
                  </p>
                </div>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  )
}
