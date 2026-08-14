/** @type {import('next').NextConfig} */
const apiTarget = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      { source: "/v1/:path*", destination: `${apiTarget}/v1/:path*` },
      { source: "/health", destination: `${apiTarget}/health` },
      { source: "/ready", destination: `${apiTarget}/ready` },
    ];
  },
};

module.exports = nextConfig;
