import type { Metadata } from 'next'
import VideoClippingClient from './VideoClippingClient'

export const metadata: Metadata = {
  title: 'AI Video Clipping & Distribution — CreaTect AI',
  description:
    'Identify high-engagement segments to create viral shorts and reels. Analyze long-form video, generate metadata, and distribute everywhere in one click.',
}

export default function VideoClippingPage() {
  return <VideoClippingClient />
}
