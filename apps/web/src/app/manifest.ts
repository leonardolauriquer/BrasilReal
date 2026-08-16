import type { MetadataRoute } from "next";
import { SITE_DESCRIPTION } from "@/lib/brand";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Brasil Real",
    short_name: "Brasil Real",
    description: SITE_DESCRIPTION,
    start_url: "/",
    display: "standalone",
    background_color: "#5a766f",
    theme_color: "#5a766f",
    lang: "pt-BR",
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml" },
      { src: "/apple-icon.png", sizes: "180x180", type: "image/png" },
    ],
  };
}
