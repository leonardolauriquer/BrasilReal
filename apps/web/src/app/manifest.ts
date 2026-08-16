import type { MetadataRoute } from "next";
import { SITE_DESCRIPTION, SITE_URL } from "@/lib/brand";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Brasil Real",
    short_name: "Brasil Real",
    description: SITE_DESCRIPTION,
    id: `${SITE_URL}/`,
    start_url: "/",
    scope: "/",
    display: "standalone",
    display_override: ["standalone", "minimal-ui"],
    background_color: "#5a766f",
    theme_color: "#14201c",
    lang: "pt-BR",
    dir: "ltr",
    orientation: "any",
    categories: ["education", "reference", "navigation"],
    launch_handler: { client_mode: "focus-existing" },
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      {
        src: "/icons/maskable-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/icons/maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
      { src: "/apple-icon.png", sizes: "180x180", type: "image/png" },
    ],
  } as MetadataRoute.Manifest;
}
