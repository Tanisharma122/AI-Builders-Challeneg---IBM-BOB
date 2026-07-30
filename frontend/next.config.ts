import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        // Proxy all /api/* requests to the FastAPI backend during development.
        // In production, configure nginx/reverse-proxy instead.
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/:path*`,
      },
      {
        // Proxy /outputs/* for serving processed clip files.
        source: "/outputs/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/outputs/:path*`,
      },
    ];
  },
};

export default nextConfig;
