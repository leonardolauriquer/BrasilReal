import type { Metadata, Viewport } from "next";
import { Figtree, Fraunces } from "next/font/google";
import { SITE_DESCRIPTION, SITE_URL } from "@/lib/brand";
import "./globals.css";

const sans = Figtree({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
});

const display = Fraunces({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "Brasil Real",
  description: SITE_DESCRIPTION,
  applicationName: "Brasil Real",
  keywords: [
    "Brasil",
    "atlas",
    "IBGE",
    "dados oficiais",
    "mapa",
    "UF",
    "indicadores",
  ],
  openGraph: {
    type: "website",
    locale: "pt_BR",
    url: SITE_URL,
    siteName: "Brasil Real",
    title: "Brasil Real",
    description: SITE_DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: "Brasil Real",
    description: SITE_DESCRIPTION,
  },
  appleWebApp: {
    capable: true,
    title: "Brasil Real",
    statusBarStyle: "black-translucent",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#5a766f",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={`${sans.variable} ${display.variable}`}>{children}</body>
    </html>
  );
}
