import type { Metadata, Viewport } from "next";
import { Figtree, Fraunces } from "next/font/google";
import { SITE_DESCRIPTION, SITE_URL } from "@/lib/brand";
import { I18nProvider } from "@/lib/i18n/I18nProvider";
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
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: "Brasil Real — atlas exploratório com dados oficiais",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Brasil Real",
    description: SITE_DESCRIPTION,
    images: ["/og.png"],
  },
  appleWebApp: {
    capable: true,
    title: "Brasil Real",
    statusBarStyle: "black-translucent",
  },
  formatDetection: { telephone: false },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(display-mode: standalone)", color: "#14201c" },
    { media: "(prefers-color-scheme: dark)", color: "#14201c" },
    { color: "#5a766f" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={`${sans.variable} ${display.variable}`}>
        <I18nProvider>{children}</I18nProvider>
      </body>
    </html>
  );
}
