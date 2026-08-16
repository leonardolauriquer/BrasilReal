/** @type {import('next').NextConfig} */
const path = require("path");
const apiTarget = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";
const staticExport = process.env.FIREBASE_HOSTING === "1";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "@brasil-real/contracts": path.resolve(
        __dirname,
        "../../packages/contracts/typescript/index.ts",
      ),
    };
    return config;
  },
};

if (staticExport) {
  nextConfig.output = "export";
  nextConfig.images = { unoptimized: true };
  nextConfig.trailingSlash = true;
} else {
  nextConfig.rewrites = async () => {
    if (process.env.NEXT_PUBLIC_API_URL) return [];
    return [
      { source: "/v1/:path*", destination: `${apiTarget}/v1/:path*` },
      { source: "/health", destination: `${apiTarget}/health` },
      { source: "/ready", destination: `${apiTarget}/ready` },
    ];
  };
}

module.exports = nextConfig;
